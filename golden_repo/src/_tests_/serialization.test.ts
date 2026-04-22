import { Job } from "../models/job";
import { JobResult } from "../models/result";
import {
  serializeJob,
  deserializeJob,
  serializeResult,
  deserializeResult,
  serializeManyJobs,
  deserializeManyJobs,
} from "../utils/serialization";

describe("Serialization", () => {
  test("job roundtrip preserves all fields", () => {
    const job = new Job("ser", { key: "value" }, { priority: 3, tags: ["x", "y"] });
    const json = serializeJob(job);
    expect(typeof json).toBe("string");
    const restored = deserializeJob(json);
    expect(restored.name).toBe("ser");
    expect(restored.payload).toEqual({ key: "value" });
    expect(restored.priority).toBe(3);
    expect(restored.tags).toEqual(["x", "y"]);
    expect(restored.id).toBe(job.id);
  });

  test("result roundtrip preserves all fields", () => {
    const result = JobResult.ok("r1", { data: true }, { worker: "w" });
    const json = serializeResult(result);
    const restored = deserializeResult(json);
    expect(restored.jobId).toBe("r1");
    expect(restored.success).toBe(true);
    expect(restored.value).toEqual({ data: true });
  });

  test("many jobs roundtrip", () => {
    const jobs = [
      new Job("a", { x: 1 }),
      new Job("b", { y: 2 }),
      new Job("c", { z: 3 }),
    ];
    const json = serializeManyJobs(jobs);
    const restored = deserializeManyJobs(json);
    expect(restored.length).toBe(3);
    expect(restored.map((j) => j.name)).toEqual(["a", "b", "c"]);
  });

  test("serialized job is valid JSON", () => {
    const job = new Job("json", { nested: { a: [1, 2] } });
    const json = serializeJob(job);
    expect(() => JSON.parse(json)).not.toThrow();
  });

  test("error result roundtrip", () => {
    const result = JobResult.err("e1", "something broke");
    const restored = deserializeResult(serializeResult(result));
    expect(restored.success).toBe(false);
    expect(restored.error).toBe("something broke");
  });
});