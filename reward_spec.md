# Reward Specification

## Terminal reward

- `1.0`: `npx tsc` succeeds and all 84 target tests pass.
- `0.0`: build fails or any test fails.

## Interim reward guidance

- +0.10: correct `package.json` with valid dependencies and `tsconfig.json` with ES2022 strict mode configuration
- +0.10: idiomatic TypeScript project layout (src/ with modular subdirectories, proper ES module imports/exports)
- +0.10: Job model correctly implements state machine transitions (PENDING → RUNNING → COMPLETED/FAILED/RETRYING) with equivalent behavior to Python including all edge case rejections
- +0.10: custom Error subclasses defined for InvalidJobStateError, QueueFullError, DuplicateJobError with correct inheritance and error messages
- +0.10: TaskQueue implemented with proper min-heap priority queue (not Array.sort), push/pop/peek/remove/clear all match Python behavior
- +0.10: CpuWorker correctly implements factorial, fibonacci, prime_check with identical outputs and input validation matching Python
- +0.10: IoWorker correctly implements echo (with async delay), transform (uppercase/lowercase/identity/keys_only), and aggregate (with numeric filtering) matching Python behavior
- +0.10: Scheduler orchestrates job submission, worker dispatch, retry logic, and result collection with equivalent behavior to Python
- +0.05: scheduling strategies (priority and round-robin) with shouldPreempt logic matching Python
- +0.05: serialization utilities produce JSON roundtrips preserving all Job and JobResult fields
- +0.05: validation utilities match exact Python rules for payload keys, priority range, job name format, and tag sanitization
- +0.05: MemoryStorage implements save/load/delete/exists/listKeys with copy semantics matching Python