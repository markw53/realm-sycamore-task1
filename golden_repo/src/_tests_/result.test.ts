import { JobResult } from "../models/result";

describe("JobResult", () => {
  test("ok factory creates success result", () => {
    const r = JobResult.ok("job-1", 42, { worker: "w1" });
    expect(r.success).toBe(true);
    expect(r.value).toBe(42);
    expect(r.jobId).toBe("job-1");
    expect(r.isError).toBe(false);
    expect(r.error).toBeNull();
    expect(r.metadata).toEqual({ worker: "w1" });
    expect(r.timestamp).toBeGreaterThan(0);
  });

  test("err factory creates failure result", () => {
    const r = JobResult.err("job-2", "boom", { worker: "w2" });
    expect(r.success).toBe(false);
    expect(r.error).toBe("boom");
    expect(r.isError).toBe(true);
    expect(r.value).toBeNull();
  });

  test("toDict includes all fields", () => {
    const r = JobResult.ok("d", "val", { key: "meta" });
    const dict = r.toDict();
    expect(dict.jobId).toBe("d");
    expect(dict.success).toBe(true);
    expect(dict.value).toBe("val");
    expect(dict.metadata).toEqual({ key: "meta" });
  });

  test("fromDict roundtrip preserves fields", () => {
    const original = JobResult.err("rt", "oops");
    const restored = JobResult.fromDict(original.toDict());
    expect(restored.jobId).toBe("rt");
    expect(restored.success).toBe(false);
    expect(restored.error).toBe("oops");
  });
});