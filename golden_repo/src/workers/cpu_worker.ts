/**
 * Worker for CPU-bound tasks.
 */

import { Job } from "../models/job";
import { BaseWorker } from "./base";

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
  async execute(job: Job): Promise<unknown> {
    const action = job.payload.action as string | undefined;

    if (action === "factorial") {
      const n = job.payload.n;
      if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
        throw new Error(`Invalid factorial input: ${n}`);
      }
      const result = await Promise.resolve(factorial(n));
      return { factorial: result };
    } else if (action === "fibonacci") {
      const n = job.payload.n;
      if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
        throw new Error(`Invalid fibonacci input: ${n}`);
      }
      const result = await Promise.resolve(fibonacci(n));
      return { fibonacci: result };
    } else if (action === "prime_check") {
      const n = job.payload.n;
      if (typeof n !== "number" || !Number.isInteger(n) || n < 2) {
        return { is_prime: false };
      }
      const result = await Promise.resolve(isPrime(n));
      return { is_prime: result };
    } else {
      throw new Error(`Unknown CPU action: ${action}`);
    }
  }
}