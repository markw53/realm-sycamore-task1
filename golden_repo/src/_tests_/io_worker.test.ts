import { Job } from "../models/job";
import { IoWorker } from "../workers/io_worker";

describe("IoWorker", () => {
  let worker: IoWorker;

  beforeEach(() => {
    worker = new IoWorker("io-test", 5.0);
  });

  test("echo returns message after delay", async () => {
    const result = await worker.run(
      new Job("e", { action: "echo", message: "hello", delay: 0.01 })
    );
    expect(result.success).toBe(true);
    expect(result.value).toEqual({ echoed: "hello" });
  });

  test("echo with empty message", async () => {
    const result = await worker.run(
      new Job("e", { action: "echo", message: "", delay: 0.01 })
    );
    expect(result.value).toEqual({ echoed: "" });
  });

  test("transform uppercase", async () => {
    const result = await worker.run(new Job("t", {
      action: "transform",
      data: { name: "test", count: 5 },
      operation: "uppercase",
    }));
    expect(result.success).toBe(true);
    expect(result.value).toEqual({ name: "TEST", count: 5 });
  });

  test("transform lowercase", async () => {
    const result = await worker.run(new Job("t", {
      action: "transform",
      data: { Title: "HELLO", num: 42 },
      operation: "lowercase",
    }));
    expect(result.value).toEqual({ Title: "hello", num: 42 });
  });

  test("transform identity returns copy", async () => {
    const data = { a: 1, b: "two" };
    const result = await worker.run(new Job("t", {
      action: "transform", data, operation: "identity",
    }));
    expect(result.value).toEqual(data);
  });

  test("transform keys_only", async () => {
    const result = await worker.run(new Job("t", {
      action: "transform",
      data: { x: 1, y: 2, z: 3 },
      operation: "keys_only",
    }));
    expect(result.value).toEqual({ keys: ["x", "y", "z"] });
  });

  test("transform unknown operation fails", async () => {
    const result = await worker.run(new Job("t", {
      action: "transform", data: {}, operation: "reverse",
    }));
    expect(result.success).toBe(false);
    expect(result.error).toContain("Unknown transform operation");
  });

  test("aggregate with numeric items", async () => {
    const result = await worker.run(new Job("a", {
      action: "aggregate", items: [1, 2, 3, 4, 5],
    }));
    expect(result.value).toEqual({
      count: 5, sum: 15, avg: 3.0, min: 1, max: 5,
    });
  });

  test("aggregate with empty list", async () => {
    const result = await worker.run(new Job("a", {
      action: "aggregate", items: [],
    }));
    expect(result.value).toEqual({
      count: 0, sum: 0, avg: 0.0, min: null, max: null,
    });
  });

  test("aggregate with mixed types filters non-numeric", async () => {
    const result = await worker.run(new Job("a", {
      action: "aggregate", items: [10, "skip", 20, null, 30],
    }));
    const value = result.value as Record<string, unknown>;
    expect(value.count).toBe(3);
    expect(value.sum).toBe(60);
    expect(value.avg).toBe(20.0);
  });

    test("aggregate with only non-numeric items", async () => {
    const result = await worker.run(new Job("a", {
      action: "aggregate", items: ["a", "b", "c"],
    }));
    const value = result.value as Record<string, unknown>;
    expect(value.count).toBe(3);
    expect(value.sum).toBe(0);
    expect(value.avg).toBe(0.0);
    expect(value.min).toBeNull();
    expect(value.max).toBeNull();
  });

  test("unknown IO action fails", async () => {
    const result = await worker.run(new Job("bad", { action: "nope" }));
    expect(result.success).toBe(false);
    expect(result.error).toContain("Unknown IO action");
  });
});