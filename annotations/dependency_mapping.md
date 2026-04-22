# Dependency Mapping

## Direct dependency substitutions

| Python dependency | TypeScript equivalent | Notes |
|---|---|---|
| `structlog` (PyPI) | Custom structured logger (no dependency) | Python's structlog provides structured key-value logging. Replaced with a lightweight custom logger using `console.log` with JSON-formatted context objects. No third-party logging library needed for this project's complexity. |
| `aiofiles` (PyPI) | `fs/promises` (Node.js stdlib) | Python's aiofiles provides async file I/O. Node.js has native async file operations via `fs/promises` — direct equivalent with no dependency needed. |
| `pydantic` (PyPI) | TypeScript type system + manual validation | Listed in source `pyproject.toml` but not directly imported in source code. TypeScript's strict type system and constructor validation replace Pydantic's role. No equivalent library needed. |
| `asyncio` (stdlib) | Native async/await + Promises (built-in) | Direct equivalent. Python's `asyncio.sleep` → `setTimeout` wrapped in Promise. Python's `asyncio.wait_for` → `Promise.race` with timeout. Python's `asyncio.to_thread` → `Promise.resolve` or microtask scheduling (Node.js is single-threaded, no thread offloading needed). |
| `threading` (stdlib) | Not needed | Python's threading locks (`threading.Lock`) protect shared state from concurrent access. Node.js is single-threaded with an event loop — no mutex/lock equivalent needed. Lock acquisition/release logic is removed, but the data structure semantics are preserved. |
| `heapq` (stdlib) | Custom min-heap implementation | Python's `heapq` provides heap operations on lists. No stdlib equivalent in Node.js/TypeScript. Implemented as a custom `MinHeap` class with `push`, `pop`, `peek` operations. |
| `json` (stdlib) | `JSON.stringify` / `JSON.parse` (built-in) | Direct equivalent. |
| `dataclasses` (stdlib) | TypeScript classes | No library needed; TypeScript classes with constructor parameters, property accessors, and methods are the natural equivalent of Python dataclasses. |
| `enum` (stdlib) | TypeScript `enum` or const objects | Python's `Enum` and `IntEnum` map to TypeScript string/numeric enums. Values preserved exactly. |
| `uuid` (stdlib) | `crypto.randomUUID()` (Node.js 19+) | Direct equivalent. No third-party UUID library needed. |
| `time` (stdlib) | `Date.now() / 1000` | Python's `time.time()` returns seconds as float. TypeScript's `Date.now()` returns milliseconds — divided by 1000 for equivalence. |
| `math` (stdlib) | Custom implementation or native JS `Math` | `math.factorial` has no JS equivalent — implemented as a custom function. `Math` object covers other numeric operations. |
| `os` (stdlib) | `fs` + `path` (Node.js stdlib) | `os.makedirs` → `fs.mkdirSync` with `recursive: true`. `os.path.join` → `path.join`. `os.path.exists` → `fs.existsSync`. |
| `abc` (stdlib) | TypeScript `abstract` classes | Direct equivalent. `ABC` + `@abstractmethod` → `abstract class` + `abstract method()`. |
| `typing` (stdlib) | TypeScript type system | `Any` → `unknown` or concrete types, `Optional[T]` → `T | null`, `Callable` → function types, `Literal` → string literal union types. |

## Dependencies NOT carried over

- `setuptools` / `setuptools-scm`: Build system replaced by `tsc` (TypeScript compiler) configured via `tsconfig.json`. No build tool dependency needed.
- `pytest`: Testing framework not translated — behavioral tests are provided externally via<span class="ml-2" /><span class="inline-block w-3 h-3 rounded-full bg-neutral-a12 align-middle mb-[0.1rem]" />