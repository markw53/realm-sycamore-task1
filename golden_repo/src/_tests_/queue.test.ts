import { Job } from "../models/job";
import { TaskQueue, QueueFullError, DuplicateJobError } from "../models/queue";

describe("TaskQueue", () => {
  test("push and pop respects priority ordering", () => {
    const q = new TaskQueue(10);
    q.push(new Job("low", {}, { priority: 8 }));
    q.push(new Job("high", {}, { priority: 1 }));
    q.push(new Job("mid", {}, { priority: 5 }));

    expect(q.size).toBe(3);
    expect(q.pop()!.name).toBe("high");
    expect(q.pop()!.name).toBe("mid");
    expect(q.pop()!.name).toBe("low");
  });

  test("FIFO tiebreaker for equal priorities", () => {
    const q = new TaskQueue(10);
    q.push(new Job("first", {}, { priority: 5 }));
    q.push(new Job("second", {}, { priority: 5 }));
    q.push(new Job("third", {}, { priority: 5 }));

    expect(q.pop()!.name).toBe("first");
    expect(q.pop()!.name).toBe("second");
    expect(q.pop()!.name).toBe("third");
  });

  test("pop returns null on empty queue", () => {
    const q = new TaskQueue(10);
    expect(q.pop()).toBeNull();
  });

  test("push rejects when full", () => {
    const q = new TaskQueue(2);
    q.push(new Job("a", {}));
    q.push(new Job("b", {}));
    expect(() => q.push(new Job("c", {}))).toThrow(QueueFullError);
  });

  test("push rejects duplicate job id", () => {
    const q = new TaskQueue(10);
    const job = new Job("dup", {});
    q.push(job);
    expect(() => q.push(job)).toThrow(DuplicateJobError);
  });

  test("remove returns true for existing job", () => {
    const q = new TaskQueue(10);
    const job = new Job("r", {});
    q.push(job);
    expect(q.remove(job.id)).toBe(true);
    expect(q.size).toBe(0);
  });

  test("remove returns false for missing job", () => {
    const q = new TaskQueue(10);
    expect(q.remove("nonexistent")).toBe(false);
  });

  test("peek returns highest priority without removing", () => {
    const q = new TaskQueue(10);
    q.push(new Job("lo", {}, { priority: 9 }));
    q.push(new Job("hi", {}, { priority: 0 }));
    expect(q.peek()!.name).toBe("hi");
    expect(q.size).toBe(2);
  });

  test("peek returns null on empty queue", () => {
    const q = new TaskQueue(10);
    expect(q.peek()).toBeNull();
  });

  test("getJob retrieves by id", () => {
    const q = new TaskQueue(10);
    const job = new Job("find-me", {});
    q.push(job);
    expect(q.getJob(job.id)!.name).toBe("find-me");
    expect(q.getJob("nope")).toBeNull();
  });

  test("isEmpty and isFull", () => {
    const q = new TaskQueue(1);
    expect(q.isEmpty).toBe(true);
    expect(q.isFull).toBe(false);
    q.push(new Job("x", {}));
    expect(q.isEmpty).toBe(false);
    expect(q.isFull).toBe(true);
  });

  test("clear removes all jobs and returns count", () => {
    const q = new TaskQueue(10);
    q.push(new Job("a", {}));
    q.push(new Job("b", {}));
    q.push(new Job("c", {}));
    expect(q.clear()).toBe(3);
    expect(q.size).toBe(0);
    expect(q.isEmpty).toBe(true);
  });

  test("getAllJobs returns all enqueued jobs", () => {
    const q = new TaskQueue(10);
    q.push(new Job("x", {}));
    q.push(new Job("y", {}));
    expect(q.getAllJobs().length).toBe(2);
  });

  test("pop skips removed jobs", () => {
    const q = new TaskQueue(10);
    const a = new Job("a", {}, { priority: 1 });
    const b = new Job("b", {}, { priority: 2 });
    const c = new Job("c", {}, { priority: 3 });
    q.push(a);
    q.push(b);
    q.push(c);
    q.remove(b.id);
    expect(q.pop()!.name).toBe("a");
    expect(q.pop()!.name).toBe("c");
  });
});