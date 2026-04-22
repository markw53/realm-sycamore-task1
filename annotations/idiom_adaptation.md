# Idiom Adaptation

## Python → TypeScript idiom changes

### 1. Error handling: exception classes → custom Error subclasses

Python uses exception classes with inheritance. TypeScript uses custom Error subclasses with the same pattern but different syntax.

**Python:**
```python
class InvalidJobStateError(Exception):
    """Raised when a job state transition is invalid."""
    pass

raise InvalidJobStateError(f"Cannot start job in state {self.status.value}")
TypeScript:

typescript
export class InvalidJobStateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidJobStateError";
    Object.setPrototypeOf(this, InvalidJobStateError.prototype);
  }
}

throw new InvalidJobStateError(`Cannot start job in state ${this.status}`);
Unlike Python → Go (where exceptions become error returns), Python → TypeScript preserves the throw/catch paradigm. The key adaptation is Object.setPrototypeOf to ensure instanceof works correctly with TypeScript's compiled output.

2. Dataclasses → TypeScript classes with constructor parameters
Python's @dataclass with field(default_factory=...) becomes TypeScript classes with constructor defaults and explicit property declarations.

Python:

python
@dataclass
class Job:
    name: str
    payload: dict[str, Any]
    priority: int = JobPriority.MEDIUM.value
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    tags: list[str] = field(default_factory=list)
TypeScript:

typescript
export class Job {
  public name: string;
  public payload: Record<string, unknown>;
  public priority: number;
  public id: string;
  public status: JobStatus;
  public tags: string[];

  constructor(
    name: string,
    payload: Record<string, unknown>,
    options: Partial<JobOptions> = {}
  ) {
    this.name = name;
    this.payload = payload;
    this.priority = options.priority ?? JobPriority.MEDIUM;
    this.id = options.id ?? crypto.randomUUID();
    this.status = options.status ?? JobStatus.PENDING;
    this.tags = options.tags ?? [];
  }
}
Python's positional + keyword arguments with defaults map to a required-params + options-object pattern in TypeScript, which is more idiomatic than long parameter lists.

3. Optional types: Optional[T] → T | null
Python's Optional[float] pattern maps to TypeScript union types.

Python:

python
started_at: Optional[float] = None
completed_at: Optional[float] = None

@property
def duration(self) -> Optional[float]:
    if self.started_at is None:
        return None
TypeScript:

typescript
public startedAt: number | null = null;
public completedAt: number | null = null;

get duration(): number | null {
  if (this.startedAt === null) return null;
null is used rather than undefined to match Python's None semantics — an explicit "no value" rather than "not yet assigned."

4. Python @property → TypeScript getters
Python's @property decorator maps directly to TypeScript's get accessor syntax.

Python:

python
@property
def is_terminal(self) -> bool:
    return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

@property
def duration(self) -> Optional[float]:
    ...
TypeScript:

typescript
get isTerminal(): boolean {
  return [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    .includes(this.status);
}

get duration(): number | null {
  ...
}
5. Python enums → TypeScript string/numeric enums
Python's Enum with string/numeric values maps to TypeScript enums preserving the same values.

Python:

python
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 5
    LOW = 8
    BACKGROUND = 10
TypeScript:

typescript
export enum JobStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  RETRYING = "retrying",
}

export enum JobPriority {
  CRITICAL = 0,
  HIGH = 1,
  MEDIUM = 5,
  LOW = 8,
  BACKGROUND = 10,
}
This is a nearly 1:1 mapping. The string enum preserves serialization compatibility (.value in Python → direct enum value in TypeScript).

6. Abstract base classes → TypeScript abstract classes
Python's ABC with @abstractmethod maps directly to TypeScript's abstract keyword.

Python:

python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    async def load(self, key: str) -> Optional[dict[str, Any]]: ...
TypeScript:

typescript
export abstract class StorageBackend {
  abstract save(key: string, data: Record<string, unknown>): Promise<void>;
  abstract load(key: string): Promise<Record<string, unknown> | null>;
}
The async keyword in Python becomes Promise<T> return types in TypeScript — both enforce that implementations must be awaitable.

7. asyncio patterns → native async/await
Python's asyncio-specific patterns adapt to TypeScript's Promise-based async model.

Python:

python
result = await asyncio.wait_for(
    self.execute(job), timeout=job.timeout or self.timeout
)
await asyncio.sleep(0.01)
result = await asyncio.to_thread(math.factorial, n)
TypeScript:

typescript
result = await withTimeout(
  this.execute(job), (job.timeout || this.timeout) * 1000
);
await new Promise(resolve => setTimeout(resolve, 10));
result = await Promise.resolve(factorial(n));
Key adaptations:

asyncio.wait_for → custom withTimeout using Promise.race with a reject timer
asyncio.sleep(seconds) → setTimeout wrapped in a Promise (milliseconds)
asyncio.to_thread → Promise.resolve (Node.js is single-threaded; there's no GIL to escape)
8. threading.Lock → removed (single-threaded runtime)
Python's TaskQueue uses threading.Lock for thread safety. This is entirely removed in TypeScript.

Python:

python
def push(self, job: Job) -> None:
    with self._lock:
        if len(self._heap) >= self._max_size:
            raise QueueFullError(...)
        heapq.heappush(self._heap, entry)
TypeScript:

typescript
push(job: Job): void {
  if (this.heap.length >= this.maxSize) {
    throw new QueueFullError(...);
  }
  this.heap.push(entry);
  this.siftUp(this.heap.length - 1);
}
Node.js's event loop guarantees that synchronous code blocks execute atomically — no interleaving is possible within a single function call. The lock removal is safe because the source code's concurrency model (asyncio) maps to single-threaded cooperative multitasking in Node.js.

9. heapq → custom MinHeap class
Python's heapq module operates on plain lists. TypeScript has no stdlib heap, requiring a custom implementation.

Python:

python
import heapq

entry = (job.priority, self._counter, job)
heapq.heappush(self._heap, entry)
priority, counter, job = heapq.heappop(self._heap)
TypeScript:

typescript
// Custom MinHeap with sift-up/sift-down operations
private siftUp(i: number): void {
  while (i > 0) {
    const parent = Math.floor((i - 1) / 2);
    if (this.compare(this.heap[i], this.heap[parent]) < 0) {
      [this.heap[i], this.heap[parent]] = [this.heap[parent], this.heap[i]];
      i = parent;
    } else break;
  }
}
The comparison function replicates Python's tuple comparison: first by priority (numeric), then by insertion counter (FIFO tiebreaker).

10. __post_init__ validation → constructor validation
Python's @dataclass with __post_init__ for validation becomes constructor body validation in TypeScript.

Python:

python
@dataclass(frozen=True)
class QueueConfig:
    max_workers: int = 4
    def __post_init__(self):
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
TypeScript:

typescript
export class QueueConfig {
  public readonly maxWorkers: number;

  constructor(options: Partial<QueueConfigOptions> = {}) {
    this.maxWorkers = options.maxWorkers ?? 4;
    if (this.maxWorkers < 1) {
      throw new Error("maxWorkers must be >= 1");
    }
  }
}
The frozen=True constraint maps to readonly properties, preventing mutation after construction.

11. Naming conventions: snake_case → camelCase
All identifiers adapt to TypeScript conventions.

Python	TypeScript
max_workers	maxWorkers
job_id	jobId
retry_count	retryCount
is_terminal	isTerminal
to_dict	toDict
from_dict	fromDict
get_all_jobs	getAllJobs
run_all	runAll
process_next	processNext
Class names remain PascalCase in both languages. Enum members remain UPPER_SNAKE_CASE in both.

12. __init__.py barrel exports → ES module exports
Python's __init__.py files that re-export from submodules are replaced by direct ES module imports.

Python:

python
# src/models/__init__.py
from src.models.job import Job, JobStatus, JobPriority, InvalidJobStateError
from src.models.queue import TaskQueue, QueueFullError, DuplicateJobError
from src.models.result import JobResult

__all__ = [
    "Job", "JobStatus", "JobPriority", "InvalidJobStateError",
    "TaskQueue", "QueueFullError", "DuplicateJobError",
    "JobResult",
]
TypeScript:

typescript
// Consumers import directly from the specific module
import { Job, JobStatus, JobPriority, InvalidJobStateError } from "./models/job";
import { TaskQueue, QueueFullError, DuplicateJobError } from "./models/queue";
import { JobResult } from "./models/result";
Barrel index.ts files could be used but are not idiomatic for internal project imports in TypeScript. Direct imports are preferred for tree-shaking and clarity.

13. dict[str, Any] → Record<string, unknown>
Python's loosely-typed dictionaries map to TypeScript's Record type with unknown instead of any for type safety.

Python:

python
payload: dict[str, Any]
metadata: dict[str, Any] = field(default_factory=dict)
TypeScript:

typescript
payload: Record<string, unknown>;
metadata: Record<string, unknown> = {};
unknown is preferred over any because it forces type narrowing before use — making the TypeScript version actually safer than the Python original.

14. @staticmethod → static
Direct 1:1 mapping with slightly different syntax.

Python:

python
@staticmethod
def _fibonacci(n: int) -> int:
    ...

@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Job":
    ...
TypeScript:

typescript
private static fibonacci(n: number): number {
  ...
}

static fromDict(data: Record<string, unknown>): Job {
  ...
}
@classmethod with cls parameter becomes a regular static method — TypeScript doesn't need an explicit class reference since static methods are called on the class directly.

text

---