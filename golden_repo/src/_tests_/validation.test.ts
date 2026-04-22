import {
  validatePayload,
  validatePriority,
  validateJobName,
  sanitizeTags,
} from "../utils/validation";

describe("validatePayload", () => {
  test("reports missing keys", () => {
    const errors = validatePayload({ a: 1 }, ["a", "b", "c"]);
    expect(errors.length).toBe(2);
    expect(errors).toContain("Missing required key: b");
    expect(errors).toContain("Missing required key: c");
  });

  test("returns empty when all keys present", () => {
    expect(validatePayload({ a: 1, b: 2, c: 3 }, ["a", "b"])).toEqual([]);
  });

  test("rejects non-object input", () => {
    const errors = validatePayload("not a dict" as any, ["a"]);
    expect(errors.length).toBe(1);
  });

  test("handles empty required keys", () => {
    expect(validatePayload({ a: 1 }, [])).toEqual([]);
  });
});

describe("validatePriority", () => {
  test("accepts 0-10", () => {
    for (const n of [0, 1, 5, 10]) {
      expect(validatePriority(n)).toBe(true);
    }
  });

  test("rejects out of range", () => {
    expect(validatePriority(-1)).toBe(false);
    expect(validatePriority(11)).toBe(false);
    expect(validatePriority(100)).toBe(false);
  });
});

describe("validateJobName", () => {
  test("accepts valid names", () => {
    expect(validateJobName("my-job_v1.0")).toEqual([]);
    expect(validateJobName("simple")).toEqual([]);
    expect(validateJobName("a")).toEqual([]);
  });

  test("rejects empty string", () => {
    expect(validateJobName("").length).toBeGreaterThan(0);
  });

  test("rejects names over 256 chars", () => {
    expect(validateJobName("a".repeat(257)).length).toBeGreaterThan(0);
  });

  test("rejects special characters", () => {
    expect(validateJobName("job name with spaces!").length).toBeGreaterThan(0);
    expect(validateJobName("job@name").length).toBeGreaterThan(0);
  });

  test("accepts exactly 256 chars", () => {
    expect(validateJobName("a".repeat(256))).toEqual([]);
  });
});

describe("sanitizeTags", () => {
  test("deduplicates and normalizes", () => {
    expect(sanitizeTags(["Hello", " hello ", "WORLD", "world", ""])).toEqual([
      "hello",
      "world",
    ]);
  });

  test("handles empty list", () => {
    expect(sanitizeTags([])).toEqual([]);
  });

  test("preserves order of first occurrence", () => {
    expect(sanitizeTags(["B", "A", "b", "a"])).toEqual(["b", "a"]);
  });

  test("strips whitespace", () => {
    expect(sanitizeTags(["  spaced  ", "\ttabbed\t"])).toEqual(["spaced", "tabbed"]);
  });
});