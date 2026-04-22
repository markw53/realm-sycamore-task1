import { Job, JobStatus, JobPriority, InvalidJobStateError } from "../models/job";

describe("Job", () => {
  test("creates with default values", () => {
    const job = new Job("test-job", { action: "echo" });
    expect(job.name).toBe("test-job");
    expect(job.status).toBe(JobStatus.PENDING);
    expect(job.priority).toBe(JobPriority.MEDIUM);
    expect(job.id).toBeDefined();
    expect(typeof job.id).toBe("string");
    expect(job.retryCount).toBe(0);
    expect(job.maxRetries).toBe(3);
    expect(job.tags).toEqual([]);
    expect(job.isTerminal).toBe(false);
    expect(job.startedAt).toBeNull();
    expect(job.completedAt).toBeNull();
    expect(job.result).toBeNull();
    expect(job.error).toBeNull();
  });

  test("creates with custom options", () => {
    const job = new Job("custom", { x: 1 }, {
      priority: 2,
      maxRetries: 5,
      timeout: 60,
      tags: ["urgent", "batch"],
    });
    expect(job.priority).toBe(2);
    expect(job.maxRetries).toBe(5);
    expect(job.timeout).toBe(60);
    expect(job.tags).toEqual(["urgent", "batch"]);
  });

  describe("state transitions", () => {
    test("start: PENDING → RUNNING", () => {
      const job = new Job("j", {});
      job.start();
      expect(job.status).toBe(JobStatus.RUNNING);
      expect(job.startedAt).not.toBeNull();
    });

    test("start: RETRYING → RUNNING", () => {
      const job = new Job("j", {}, { maxRetries: 3 });
      job.start();
      job.fail("err");
      expect(job.status).toBe(JobStatus.RETRYING);
      job.start();
      expect(job.status).toBe(JobStatus.RUNNING);
    });

    test("start rejects from COMPLETED", () => {
      const job = new Job("j", {});
      job.start();
      job.complete("ok");
      expect(() => job.start()).toThrow(InvalidJobStateError);
    });

    test("start rejects from FAILED", () => {
      const job = new Job("j", {}, { maxRetries: 0 });
      job.start();
      job.fail("err");
      expect(() => job.start()).toThrow(InvalidJobStateError);
    });

    test("start rejects from CANCELLED", () => {
      const job = new Job("j", {});
      job.cancel();
      expect(() => job.start()).toThrow(InvalidJobStateError);
    });

    test("complete: RUNNING → COMPLETED", () => {
      const job = new Job("j", {});
      job.start();
      job.complete({ value: 42 });
      expect(job.status).toBe(JobStatus.COMPLETED);
      expect(job.result).toEqual({ value: 42 });
      expect(job.completedAt).not.toBeNull();
      expect(job.isTerminal).toBe(true);
    });

    test("complete rejects from PENDING", () => {
      const job = new Job("j", {});
      expect(() => job.complete("x")).toThrow(InvalidJobStateError);
    });

    test("fail → RETRYING when retries remain", () => {
      const job = new Job("j", {}, { maxRetries: 2 });
      job.start();
      job.fail("error 1");
      expect(job.status).toBe(JobStatus.RETRYING);
      expect(job.retryCount).toBe(1);
      expect(job.error).toBe("error 1");
      expect(job.isTerminal).toBe(false);
    });

    test("fail → FAILED when retries exhausted", () => {
      const job = new Job("j", {}, { maxRetries: 0 });
      job.start();
      job.fail("fatal");
      expect(job.status).toBe(JobStatus.FAILED);
      expect(job.completedAt).not.toBeNull();
      expect(job.isTerminal).toBe(true);
    });

    test("fail rejects from PENDING", () => {
      const job = new Job("j", {});
      expect(() => job.fail("err")).toThrow(InvalidJobStateError);
    });

    test("cancel from PENDING", () => {
      const job = new Job("j", {});
      job.cancel();
      expect(job.status).toBe(JobStatus.CANCELLED);
      expect(job.completedAt).not.toBeNull();
      expect(job.isTerminal).toBe(true);
    });

    test("cancel from RUNNING", () => {
      const job = new Job("j", {});
      job.start();
      job.cancel();
      expect(job.status).toBe(JobStatus.CANCELLED);
    });

    test("cancel rejects from COMPLETED", () => {
      const job = new Job("j", {});
      job.start();
      job.complete();
      expect(() => job.cancel()).toThrow(InvalidJobStateError);
    });

    test("cancel rejects from FAILED", () => {
      const job = new Job("j", {}, { maxRetries: 0 });
      job.start();
      job.fail("err");
      expect(() => job.cancel()).toThrow(InvalidJobStateError);
    });
  });

  describe("properties", () => {
    test("duration is null before start", () => {
      const job = new Job("j", {});
      expect(job.duration).toBeNull();
    });

    test("duration is non-negative after start", () => {
      const job = new Job("j", {});
      job.start();
      expect(job.duration).not.toBeNull();
      expect(job.duration!).toBeGreaterThanOrEqual(0);
    });

    test("isTerminal for all terminal states", () => {
      const completed = new Job("c", {});
      completed.start();
      completed.complete();
      expect(completed.isTerminal).toBe(true);

      const failed = new Job("f", {}, { maxRetries: 0 });
      failed.start();
      failed.fail("err");
      expect(failed.isTerminal).toBe(true);

      const cancelled = new Job("x", {});
      cancelled.cancel();
      expect(cancelled.isTerminal).toBe(true);
    });

    test("isTerminal false for non-terminal states", () => {
      expect(new Job("p", {}).isTerminal).toBe(false);

      const running = new Job("r", {});
      running.start();
      expect(running.isTerminal).toBe(false);

      const retrying = new Job("rt", {}, { maxRetries: 3 });
      retrying.start();
      retrying.fail("err");
      expect(retrying.isTerminal).toBe(false);
    });
  });

  describe("serialization", () => {
    test("toDict includes all fields", () => {
      const job = new Job("ser", { key: "val" }, { priority: 2, tags: ["a", "b"] });
      const dict = job.toDict();
      expect(dict.id).toBe(job.id);
      expect(dict.name).toBe("ser");
      expect(dict.payload).toEqual({ key: "val" });
      expect(dict.priority).toBe(2);
      expect(dict.status).toBe("pending");
      expect(dict.tags).toEqual(["a", "b"]);
      expect(dict.retryCount).toBe(0);
      expect(dict.maxRetries).toBe(3);
    });

    test("fromDict roundtrip preserves all fields", () => {
      const original = new Job("rt", { data: [1, 2, 3] }, { priority: 1, tags: ["x"] });
      original.start();
      const dict = original.toDict();
      const restored = Job.fromDict(dict);
      expect(restored.id).toBe(original.id);
      expect(restored.name).toBe(original.name);
      expect(restored.payload).toEqual(original.payload);
      expect(restored.priority).toBe(original.priority);
      expect(restored.status).toBe(original.status);
      expect(restored.tags).toEqual(original.tags);
      expect(restored.startedAt).toBe(original.startedAt);
    });
  });
});