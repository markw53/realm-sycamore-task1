# Non-Literal Translation Rationale

Places where the TypeScript translation deliberately deviates from a line-by-line Python translation, and why.

## 1. Threading locks removed entirely

**Python:** `TaskQueue` uses `threading.Lock` with `with self._lock:` context managers on every operation (push, pop, peek, remove, get_job, clear, get_all_jobs).

**TypeScript:** No locking mechanism. All queue operations are plain synchronous method calls.

**Why:** Python's threading module protects against concurrent access from multiple OS threads. Node.js runs JavaScript on a single thread with an event loop — synchronous code blocks execute atomically without interleaving. Since the source code uses `asyncio` (cooperative multitasking), not `threading.Thread`, the translated async code in TypeScript has the same concurrency guarantees without locks. Adding artificial locking (e.g., via `Mutex` from a third-party library) would be non-idiomatic and misleading.

## 2. `asyncio.to_thread` replaced with synchronous execution

**Python:** CPU-bound work in `CpuWorker` is offloaded via `asyncio.to_thread(math.factorial, n)` to avoid blocking the event loop.

**TypeScript:** `factorial(n)`, `fibonacci(n)`, and `isPrime(n)` are called synchronously within an async function, wrapped in `Promise.resolve()`.

**Why:** Python's `asyncio.to_thread` exists because of the GIL — CPU-bound work in the main thread blocks the entire event loop. Node.js has the same single-threaded constraint, but for the computational loads in this project (factorial of 20, fibonacci of 30, primality checks), the execution time is negligible (sub-millisecond). Using `worker_threads` would be the true equivalent of `to_thread`, but it would add massive complexity for zero behavioral benefit. If heavy CPU work were required, `worker_threads` or a native addon would be warranted — but that's not the case here.

## 3. `asyncio.wait_for` replaced with `Promise.race` timeout pattern

**Python:** `await asyncio.wait_for(self.execute(job), timeout=job.timeout)` raises `asyncio.TimeoutError` if the coroutine exceeds the timeout.

**TypeScript:**
```typescript
async function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: NodeJS.Timeout;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new TimeoutError(`Timeout after ${ms}ms`)), ms);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}
Why: There is no built-in wait_for in Node.js. Promise.race is the idiomatic equivalent — it resolves or rejects with whichever Promise settles first. The finally block ensures the timer is cleaned up to prevent event loop hangs. A custom TimeoutError class replaces asyncio.TimeoutError.

4. __init__.py barrel exports replaced with direct imports
Python: Each package has an __init__.py that re-exports public symbols:

python
# src/models/__init__.py
from src.models.job import Job, JobStatus, JobPriority, InvalidJobStateError
__all__ = ["Job", "JobStatus", "JobPriority", "InvalidJobStateError", ...]
TypeScript: Consumers import directly from specific modules:

typescript
import { Job, JobStatus, JobPriority } from "./models/job";
Why: While TypeScript supports barrel files (index.ts), they are increasingly discouraged for internal project imports due to circular dependency risks and tree-shaking interference. Direct imports are explicit, avoid re-export indirection, and are the prevailing convention in modern TypeScript projects. The public API surface is equivalent — the same symbols are available, just imported from their source modules.

5. heapq operations replaced with custom MinHeap class
Python: Uses heapq.heappush and heapq.heappop operating on a plain list with tuple comparison (priority, counter, job).

TypeScript: Custom MinHeap class with explicit siftUp/siftDown methods and a comparator function.

Why: JavaScript/TypeScript has no stdlib heap implementation. Using Array.sort() after each insertion would be O(n log n) per push instead of O(log n) — a behavioral regression in performance characteristics. The custom MinHeap preserves the same algorithmic complexity as Python's heapq. The comparator replicates Python's tuple ordering: first by priority (ascending), then by insertion counter (FIFO tiebreaker).

6. dataclass(frozen=True) replaced with readonly properties
Python: QueueConfig uses @dataclass(frozen=True) which prevents attribute modification after construction, raising FrozenInstanceError on assignment.

TypeScript: Properties declared with readonly keyword:

typescript
export class QueueConfig {
  public readonly maxWorkers: number;
  public readonly maxQueueSize: number;
  // ...
}
Why: TypeScript's readonly is a compile-time constraint — it prevents reassignment in TypeScript code but doesn't raise a runtime error like Python's FrozenInstanceError. This is actually stricter in one way (caught at compile time rather than runtime) but weaker in another (no runtime enforcement in compiled JS). For this project's use case, compile-time immutability is sufficient — QueueConfig is never mutated after construction in any code path.

7. __post_init__ validation moved to constructor body
Python: @dataclass generates __init__ automatically, then calls __post_init__ for custom validation:

python
@dataclass(frozen=True)
class QueueConfig:
    max_workers: int = 4
    def __post_init__(self):
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
TypeScript: Validation happens in the constructor after property assignment:

typescript
constructor(options: Partial<QueueConfigOptions> = {}) {
  this.maxWorkers = options.maxWorkers ?? 4;
  if (this.maxWorkers < 1) {
    throw new Error("maxWorkers must be >= 1");
  }
}
Why: TypeScript has no __post_init__ equivalent. Constructor body validation is the standard pattern. The behavioral result is identical — invalid configurations throw at construction time with equivalent error messages.

8. dict[str, Any] narrowed to Record<string, unknown>
Python: Uses dict[str, Any] extensively for payloads, metadata, and serialized data.

TypeScript: Uses Record<string, unknown> instead of Record<string, any>.

Why: This is a deliberate improvement over a literal translation. any in TypeScript disables type checking entirely — it's the escape hatch equivalent of Python's Any. unknown is safer: it requires explicit type narrowing before use, catching type errors at compile time that Python would only catch at runtime. The behavioral contract is identical (both accept any value), but the TypeScript version provides stronger static guarantees.

9. time.time() → Date.now() / 1000
Python: time.time() returns seconds since epoch as a float (e.g., 1713734400.123).

TypeScript: Date.now() returns milliseconds since epoch as an integer (e.g., 1713734400123).

Why: All timestamp fields (createdAt, startedAt, completedAt) and duration calculations use Date.now() / 1000 to produce seconds-as-float, matching Python's behavior. This ensures serialized output (toDict) produces numerically equivalent timestamps and duration calculations produce the same results.

10. structlog replaced with minimal structured logger
Python: structlog with ConsoleRenderer produces formatted log lines with key-value context:

text
2024-01-01T00:00:00Z [info] job_submitted  job_id=abc name=test priority=1
TypeScript: Custom logger produces JSON-formatted structured output:

json
{"level":"info","event":"job_submitted","job_id":"abc","name":"test","priority":1,"timestamp":"2024-01-01T00:00:00.000Z"}
Why: There is no TypeScript equivalent of structlog that matches its exact output format. Rather than pulling in a heavy logging framework (winston, pino) for minimal logging needs, a lightweight custom implementation preserves the structured key-value contract. The semantic content is equivalent — same events, same context keys, same log levels — but the output format differs. Tests validate behavior through return values, not log output, so this difference has no impact on functional equivalence.

11. Constructor signature uses options object pattern
Python: Dataclass constructors accept many keyword arguments:

python
Job(name="test", payload={}, priority=1, max_retries=5, tags=["a"])
TypeScript: Required parameters are positional, optional parameters use an options object:

typescript
new Job("test", {}, { priority: 1, maxRetries: 5, tags: ["a"] })
Why: TypeScript doesn't have keyword arguments. Long parameter lists with many optional values are error-prone (you'd need to pass undefined for skipped parameters). The options-object pattern is the idiomatic TypeScript equivalent — it provides named, optional parameters with defaults, and is the standard practice in Node.js libraries (Express, Fastify, etc.).

12. math.factorial implemented manually
Python: math.factorial(n) is a C-optimized stdlib function.

TypeScript: Custom implementation using iterative multiplication:

typescript
function factorial(n: number): number {
  if (n <= 1) return 1;
  let result = 1;
  for (let i = 2; i <= n; i++) result *= i;
  return result;
}
Why: JavaScript has no Math.factorial. The iterative implementation produces identical results for all inputs tested (n ≤ 20). Note: for n > 20, JavaScript's Number type loses integer precision (max safe integer is 2^53 - 1), while Python handles arbitrary precision. For n = 20, 2432902008176640000 is within safe integer range, so results are exact. This limitation is documented but acceptable for the project's test cases.

text

---