# Realm Sycamore Task — Python to TypeScript Task Queue

This directory is a Python-to-TypeScript repository-level code translation task in the Sycamore benchmark format. It follows the **authoritative reference** layout from the sample task.

## How the pieces wire up (must-read for authors)

A sycamore task is uploaded to the platform as **four seed files**:

| File | Required | What it is |
|---|---|---|
| `task_config.json` | yes | Declarative spec: pipeline, image, build/test commands, FAIL_TO_PASS list. Does **not** contain the tests inline. |
| `prompt.txt` | yes | Agent-visible instructions (source language, target language, what to translate, what not to). |
| `test_patch.diff` | yes | Hidden Jest test suite as a unified diff. Imported into the criterion at task-create time; `git apply`'d into `/target` by the verifier **after** `submit_answer`. Agent never sees it. |
| `golden_repo.tar.gz` | optional | Reference translation as a tarball. If present, enables `model="golden_repo_validation"` runs that extract the tarball into `/target` and run the same test harness — proves the pipeline is correct independent of any agent. |

`submission.zip` at the repo root is just these four files flat-zipped; it's the bundle you upload.

The rest of this directory (`source_repo/`, `golden_repo/`, `docker/`, `behavioral_tests/`, `annotations/`, etc.) is authoring scratch: inputs to the Docker image build and reviewer context. It is NOT uploaded to the platform.

## Last verified on staging

- Task ID: `<your-task-id>`
- Image: `micro1ai/sycamore-taskqueue:<your-tag>`
- Gold run: **1.0** — pipeline is end-to-end correct.
- Agent runs: pending

## Task overview

It packages one complete episode with:

- a source Python repository (task-queue — async task queue with pluggable scheduling)
- a task prompt specifying TypeScript as the target language and behavioral equivalence expectations
- **hidden behavioral tests** (84 Jest tests exercising the translated TypeScript modules directly) — delivered as `test_patch.diff` (a unified diff) that the sycamore verifier `git apply`s into `/target/tests/` *after* the agent calls `submit_answer`. The agent never sees the tests.
- a golden response: fully translated TypeScript repository with all tests passing
- annotations covering translation strategy, dependency mapping, idiom adaptation, and non-literal translation rationale
- rubric, reward spec, verifier, and review artifacts

## Task summary

Translate an 18-file Python async task queue system into idiomatic TypeScript, including:

- source code (job model, priority queue, workers, scheduler, storage backends, serialization, validation, config)
- build configuration (`pyproject.toml` + `requirements.txt` → `package.json` + `tsconfig.json`)
- dependency mapping (`structlog` → idiomatic TS logging, `aiofiles` → native `fs/promises`)
- module system mapping (`__init__.py` barrel exports → ES module imports/exports)

### Translation challenge categories

| Category | Manifestation in this task |
|---|---|
| Build system & dependency management | `pyproject.toml` + `requirements.txt` → `package.json` + `tsconfig.json`, `structlog` → native logging, `aiofiles` → `fs/promises` |
| Module system & project structure | `__init__.py` barrel re-exports → ES module exports, `src/` package layout → `src/` with TypeScript modules |
| Type system bridging | Dataclasses → TS classes, `dict[str, Any]` → `Record<string, unknown>` or typed interfaces, `Optional` → `T \| null`, Python enums → TS enums |
| Concurrency model adaptation | `asyncio` + `asyncio.to_thread` → native async/await + Promises, `asyncio.wait_for` → `Promise.race` timeout pattern, threading locks → adapted for single-threaded runtime |
| Error handling paradigm translation | Custom exception hierarchy (`InvalidJobStateError`, `QueueFullError`, `DuplicateJobError`) → custom Error subclasses with proper inheritance |
| Ecosystem idiom adaptation | `@property` → getters, `@staticmethod` → static methods, `@abstractmethod` → abstract classes, `__post_init__` → constructor validation, `heapq` → manual min-heap implementation, snake_case → camelCase |

### Difficulty profile

- Language pair: Python → TypeScript (dynamic-to-static-ish, async model shift)
- Difficulty band: medium
- Source files: 18 Python modules
- Target files: ~15 TypeScript modules + config files
- Source behavioral tests: 0 (zero-test environment per Sycamore spec)
- Target test count: 84 hidden Jest tests

## Behavioral prompt

The agent-visible prompt is [prompt.txt](prompt.txt). It describes:

- the source repository's functionality
- the target language (TypeScript ES2022, strict mode, Node.js 20+)
- behavioral equivalence expectations
- what to translate and what not to translate

It does not reveal the specific TypeScript module layout, naming decisions, dependency choices, or implementation strategies used in the golden response.

## What you upload to Realm

Exactly the contents of [submission.zip](submission.zip) — four files, unzipped in [submission/](submission) so you can inspect them:

| File | Required | Role |
|---|---|---|
| [submission/task_config.json](submission/task_config.json) | yes | Task metadata, `build_cmd` / `test_cmd`, `FAIL_TO_PASS` list. Does **not** embed tests. |
| [submission/prompt.txt](submission/prompt.txt) | yes | Agent-visible prompt. |
| [submission/test_patch.diff](submission/test_patch.diff) | yes | Hidden Jest test suite as a unified diff. Platform base64-encodes it into the criterion at task-create time; verifier `git apply`s it into `/target` after `submit_answer`. Agent never sees it. |
| [submission/golden_repo.tar.gz](submission/golden_repo.tar.gz) | optional | Reference TypeScript translation as a tarball. Enables `model="golden_repo_validation"` runs that extract the tarball into `/target` and run the same harness — proves the pipeline is correct independent of any agent. |

`submission.zip` and `submission/` are byte-identical mirrors. There are no other copies of these files in this directory — the zip is the single source of truth.

## Supporting context (for reading, not uploading)

- [source_repo/](source_repo): Python source input to the Docker image. What the agent sees at `/source` at eval start.
- [golden_repo/](golden_repo): TypeScript reference translation. Tar this (without `.git/` or `.DS_Store`) to produce `golden_repo.tar.gz`.
- [docker/Dockerfile.combined](docker/Dockerfile.combined): authoritative sandbox image (python + node + jest). Build from this when bumping the image tag.
- [behavioral_tests/test_task_queue_behavioral.ts](behavioral_tests/test_task_queue_behavioral.ts): human-readable source for the tests embedded in `test_patch.diff`. Edit this then regenerate the diff if you need to change the test suite.
- [target_tests/](target_tests): TypeScript unit tests internal to the golden repo, kept for gold validation only (behavioral tests via Jest are the active scoring suite).
- [run_tests.sh](run_tests.sh) + [grader/](grader): local verification shim.
- [rubric.md](rubric.md), [reward_spec.md](reward_spec.md), [environment_interface.md](environment_interface.md), [annotations/](annotations), [reviews/](reviews): reviewer materials.

## Reproducing this task from scratch

1. Build (or pull) the Docker image from `docker/Dockerfile.combined`. The current task uses `micro1ai/sycamore-taskqueue:<your-tag>`.
2. POST `submission.zip` contents to the platform as seed files for a new task (or pass the zip as a single multipart upload — the platform unpacks).
3. Trigger `build-coding-task`. The importer reads `task_config.json`, base64-encodes `test_patch.diff` into the criterion's `conversion_config.test_patch`, and stashes `golden_repo.tar.gz` as `golden_repo_b64`.
4. Run `model="golden_repo_validation"` first. Expected score: `1.0`. If not, the harness is broken before you even put an agent on it.
5. Then run any agent (Opus, GPT-5.4, Gemini 3.1, etc.).

## Local verification

Run the bundled verifier against the golden translation:

```bash
./run_tests.sh

Evaluate an agent submission:

bash
./run_tests.sh --mode submission --submission /path/to/agent/output
Evaluate both golden and submission:

bash
./run_tests.sh --mode both --submission /path/to/agent/output
Direct verification
Build and test the golden translation directly:

bash
cd golden_repo
npm install
npx tsc
npx jest --forceExit --detectOpenHandles --verbose
Expected result: 84 passed, 0 failed

Verify the source Python repo:

bash
cd source_repo
pip install -r requirements.txt
python -m src.main
Expected result: runs successfully with structured log output showing 6 jobs processed.