# Sycamore Rubric

## Deterministic gates

- Gate A: The translated TypeScript repository compiles with `npx tsc` without errors and all dependencies resolve with `npm install`.
- Gate B: All 84 target-language tests pass with `npx jest --forceExit --detectOpenHandles --verbose`.
- Gate C: The agent did not modify the test suite files — equivalence is validated by the provided tests, not agent-written tests.
- Gate D: The `package.json` declares valid dependencies and `tsconfig.json` is configured for ES2022 strict mode with all required compiler options.

## Subjective review items

1. **Build system translation**: `pyproject.toml` and `requirements.txt` correctly mapped to `package.json` and `tsconfig.json` with appropriate dependencies. No unnecessary dependencies added. `structlog` → idiomatic TS logging, `aiofiles` → native `fs/promises`.
2. **Module system mapping**: Python's package structure with `__init__.py` barrel exports correctly mapped to TypeScript ES module imports/exports. Cross-package import paths resolve correctly without circular dependencies.
3. **Type system bridging**: Python dataclasses translated to TypeScript classes with proper constructor signatures, property accessors, and type annotations. Python's `Any` mapped to concrete types where inferrable, not overused as an escape hatch. `Optional` fields use `T | null` or appropriate union types.
4. **Error handling paradigm**: Python custom exceptions (`InvalidJobStateError`, `QueueFullError`, `DuplicateJobError`) translated to TypeScript custom Error subclasses with proper inheritance chains. Error messages preserve the same content and format.
5. **Concurrency model adaptation**: Python's `asyncio` with `async/await` and `asyncio.to_thread` for CPU-bound work translated to idiomatic TypeScript async/await with Promises. Timeout handling via `asyncio.wait_for` mapped to an equivalent TypeScript pattern (e.g., `Promise.race` with a timeout promise).
6. **Ecosystem idiom adaptation**: Target code follows TypeScript naming conventions (camelCase for variables/functions, PascalCase for classes/types/enums). Does not carry over Python patterns literally (e.g., `__post_init__` → constructor validation, `@property` → getter methods, `@staticmethod` → static methods, `@abstractmethod` → abstract class methods).
7. **Dependency substitution quality**: `structlog` replaced with an idiomatic structured logging approach (not a direct port of structlog's API). `aiofiles` replaced with native `fs/promises`. No unnecessary third-party dependencies where Node.js built-ins suffice.
8. **Data structure fidelity**: Python's `heapq`-based priority queue translated to a proper min-heap implementation in TypeScript — not replaced with `Array.sort()`. Thread-safe locking patterns adapted appropriately for Node.js's single-threaded event loop.
9. **Functional equivalence**: Job state machine transitions, priority queue ordering, worker dispatch, retry logic, scheduling strategies, serialization roundtrips, validation rules, and storage operations produce equivalent results for the same inputs across all edge cases.
10. **Non-literal translation quality**: Where literal translation would be non-idiomatic, the translator made appropriate adaptations while preserving behavior (e.g., Python enums → TypeScript enums with matching values, Python `dataclass` field defaults → constructor parameter defaults, Python `dict[str, Any]` → TypeScript `Record<string, unknown>` or typed interfaces, threading locks → removed or adapted for single-threaded runtime).