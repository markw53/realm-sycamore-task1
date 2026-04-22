# Translation Strategy

## Overall approach

The translation follows a module-by-module strategy, starting with leaf dependencies (config, models, errors) and working up to the modules that depend on them (workers, scheduler, storage, utils). Unlike Go, TypeScript resolves imports at compile time and handles circular references through its module system, but the bottom-up approach ensures each module can be tested independently as it's translated.

The translation preserves the Python source's package structure almost directly — TypeScript's module system is flexible enough that a 1:1 directory mapping is both possible and idiomatic. The key structural changes are naming convention shifts (snake_case → camelCase) and the removal of `__init__.py` barrel files in favor of direct imports.

## Package mapping

|
 Python module 
|
 TypeScript module 
|
 Rationale 
|
|
---
|
---
|
---
|
|
`src/__init__.py`
|
 (no equivalent — direct imports used) 
|
 TypeScript consumers import from specific modules. Barrel 
`index.ts`
 files are possible but discouraged for internal imports. 
|
|
`src/config.py`
|
`src/config.ts`
|
 Direct 1:1 mapping. 
`@dataclass(frozen=True)`
 → class with 
`readonly`
 properties and constructor validation. 
|
|
`src/models/__init__.py`
|
 (no equivalent) 
|
 Re-exports eliminated. Consumers import directly from 
`models/job`
, 
`models/queue`
, 
`models/result`
. 
|
|
`src/models/job.py`
|
`src/models/job.ts`
|
 Job class, JobStatus/JobPriority enums, InvalidJobStateError. Core state machine logic preserved exactly. 
|
|
`src/models/queue.py`
|
`src/models/queue.ts`
|
 TaskQueue with custom MinHeap replacing 
`heapq`
. Threading locks removed. QueueFullError, DuplicateJobError. 
|
|
`src/models/result.py`
|
`src/models/result.ts`
|
 JobResult with 
`ok`
/
`err`
 factory methods. Direct mapping. 
|
|
`src/workers/__init__.py`
|
 (no equivalent) 
|
 Re-exports eliminated. 
|
|
`src/workers/base.py`
|
`src/workers/base.ts`
|
 Abstract BaseWorker class. 
`asyncio.wait_for`
 → 
`Promise.race`
 timeout pattern. 
|
|
`src/workers/cpu_worker.py`
|
`src/workers/cpu_worker.ts`
|
 CpuWorker with factorial, fibonacci, prime_check. 
`asyncio.to_thread`
 → synchronous execution. 
`math.factorial`
 → custom implementation. 
|
|
`src/workers/io_worker.py`
|
`src/workers/io_worker.ts`
|
 IoWorker with echo, transform, aggregate. 
`asyncio.sleep`
 → 
`setTimeout`
 Promise. 
|
|
`src/scheduler/__init__.py`
|
 (no equivalent) 
|
 Re-exports eliminated. 
|
|
`src/scheduler/priority.py`
|
`src/scheduler/priority.ts`
|
 PriorityScheduler. Direct 1:1 mapping. 
|
|
`src/scheduler/round_robin.py`
|
`src/scheduler/round_robin.ts`
|
 RoundRobinScheduler. Direct 1:1 mapping. 
|
|
`src/scheduler/scheduler.py`
|
`src/scheduler/scheduler.ts`
|
 Main Scheduler orchestrator. Worker creation, job dispatch, retry logic. 
`asyncio.sleep`
 → 
`setTimeout`
 Promise. 
|
|
`src/storage/__init__.py`
|
 (no equivalent) 
|
 Re-exports eliminated. 
|
|
`src/storage/backend.py`
|
`src/storage/backend.ts`
|
 Abstract StorageBackend. 
`ABC`
 + 
`@abstractmethod`
 → 
`abstract class`
. 
|
|
`src/storage/memory.py`
|
`src/storage/memory.ts`
|
 MemoryStorage. Copy semantics preserved with spread operator / 
`structuredClone`
. 
|
|
`src/storage/file_store.py`
|
`src/storage/file_store.ts`
|
 FileStorage. 
`aiofiles`
 → 
`fs/promises`
. 
`os.makedirs`
 → 
`fs.mkdirSync`
 with 
`recursive`
. 
|
|
`src/utils/__init__.py`
|
 (no equivalent) 
|
 Re-exports eliminated. 
|
|
`src/utils/logging.py`
|
`src/utils/logging.ts`
|
`structlog`
 → custom structured logger using 
`console.log`
 with JSON context. 
|
|
`src/utils/serialization.py`
|
`src/utils/serialization.ts`
|
 JSON serialization. 
`json.dumps`
/
`json.loads`
 → 
`JSON.stringify`
/
`JSON.parse`
. 
|
|
`src/utils/validation.py`
|
`src/utils/validation.ts`
|
 Input validation. Direct 1:1 logic mapping with camelCase naming. 
|
|
`src/main.py`
|
`src/main.ts`
|
 Entry point. 
`asyncio.run(main())`
 → top-level await or 
`main().catch()`
. 
|

## Build order

Translation order follows the dependency graph bottom-up:

1. **`src/config.ts`** — no internal dependencies. Standalone configuration with validation.
2. **`src/models/job.ts`** — depends on nothing. Enums, Job class, InvalidJobStateError.
3. **`src/models/result.ts`** — depends on nothing. JobResult with factory methods.
4. **`src/models/queue.ts`** — depends on `models/job`. Custom MinHeap, QueueFullError, DuplicateJobError.
5. **`src/utils/validation.ts`** — depends on nothing. Pure utility functions.
6. **`src/utils/serialization.ts`** — depends on `models/job`, `models/result`. JSON roundtrip utilities.
7. **`src/utils/logging.ts`** — depends on nothing. Structured logger setup.
8. **`src/storage/backend.ts`** — depends on nothing. Abstract storage interface.
9. **`src/storage/memory.ts`** — depends on `storage/backend`. In-memory implementation.
10. **`src/storage/file_store.ts`** — depends on `storage/backend`. File-based implementation using `fs/promises`.
11. **`src/workers/base.ts`** — depends on `models/job`, `models/result`, `utils/logging`. Abstract worker with timeout handling.
12. **`src/workers/cpu_worker.ts`** — depends on `workers/base`, `models/job`. Factorial, fibonacci, prime_check.
13. **`src/workers/io_worker.ts`** — depends on `workers/base`, `models/job`. Echo, transform, aggregate.
14. **`src/scheduler/priority.ts`** — depends on `models/job`, `models/queue`. Priority scheduling strategy.
15. **`src/scheduler/round_robin.ts`** — depends on `models/job`, `models/queue`. Round-robin scheduling strategy.
16. **`src/scheduler/scheduler.ts`** — depends on everything above. Main orchestrator.
17. **`src/main.ts`** — depends on `config`, `models/job`, `scheduler/scheduler`, `utils/logging`. Entry point.

## Key architectural decisions

### 1. Preserve directory structure
The Python `src/` layout maps almost 1:1 to TypeScript's `src/`. Unlike a Python → Go translation (which requires restructuring into `internal/` packages with one-package-per-directory), TypeScript's module system is flexible enough to preserve the original structure. This minimizes unnecessary structural divergence.

### 2. CommonJS output for subprocess testability
`tsconfig.json` targets `commonjs` module output so that compiled `.js` files in `dist/` can be loaded via `require()` in subprocess-based behavioral tests (`node -e "const { Job } = require('./dist/models/job')"`). ES modules would require `--experimental-vm-modules` flags or dynamic `import()`, adding complexity to the test harness.

### 3. No barrel files
Python's `__init__.py` re-exports are not translated to TypeScript `index.ts` barrel files. Each module exports its own symbols, and consumers import directly. This avoids:
- Circular dependency issues common with barrel files
- Unnecessary indirection
- Tree-shaking interference (relevant for bundled environments)

### 4. Options object pattern for constructors
Python's keyword arguments with defaults (`Job(name="x", priority=1, max_retries=5)`) are translated to a positional-required + options-object pattern (`new Job("x", {}, { priority: 1, maxRetries: 5 })`). This is the standard TypeScript idiom for functions with many optional parameters.

### 5. Custom MinHeap over Array.sort
Despite `Array.sort()` being simpler to implement, a proper MinHeap is used to match the O(log n) push/pop complexity of Python's `heapq`. Using `Array.sort()` would change the algorithmic complexity to O(n log n) per insertion — a behavioral regression even if outputs appear correct for small inputs.

### 6. Timestamp normalization
All timestamps use `Date.now() / 1000` to produce seconds-as-float, matching Python's `time.time()`. This ensures `toDict()` output and duration calculations are numerically equivalent across languages.

## Files produced

|
 File 
|
 Purpose 
|
|
---
|
---
|
|
`package.json`
|
 Dependencies (typescript, @types/node as devDeps), build script 
|
|
`tsconfig.json`
|
 Compiler config: ES2022, commonjs, strict, outDir: ./dist 
|
|
`src/config.ts`
|
 QueueConfig class with readonly properties and constructor validation 
|
|
`src/main.ts`
|
 Entry point with async main function 
|
|
`src/models/job.ts`
|
 Job, JobStatus, JobPriority, InvalidJobStateError 
|
|
`src/models/queue.ts`
|
 TaskQueue (MinHeap-based), QueueFullError, DuplicateJobError 
|
|
`src/models/result.ts`
|
 JobResult with ok/err factories 
|
|
`src/workers/base.ts`
|
 Abstract BaseWorker with timeout handling 
|
|
`src/workers/cpu_worker.ts`
|
 CpuWorker: factorial, fibonacci, prime_check 
|
|
`src/workers/io_worker.ts`
|
 IoWorker: echo, transform, aggregate 
|
|
`src/scheduler/priority.ts`
|
 PriorityScheduler strategy 
|
|
`src/scheduler/round_robin.ts`
|
 RoundRobinScheduler strategy 
|
|
`src/scheduler/scheduler.ts`
|
 Main Scheduler orchestrator 
|
|
`src/storage/backend.ts`
|
 Abstract StorageBackend 
|
|
`src/storage/memory.ts`
|
 MemoryStorage implementation 
|
|
`src/storage/file_store.ts`
|
 FileStorage implementation 
|
|
`src/utils/logging.ts`
|
 Structured logging configuration 
|
|
`src/utils/serialization.ts`
|
 JSON serialize/deserialize utilities 
|
|
`src/utils/validation.ts`
|
 Input validation utilities 
|
|
**
Total: 19 files
**
|
 (17 .ts source + package.json + tsconfig.json) 
|