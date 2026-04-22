"""
HIDDEN BEHAVIORAL TEST SUITE
Python pytest tests that verify the translated TypeScript repository
by building it and exercising it via subprocess.
"""


import subprocess
import json
import os
import pytest
from pathlib import Path

TARGET_DIR = os.environ.get("TARGET_DIR", str(Path(__file__).resolve().parent.parent))

@pytest.fixture(scope="session", autouse=True)
def build_target():
    """Build the TypeScript project once before all tests."""
    # Skip build if dist/ already exists (already compiled)
    if os.path.exists(os.path.join(TARGET_DIR, "dist", "config.js")):
        return

    result = subprocess.run(
        ["npm", "install"],
        cwd=TARGET_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"npm install failed:\n{result.stderr}"

    result = subprocess.run(
        ["npx", "tsc"],
        cwd=TARGET_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"tsc failed:\n{result.stderr}"

def run_node(script: str) -> subprocess.CompletedProcess:
    """Run a Node.js script against the compiled target."""
    return subprocess.run(
        ["node", "-e", script],
        cwd=TARGET_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )

# ============================================================
# 1. QueueConfig
# ============================================================

class TestQueueConfig:
    def test_default_values(self):
        result = run_node("""
            const { QueueConfig } = require('./dist/config');
            const cfg = new QueueConfig();
            console.log(JSON.stringify({
                maxWorkers: cfg.maxWorkers,
                maxQueueSize: cfg.maxQueueSize,
                defaultPriority: cfg.defaultPriority,
                schedulingStrategy: cfg.schedulingStrategy,
                storageBackend: cfg.storageBackend,
                storagePath: cfg.storagePath,
                retryLimit: cfg.retryLimit,
                timeoutSeconds: cfg.timeoutSeconds,
                logLevel: cfg.logLevel
            }));
        """)
        assert result.returncode == 0, f"Failed:\n{result.stderr}"
        data = json.loads(result.stdout.strip())
        assert data["maxWorkers"] == 4
        assert data["maxQueueSize"] == 1000
        assert data["defaultPriority"] == 5
        assert data["schedulingStrategy"] == "priority"
        assert data["storageBackend"] == "memory"
        assert data["storagePath"] == "./task_store"
        assert data["retryLimit"] == 3
        assert data["timeoutSeconds"] == 30.0
        assert data["logLevel"] == "INFO"

    def test_rejects_max_workers_below_1(self):
        result = run_node("""
            const { QueueConfig } = require('./dist/config');
            try {
                new QueueConfig({ maxWorkers: 0 });
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1, "Should reject maxWorkers: 0"

    def test_rejects_max_queue_size_below_1(self):
        result = run_node("""
            const { QueueConfig } = require('./dist/config');
            try {
                new QueueConfig({ maxQueueSize: 0 });
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1, "Should reject maxQueueSize: 0"

    def test_rejects_default_priority_out_of_range(self):
        for val in [-1, 11]:
            result = run_node(f"""
                const {{ QueueConfig }} = require('./dist/config');
                try {{
                    new QueueConfig({{ defaultPriority: {val} }});
                    process.exit(0);
                }} catch (e) {{
                    process.exit(1);
                }}
            """)
            assert result.returncode == 1, f"Should reject defaultPriority: {val}"

    def test_rejects_retry_limit_below_0(self):
        result = run_node("""
            const { QueueConfig } = require('./dist/config');
            try {
                new QueueConfig({ retryLimit: -1 });
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1, "Should reject retryLimit: -1"

    def test_rejects_timeout_seconds_zero_or_negative(self):
        for val in [0, -5]:
            result = run_node(f"""
                const {{ QueueConfig }} = require('./dist/config');
                try {{
                    new QueueConfig({{ timeoutSeconds: {val} }});
                    process.exit(0);
                }} catch (e) {{
                    process.exit(1);
                }}
            """)
            assert result.returncode == 1, f"Should reject timeoutSeconds: {val}"


# ============================================================
# 2. Job Model — State Machine
# ============================================================

class TestJobStateMachine:
    def test_creates_with_defaults(self):
        result = run_node("""
            const { Job, JobStatus, JobPriority } = require('./dist/models/job');
            const job = new Job('test-job', { action: 'echo' });
            console.log(JSON.stringify({
                name: job.name,
                status: job.status,
                priority: job.priority,
                hasId: !!job.id,
                retryCount: job.retryCount,
                maxRetries: job.maxRetries,
                isTerminal: job.isTerminal
            }));
        """)
        assert result.returncode == 0, f"Failed:\n{result.stderr}"
        data = json.loads(result.stdout.strip())
        assert data["name"] == "test-job"
        assert data["status"] == "pending"
        assert data["priority"] == 5
        assert data["hasId"] is True
        assert data["retryCount"] == 0
        assert data["maxRetries"] == 3
        assert data["isTerminal"] is False

    def test_start_transitions_pending_to_running(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.start();
            console.log(JSON.stringify({
                status: job.status,
                hasStartedAt: job.startedAt !== null && job.startedAt !== undefined
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["status"] == "running"
        assert data["hasStartedAt"] is True

    def test_start_rejects_from_completed(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.start();
            job.complete('ok');
            try {
                job.start();
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1

    def test_complete_transitions_running_to_completed(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.start();
            job.complete({ value: 42 });
            console.log(JSON.stringify({
                status: job.status,
                result: job.result,
                isTerminal: job.isTerminal,
                hasCompletedAt: job.completedAt !== null
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["status"] == "completed"
        assert data["result"] == {"value": 42}
        assert data["isTerminal"] is True
        assert data["hasCompletedAt"] is True

    def test_complete_rejects_from_pending(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            try {
                job.complete('x');
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1

    def test_fail_transitions_to_retrying(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {}, { maxRetries: 2 });
            job.start();
            job.fail('some error');
            console.log(JSON.stringify({
                status: job.status,
                retryCount: job.retryCount,
                error: job.error,
                isTerminal: job.isTerminal
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["status"] == "retrying"
        assert data["retryCount"] == 1
        assert data["error"] == "some error"
        assert data["isTerminal"] is False

    def test_fail_transitions_to_failed_when_exhausted(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {}, { maxRetries: 0 });
            job.start();
            job.fail('fatal');
            console.log(JSON.stringify({
                status: job.status,
                isTerminal: job.isTerminal,
                hasCompletedAt: job.completedAt !== null
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["status"] == "failed"
        assert data["isTerminal"] is True
        assert data["hasCompletedAt"] is True

    def test_fail_rejects_from_pending(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            try {
                new Job('j', {}).fail('err');
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1

    def test_cancel_from_pending(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.cancel();
            console.log(JSON.stringify({
                status: job.status,
                isTerminal: job.isTerminal
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["status"] == "cancelled"
        assert data["isTerminal"] is True

    def test_cancel_from_running(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.start();
            job.cancel();
            console.log(job.status);
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "cancelled"

    def test_cancel_rejects_from_completed(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            job.start();
            job.complete();
            try { job.cancel(); process.exit(0); }
            catch (e) { process.exit(1); }
        """)
        assert result.returncode == 1

    def test_cancel_rejects_from_failed(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {}, { maxRetries: 0 });
            job.start();
            job.fail('err');
            try { job.cancel(); process.exit(0); }
            catch (e) { process.exit(1); }
        """)
        assert result.returncode == 1

    def test_duration_null_before_start(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('j', {});
            console.log(JSON.stringify(job.duration));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "null"

    def test_to_dict_from_dict_roundtrip(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const job = new Job('roundtrip', { key: 'val' }, { priority: 2, tags: ['a', 'b'] });
            const dict = job.toDict();
            const restored = Job.fromDict(dict);
            console.log(JSON.stringify({
                name: restored.name,
                payload: restored.payload,
                priority: restored.priority,
                tags: restored.tags,
                idMatch: restored.id === job.id
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["name"] == "roundtrip"
        assert data["payload"] == {"key": "val"}
        assert data["priority"] == 2
        assert data["tags"] == ["a", "b"]
        assert data["idMatch"] is True


# ============================================================
# 3. TaskQueue
# ============================================================

class TestTaskQueue:
    def test_push_pop_respects_priority(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            q.push(new Job('low', {}, { priority: 8 }));
            q.push(new Job('high', {}, { priority: 1 }));
            q.push(new Job('mid', {}, { priority: 5 }));
            const names = [q.pop().name, q.pop().name, q.pop().name];
            console.log(JSON.stringify(names));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == ["high", "mid", "low"]

    def test_pop_empty_returns_null(self):
        result = run_node("""
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            console.log(JSON.stringify(q.pop()));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "null"

    def test_push_rejects_when_full(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(2);
            q.push(new Job('a', {}));
            q.push(new Job('b', {}));
            try { q.push(new Job('c', {})); process.exit(0); }
            catch (e) { process.exit(1); }
        """)
        assert result.returncode == 1

    def test_push_rejects_duplicate(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            const job = new Job('dup', {});
            q.push(job);
            try { q.push(job); process.exit(0); }
            catch (e) { process.exit(1); }
        """)
        assert result.returncode == 1

    def test_remove_existing(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            const job = new Job('r', {});
            q.push(job);
            console.log(JSON.stringify({
                removed: q.remove(job.id),
                size: q.size
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["removed"] is True
        assert data["size"] == 0

    def test_remove_missing(self):
        result = run_node("""
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            console.log(q.remove('nonexistent'));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "false"

    def test_peek_without_removing(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            q.push(new Job('lo', {}, { priority: 9 }));
            q.push(new Job('hi', {}, { priority: 0 }));
            console.log(JSON.stringify({
                name: q.peek().name,
                size: q.size
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["name"] == "hi"
        assert data["size"] == 2

    def test_get_job_by_id(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            const job = new Job('find-me', {});
            q.push(job);
            console.log(JSON.stringify({
                found: q.getJob(job.id).name,
                missing: q.getJob('nope')
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["found"] == "find-me"
        assert data["missing"] is None

    def test_is_empty_and_is_full(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(1);
            const before = { empty: q.isEmpty, full: q.isFull };
            q.push(new Job('x', {}));
            const after = { empty: q.isEmpty, full: q.isFull };
            console.log(JSON.stringify({ before, after }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["before"]["empty"] is True
        assert data["before"]["full"] is False
        assert data["after"]["empty"] is False
        assert data["after"]["full"] is True

    def test_clear(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            q.push(new Job('a', {}));
            q.push(new Job('b', {}));
            console.log(JSON.stringify({
                cleared: q.clear(),
                size: q.size,
                empty: q.isEmpty
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["cleared"] == 2
        assert data["size"] == 0
        assert data["empty"] is True

    def test_get_all_jobs(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const q = new TaskQueue(10);
            q.push(new Job('x', {}));
            q.push(new Job('y', {}));
            console.log(q.getAllJobs().length);
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "2"


# ============================================================
# 4. JobResult
# ============================================================

class TestJobResult:
    def test_ok_factory(self):
        result = run_node("""
            const { JobResult } = require('./dist/models/result');
            const r = JobResult.ok('job-1', 42, { worker: 'w1' });
            console.log(JSON.stringify({
                success: r.success,
                value: r.value,
                jobId: r.jobId,
                isError: r.isError,
                metadata: r.metadata
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is True
        assert data["value"] == 42
        assert data["jobId"] == "job-1"
        assert data["isError"] is False
        assert data["metadata"] == {"worker": "w1"}

    def test_err_factory(self):
        result = run_node("""
            const { JobResult } = require('./dist/models/result');
            const r = JobResult.err('job-2', 'boom', { worker: 'w2' });
            console.log(JSON.stringify({
                success: r.success,
                error: r.error,
                isError: r.isError
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert data["error"] == "boom"
        assert data["isError"] is True

    def test_to_dict_from_dict_roundtrip(self):
        result = run_node("""
            const { JobResult } = require('./dist/models/result');
            const r = JobResult.ok('rt', 'val');
            const dict = r.toDict();
            const restored = JobResult.fromDict(dict);
            console.log(JSON.stringify({
                jobId: restored.jobId,
                success: restored.success,
                value: restored.value
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["jobId"] == "rt"
        assert data["success"] is True
        assert data["value"] == "val"


# ============================================================
# 5. CpuWorker
# ============================================================

class TestCpuWorker:
    def test_factorial_20(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('f', { action: 'factorial', n: 20 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["factorial"] == 2432902008176640000

    def test_factorial_0(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('f0', { action: 'factorial', n: 0 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"factorial": 1}

    def test_factorial_rejects_negative(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('fn', { action: 'factorial', n: -1 }));
                console.log(JSON.stringify({ success: r.success, error: r.error }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert "Invalid factorial input" in data["error"]

    def test_fibonacci_30(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('fib', { action: 'fibonacci', n: 30 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"fibonacci": 832040}

    def test_fibonacci_0_and_1(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r0 = await w.run(new Job('f0', { action: 'fibonacci', n: 0 }));
                const r1 = await w.run(new Job('f1', { action: 'fibonacci', n: 1 }));
                console.log(JSON.stringify([r0.value, r1.value]));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data == [{"fibonacci": 0}, {"fibonacci": 1}]

    def test_fibonacci_rejects_negative(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('fn', { action: 'fibonacci', n: -5 }));
                console.log(JSON.stringify({ success: r.success, error: r.error }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert "Invalid fibonacci input" in data["error"]

    def test_prime_check_97(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('p', { action: 'prime_check', n: 97 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"is_prime": True}

    def test_prime_check_100(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('p', { action: 'prime_check', n: 100 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"is_prime": False}

    def test_prime_check_below_2(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('p', { action: 'prime_check', n: 1 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"is_prime": False}

    def test_unknown_action(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                const r = await w.run(new Job('bad', { action: 'unknown_thing' }));
                console.log(JSON.stringify({ success: r.success, error: r.error }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert "Unknown CPU action" in data["error"]

    def test_worker_stats(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { CpuWorker } = require('./dist/workers/cpu_worker');
            (async () => {
                const w = new CpuWorker('cpu-test', 5.0);
                await w.run(new Job('s', { action: 'factorial', n: 5 }));
                console.log(JSON.stringify(w.stats));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["workerId"] == "cpu-test"
        assert data["jobsProcessed"] == 1
        assert data["isBusy"] is False


# ============================================================
# 6. IoWorker
# ============================================================

class TestIoWorker:
    def test_echo(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('e', { action: 'echo', message: 'hello', delay: 0.01 }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"echoed": "hello"}

    def test_transform_uppercase(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('t', {
                    action: 'transform',
                    data: { name: 'test', count: 5 },
                    operation: 'uppercase'
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"name": "TEST", "count": 5}

    def test_transform_lowercase(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('t', {
                    action: 'transform',
                    data: { Title: 'HELLO' },
                    operation: 'lowercase'
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"Title": "hello"}

    def test_transform_identity(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('t', {
                    action: 'transform',
                    data: { a: 1, b: 'two' },
                    operation: 'identity'
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"a": 1, "b": "two"}

    def test_transform_keys_only(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('t', {
                    action: 'transform',
                    data: { x: 1, y: 2, z: 3 },
                    operation: 'keys_only'
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"keys": ["x", "y", "z"]}

    def test_transform_unknown_operation(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('t', {
                    action: 'transform', data: {}, operation: 'reverse'
                }));
                console.log(JSON.stringify({ success: r.success, error: r.error }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert "Unknown transform operation" in data["error"]

    def test_aggregate_numeric(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('a', {
                    action: 'aggregate', items: [1, 2, 3, 4, 5]
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {
            "count": 5, "sum": 15, "avg": 3.0, "min": 1, "max": 5
        }

    def test_aggregate_empty(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('a', {
                    action: 'aggregate', items: []
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {
            "count": 0, "sum": 0, "avg": 0.0, "min": None, "max": None
        }

    def test_aggregate_mixed_types(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('a', {
                    action: 'aggregate', items: [10, 'skip', 20, null, 30]
                }));
                console.log(JSON.stringify({
                    count: r.value.count, sum: r.value.sum, avg: r.value.avg
                }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["count"] == 3
        assert data["sum"] == 60
        assert data["avg"] == 20.0

    def test_aggregate_no_numeric(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('a', {
                    action: 'aggregate', items: ['a', 'b', 'c']
                }));
                console.log(JSON.stringify(r.value));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {
            "count": 3, "sum": 0, "avg": 0.0, "min": None, "max": None
        }

    def test_unknown_io_action(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { IoWorker } = require('./dist/workers/io_worker');
            (async () => {
                const w = new IoWorker('io-test', 5.0);
                const r = await w.run(new Job('bad', { action: 'nope' }));
                console.log(JSON.stringify({ success: r.success, error: r.error }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is False
        assert "Unknown IO action" in data["error"]


# ============================================================
# 7. Scheduler
# ============================================================

class TestScheduler:
    def test_submit_and_process(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            (async () => {
                const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
                sched.submit(new Job('factorial', { action: 'factorial', n: 10 }));
                const r = await sched.processNext();
                console.log(JSON.stringify({ success: r.success, value: r.value }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["success"] is True
        assert data["value"] == {"factorial": 3628800}

    def test_submit_rejects_invalid_priority(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            const sched = new Scheduler(new QueueConfig());
            try {
                sched.submit(new Job('bad', {}, { priority: 11 }));
                process.exit(0);
            } catch (e) {
                process.exit(1);
            }
        """)
        assert result.returncode == 1

    def test_run_all(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            (async () => {
                const sched = new Scheduler(new QueueConfig({ maxWorkers: 4, maxQueueSize: 10 }));
                sched.submit(new Job('f1', { action: 'factorial', n: 5 }, { priority: 1 }));
                sched.submit(new Job('f2', { action: 'fibonacci', n: 10 }, { priority: 2 }));
                const results = await sched.runAll();
                const successes = results.filter(r => r.success).length;
                console.log(JSON.stringify({ total: results.length, successes }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["total"] >= 2
        assert data["successes"] == 2

    def test_get_stats(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            (async () => {
                const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
                sched.submit(new Job('s', { action: 'factorial', n: 3 }));
                await sched.runAll();
                const stats = sched.getStats();
                console.log(JSON.stringify({
                    queueSize: stats.queueSize,
                    hasResults: stats.totalResults >= 1,
                    strategy: stats.strategy,
                    workerCount: stats.workers.length
                }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["queueSize"] == 0
        assert data["hasResults"] is True
        assert data["strategy"] == "priority"
        assert data["workerCount"] == 2

    def test_get_result_by_id(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            (async () => {
                const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
                const job = new Job('gr', { action: 'prime_check', n: 7 });
                const id = sched.submit(job);
                await sched.runAll();
                const r = sched.getResult(id);
                console.log(JSON.stringify({ found: r !== null, success: r.success }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["found"] is True
        assert data["success"] is True

    def test_round_robin_strategy(self):
        result = run_node("""
            const { QueueConfig } = require('./dist/config');
            const { Scheduler } = require('./dist/scheduler/scheduler');
            const sched = new Scheduler(new QueueConfig({ schedulingStrategy: 'round_robin' }));
            console.log(sched.getStats().strategy);
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "round_robin"


# ============================================================
# 8. Scheduling Strategies
# ============================================================

class TestPriorityScheduler:
    def test_next_job(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const { PriorityScheduler } = require('./dist/scheduler/priority');
            const ps = new PriorityScheduler();
            const q = new TaskQueue(10);
            q.push(new Job('a', {}, { priority: 5 }));
            const job = ps.nextJob(q);
            console.log(job.name);
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "a"

    def test_should_preempt_higher(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { PriorityScheduler } = require('./dist/scheduler/priority');
            const ps = new PriorityScheduler();
            console.log(ps.shouldPreempt(
                new Job('c', {}, { priority: 5 }),
                new Job('i', {}, { priority: 1 })
            ));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "true"

    def test_should_not_preempt_lower(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { PriorityScheduler } = require('./dist/scheduler/priority');
            const ps = new PriorityScheduler();
            console.log(ps.shouldPreempt(
                new Job('c', {}, { priority: 1 }),
                new Job('i', {}, { priority: 5 })
            ));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "false"


class TestRoundRobinScheduler:
    def test_next_job(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { TaskQueue } = require('./dist/models/queue');
            const { RoundRobinScheduler } = require('./dist/scheduler/round_robin');
            const rr = new RoundRobinScheduler();
            const q = new TaskQueue(10);
            q.push(new Job('a', {}));
            console.log(rr.nextJob(q) !== null);
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "true"

    def test_should_preempt_always_false(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { RoundRobinScheduler } = require('./dist/scheduler/round_robin');
            const rr = new RoundRobinScheduler();
            console.log(rr.shouldPreempt(
                new Job('c', {}, { priority: 10 }),
                new Job('i', {}, { priority: 0 })
            ));
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "false"


# ============================================================
# 9. Serialization
# ============================================================

class TestSerialization:
    def test_job_roundtrip(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { serializeJob, deserializeJob } = require('./dist/utils/serialization');
            const job = new Job('ser', { key: 'value' }, { priority: 3, tags: ['x'] });
            const json = serializeJob(job);
            const restored = deserializeJob(json);
            console.log(JSON.stringify({
                name: restored.name,
                payload: restored.payload,
                priority: restored.priority,
                tags: restored.tags
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["name"] == "ser"
        assert data["payload"] == {"key": "value"}
        assert data["priority"] == 3
        assert data["tags"] == ["x"]

    def test_result_roundtrip(self):
        result = run_node("""
            const { JobResult } = require('./dist/models/result');
            const { serializeResult, deserializeResult } = require('./dist/utils/serialization');
            const r = JobResult.ok('r1', { data: true });
            const json = serializeResult(r);
            const restored = deserializeResult(json);
            console.log(JSON.stringify({
                jobId: restored.jobId,
                success: restored.success,
                value: restored.value
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["jobId"] == "r1"
        assert data["success"] is True
        assert data["value"] == {"data": True}

    def test_many_jobs_roundtrip(self):
        result = run_node("""
            const { Job } = require('./dist/models/job');
            const { serializeManyJobs, deserializeManyJobs } = require('./dist/utils/serialization');
            const jobs = [new Job('a', { x: 1 }), new Job('b', { y: 2 })];
            const json = serializeManyJobs(jobs);
            const restored = deserializeManyJobs(json);
            console.log(JSON.stringify({
                length: restored.length,
                names: restored.map(j => j.name)
            }));
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["length"] == 2
        assert data["names"] == ["a", "b"]


# ============================================================
# 10. Validation
# ============================================================

class TestValidation:
    def test_validate_payload_missing_keys(self):
        result = run_node("""
            const { validatePayload } = require('./dist/utils/validation');
            const errors = validatePayload({ a: 1 }, ['a', 'b', 'c']);
            console.log(JSON.stringify(errors));
        """)
        assert result.returncode == 0
        errors = json.loads(result.stdout.strip())
        assert len(errors) == 2
        assert "Missing required key: b" in errors
        assert "Missing required key: c" in errors

    def test_validate_payload_all_present(self):
        result = run_node("""
            const { validatePayload } = require('./dist/utils/validation');
            console.log(JSON.stringify(validatePayload({ a: 1, b: 2 }, ['a', 'b'])));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == []

    def test_validate_payload_rejects_non_dict(self):
        result = run_node("""
            const { validatePayload } = require('./dist/utils/validation');
            const errors = validatePayload('not a dict', ['a']);
            console.log(JSON.stringify(errors));
        """)
        assert result.returncode == 0
        errors = json.loads(result.stdout.strip())
        assert len(errors) == 1
        assert "dictionary" in errors[0].lower() or "object" in errors[0].lower()

    def test_validate_priority_valid(self):
        result = run_node("""
            const { validatePriority } = require('./dist/utils/validation');
            console.log(JSON.stringify([
                validatePriority(0),
                validatePriority(10),
                validatePriority(5)
            ]));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == [True, True, True]

    def test_validate_priority_invalid(self):
        result = run_node("""
            const { validatePriority } = require('./dist/utils/validation');
            console.log(JSON.stringify([
                validatePriority(-1),
                validatePriority(11)
            ]));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == [False, False]

    def test_validate_job_name_valid(self):
        result = run_node("""
            const { validateJobName } = require('./dist/utils/validation');
            console.log(JSON.stringify(validateJobName('my-job_v1.0')));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == []

    def test_validate_job_name_empty(self):
        result = run_node("""
            const { validateJobName } = require('./dist/utils/validation');
            console.log(JSON.stringify(validateJobName('')));
        """)
        assert result.returncode == 0
        assert len(json.loads(result.stdout.strip())) > 0

    def test_validate_job_name_too_long(self):
        result = run_node("""
            const { validateJobName } = require('./dist/utils/validation');
            console.log(JSON.stringify(validateJobName('a'.repeat(257))));
        """)
        assert result.returncode == 0
        assert len(json.loads(result.stdout.strip())) > 0

    def test_validate_job_name_special_chars(self):
        result = run_node("""
            const { validateJobName } = require('./dist/utils/validation');
            console.log(JSON.stringify(validateJobName('job name with spaces!')));
        """)
        assert result.returncode == 0
        assert len(json.loads(result.stdout.strip())) > 0

    def test_sanitize_tags(self):
        result = run_node("""
            const { sanitizeTags } = require('./dist/utils/validation');
            console.log(JSON.stringify(sanitizeTags(['Hello', ' hello ', 'WORLD', 'world', ''])));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == ["hello", "world"]

    def test_sanitize_tags_empty(self):
        result = run_node("""
            const { sanitizeTags } = require('./dist/utils/validation');
            console.log(JSON.stringify(sanitizeTags([])));
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == []


# ============================================================
# 11. MemoryStorage
# ============================================================

class TestMemoryStorage:
    def test_save_and_load(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                await store.save('key1', { data: 'test' });
                const loaded = await store.load('key1');
                console.log(JSON.stringify(loaded));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == {"data": "test"}

    def test_load_missing_returns_null(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                console.log(JSON.stringify(await store.load('missing')));
            })();
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "null"

    def test_delete_existing(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                await store.save('k', { x: 1 });
                const deleted = await store.delete('k');
                const after = await store.load('k');
                console.log(JSON.stringify({ deleted, after }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["deleted"] is True
        assert data["after"] is None

    def test_delete_missing(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                console.log(await store.delete('nope'));
            })();
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "false"

    def test_exists(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                await store.save('e', {});
                console.log(JSON.stringify({
                    yes: await store.exists('e'),
                    no: await store.exists('nope')
                }));
            })();
        """)
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["yes"] is True
        assert data["no"] is False

    def test_list_keys_with_prefix(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                await store.save('user:1', {});
                await store.save('user:2', {});
                await store.save('job:1', {});
                console.log(JSON.stringify(await store.listKeys('user:')));
            })();
        """)
        assert result.returncode == 0
        assert json.loads(result.stdout.strip()) == ["user:1", "user:2"]

    def test_save_makes_copy(self):
        result = run_node("""
            const { MemoryStorage } = require('./dist/storage/memory');
            (async () => {
                const store = new MemoryStorage();
                const original = { mutable: 'yes' };
                await store.save('copy-test', original);
                original.mutable = 'mutated';
                const loaded = await store.load('copy-test');
                console.log(loaded.mutable);
            })();
        """)
        assert result.returncode == 0
        assert result.stdout.strip() == "yes"