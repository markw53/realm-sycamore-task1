import { Job } from "../models/job";
import { TaskQueue } from "../models/queue";
import { PriorityScheduler } from "../scheduler/priority";
import { RoundRobinScheduler } from "../scheduler/round_robin";

describe("PriorityScheduler", () => {
  test("nextJob pops from queue", () => {
    const ps = new PriorityScheduler();
    const q = new TaskQueue(10);
    q.push(new Job("a", {}, { priority: 5 }));
    const job = ps.nextJob(q);
    expect(job).not.toBeNull();
    expect(job!.name).toBe("a");
    expect(q.isEmpty).toBe(true);
  });

  test("nextJob returns null on empty queue", () => {
    const ps = new PriorityScheduler();
    expect(ps.nextJob(new TaskQueue(10))).toBeNull();
  });

  test("shouldPreempt returns true when incoming has higher priority", () => {
    const ps = new PriorityScheduler();
    const current = new Job("c", {}, { priority: 5 });
    const incoming = new Job("i", {}, { priority: 1 });
    expect(ps.shouldPreempt(current, incoming)).toBe(true);
  });

  test("shouldPreempt returns false when incoming has lower priority", () => {
    const ps = new PriorityScheduler();
    const current = new Job("c", {}, { priority: 1 });
    const incoming = new Job("i", {}, { priority: 5 });
    expect(ps.shouldPreempt(current, incoming)).toBe(false);
  });

  test("shouldPreempt returns false for equal priority", () => {
    const ps = new PriorityScheduler();
    const current = new Job("c", {}, { priority: 3 });
    const incoming = new Job("i", {}, { priority: 3 });
    expect(ps.shouldPreempt(current, incoming)).toBe(false);
  });

  test("name is priority", () => {
    expect(new PriorityScheduler().name).toBe("priority");
  });
});

describe("RoundRobinScheduler", () => {
  test("nextJob pops from queue", () => {
    const rr = new RoundRobinScheduler();
    const q = new TaskQueue(10);
    q.push(new Job("a", {}));
    expect(rr.nextJob(q)).not.toBeNull();
  });

  test("shouldPreempt always returns false", () => {
    const rr = new RoundRobinScheduler();
    const c = new Job("c", {}, { priority: 10 });
    const i = new Job("i", {}, { priority: 0 });
    expect(rr.shouldPreempt(c, i)).toBe(false);
  });

  test("name is round_robin", () => {
    expect(new RoundRobinScheduler().name).toBe("round_robin");
  });
});