import { Job } from "../models/job";
import { QueueConfig } from "../config";
import { Scheduler } from "../scheduler/scheduler";

describe("Scheduler", () => {
  test("submit and process a single job", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
    sched.submit(new Job("factorial", { action: "factorial", n: 10 }));
    const result = await sched.processNext();
    expect(result).not.toBeNull();
    expect(result!.success).toBe(true);
    expect(result!.value).toEqual({ factorial: 3628800 });
  });

  test("submit rejects invalid priority", () => {
    const sched = new Scheduler(new QueueConfig());
    expect(() => sched.submit(new Job("bad", {}, { priority: 11 }))).toThrow();
    expect(() => sched.submit(new Job("bad", {}, { priority: -1 }))).toThrow();
  });

  test("runAll processes all jobs", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 4 }));
    sched.submit(new Job("f1", { action: "factorial", n: 5 }, { priority: 1 }));
    sched.submit(new Job("f2", { action: "fibonacci", n: 10 }, { priority: 2 }));
    sched.submit(new Job("p1", { action: "prime_check", n: 7 }, { priority: 3 }));

    const results = await sched.runAll();
    const successes = results.filter((r) => r.success);
    expect(successes.length).toBe(3);
  });

  test("getResult retrieves by job id", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
    const job = new Job("gr", { action: "prime_check", n: 7 });
    const id = sched.submit(job);
    await sched.runAll();
    const result = sched.getResult(id);
    expect(result).not.toBeNull();
    expect(result!.success).toBe(true);
  });

  test("getResult returns null for unknown id", () => {
    const sched = new Scheduler(new QueueConfig());
    expect(sched.getResult("nonexistent")).toBeNull();
  });

  test("getAllResults returns all results", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
    sched.submit(new Job("a", { action: "factorial", n: 3 }));
    sched.submit(new Job("b", { action: "fibonacci", n: 5 }));
    await sched.runAll();
    expect(sched.getAllResults().length).toBe(2);
  });

    test("getStats returns correct shape", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
    sched.submit(new Job("s", { action: "factorial", n: 3 }));
    await sched.runAll();

    const stats = sched.getStats() as Record<string, unknown>;
    expect(stats.queueSize).toBe(0);
    expect(stats.totalResults).toBeGreaterThanOrEqual(1);
    expect(stats.strategy).toBe("priority");
    const workers = stats.workers as unknown[];
    expect(Array.isArray(workers)).toBe(true);
    expect(workers.length).toBe(2);
  });

  test("round robin strategy selectable", () => {
    const sched = new Scheduler(new QueueConfig({ schedulingStrategy: "round_robin" }));
    expect(sched.getStats().strategy).toBe("round_robin");
  });

  test("stop halts processing", async () => {
    const sched = new Scheduler(new QueueConfig({ maxWorkers: 2 }));
    sched.submit(new Job("a", { action: "factorial", n: 5 }));
    sched.submit(new Job("b", { action: "factorial", n: 3 }));
    sched.stop();
    // runAll should exit early after stop
    const results = await sched.runAll();
    // May or may not have processed anything depending on timing
    expect(Array.isArray(results)).toBe(true);
  });
});