/**
 * Worker for CPU-bound tasks.
 */

import { Job } from "../models/job";
import { BaseWorker } from "./base";
import { JobResult } from "../models/result";

function factorial(n: number): number {
  if (n <= 1) return 1;
  let result = 1;
  for (let i = 2; i <= n; i++) {
    result *= i;
  }
  return result;
}

function fibonacci(n: number): number {
  if (n <= 1) return n;
  let a = 0;
  let b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}

function isPrime(n: number): boolean {
  if (n < 2) return false;
  if (n < 4) return true;
  if (n % 2 === 0 || n % 3 === 0) return false;
  let i = 5;
  while (i * i <= n) {
    if (n % i === 0 || n % (i + 2) === 0) return false;
    i += 6;
  }
  return true;
}

export class CpuWorker extends BaseWorker {
  async execute(job: Job): Promise<JobResult> {
    const action = job.payload.action as string | undefined;

    try {
      if (action === "factorial") {
        const n = job.payload.n;
        if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
          return JobResult.err(job.id, `Invalid factorial input: ${n}`);
        }
        return JobResult.ok(job.id, { factorial: factorial(n) });

      } else if (action === "fibonacci") {
        const n = job.payload.n;
        if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
          return JobResult.err(job.id, `Invalid fibonacci input: ${n}`);
        }
        return JobResult.ok(job.id, { fibonacci: fibonacci(n) });

      } else if (action === "prime_check") {
        const n = job.payload.n;
        if (typeof n !== "number" || !Number.isInteger(n) || n < 2) {
          return JobResult.ok(job.id, { is_prime: false });
        }
        return JobResult.ok(job.id, { is_prime: isPrime(n) });

      } else {
        return JobResult.err(job.id, `Unknown CPU action: ${action}`);
      }
    } catch (e: any) {
      return JobResult.err(job.id, String(e.message ?? e));
    }
  }
}
