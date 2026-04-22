import { Job } from "../models/job";
import { CpuWorker } from "../workers/cpu_worker";

describe("CpuWorker", () => {
  let worker: CpuWorker;

  beforeEach(() => {
    worker = new CpuWorker("cpu-test", 5.0);
  });

  test("factorial of 20", async () => {
    const job = new Job("f", { action: "factorial", n: 20 });
    const result = await worker.run(job);
    expect(result.success).toBe(true);
    expect(result.value).toEqual({ factorial: 2432902008176640000 });
  });

  test("factorial of 0 returns 1", async () => {
    const result = await worker.run(new Job("f0", { action: "factorial", n: 0 }));
    expect(result.success).toBe(true);
    expect(result.value).toEqual({ factorial: 1 });
  });

  test("factorial of 1 returns 1", async () => {
    const result = await worker.run(new Job("f1", { action: "factorial", n: 1 }));
    expect(result.value).toEqual({ factorial: 1 });
  });

  test("factorial rejects negative input", async () => {
    const result = await worker.run(new Job("fn", { action: "factorial", n: -1 }));
    expect(result.success).toBe(false);
    expect(result.error).toContain("Invalid factorial input");
  });

  test("factorial rejects non-integer input", async () => {
    const result = await worker.run(new Job("fi", { action: "factorial", n: "abc" }));
    expect(result.success).toBe(false);
  });

  test("fibonacci of 30", async () => {
    const result = await worker.run(new Job("fib", { action: "fibonacci", n: 30 }));
    expect(result.success).toBe(true);
    expect(result.value).toEqual({ fibonacci: 832040 });
  });

  test("fibonacci of 0 and 1", async () => {
    const r0 = await worker.run(new Job("f0", { action: "fibonacci", n: 0 }));
    const r1 = await worker.run(new Job("f1", { action: "fibonacci", n: 1 }));
    expect(r0.value).toEqual({ fibonacci: 0 });
    expect(r1.value).toEqual({ fibonacci: 1 });
  });

  test("fibonacci rejects negative", async () => {
    const result = await worker.run(new Job("fn", { action: "fibonacci", n: -5 }));
    expect(result.success).toBe(false);
    expect(result.error).toContain("Invalid fibonacci input");
  });

  test("prime_check identifies primes correctly", async () => {
    const primes = [2, 3, 5, 7, 11, 13, 97];
    for (const n of primes) {
      const result = await worker.run(new Job(`p${n}`, { action: "prime_check", n }));
      expect(result.value).toEqual({ is_prime: true });
    }
  });

  test("prime_check identifies non-primes correctly", async () => {
    const nonPrimes = [4, 6, 9, 15, 100];
    for (const n of nonPrimes) {
      const result = await worker.run(new Job(`p${n}`, { action: "prime_check", n }));
      expect(result.value).toEqual({ is_prime: false });
    }
  });

  test("prime_check for n < 2 returns false", async () => {
    for (const n of [0, 1, -1]) {
      const result = await worker.run(new Job(`p${n}`, { action: "prime_check", n }));
      expect(result.value).toEqual({ is_prime: false });
    }
  });

  test("unknown action fails", async () => {
    const result = await worker.run(new Job("bad", { action: "nope" }));
    expect(result.success).toBe(false);
    expect(result.error).toContain("Unknown CPU action");
  });

    test("stats update after execution", async () => {
    await worker.run(new Job("s1", { action: "factorial", n: 5 }));
    await worker.run(new Job("s2", { action: "factorial", n: 3 }));
    const stats = worker.stats as Record<string, unknown>;
    expect(stats.workerId).toBe("cpu-test");
    expect(stats.jobsProcessed).toBe(2);
    expect(stats.totalExecutionTime).toBeGreaterThan(0);
    expect(stats.isBusy).toBe(false);
  });
});