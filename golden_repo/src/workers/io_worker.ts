/**
 * Worker for I/O-bound tasks.
 */

import { Job } from "../models/job";
import { BaseWorker } from "./base";

function sleep(seconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

function transform(
  data: Record<string, unknown>,
  operation: string
): Record<string, unknown> {
  if (operation === "uppercase") {
    const result: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(data)) {
      result[k] = typeof v === "string" ? v.toUpperCase() : v;
    }
    return result;
  } else if (operation === "lowercase") {
    const result: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(data)) {
      result[k] = typeof v === "string" ? v.toLowerCase() : v;
    }
    return result;
  } else if (operation === "identity") {
    return { ...data };
  } else if (operation === "keys_only") {
    return { keys: Object.keys(data) };
  } else {
    throw new Error(`Unknown transform operation: ${operation}`);
  }
}

function aggregate(items: unknown[]): Record<string, unknown> {
  if (!items || items.length === 0) {
    return { count: 0, sum: 0, avg: 0.0, min: null, max: null };
  }

  const numeric = items.filter(
    (x): x is number => typeof x === "number" && !isNaN(x)
  );

  if (numeric.length === 0) {
    return {
      count: items.length,
      sum: 0,
      avg: 0.0,
      min: null,
      max: null,
    };
  }

  const sum = numeric.reduce((a, b) => a + b, 0);
  return {
    count: numeric.length,
    sum,
    avg: sum / numeric.length,
    min: Math.min(...numeric),
    max: Math.max(...numeric),
  };
}

export class IoWorker extends BaseWorker {
  async execute(job: Job): Promise<unknown> {
    const action = job.payload.action as string | undefined;

    if (action === "echo") {
      const delay = (job.payload.delay as number) ?? 0.1;
      const message = (job.payload.message as string) ?? "";
      await sleep(delay);
      return { echoed: message };
    } else if (action === "transform") {
      const data = (job.payload.data as Record<string, unknown>) ?? {};
      const operation = (job.payload.operation as string) ?? "identity";
      return transform(data, operation);
    } else if (action === "aggregate") {
      const items = (job.payload.items as unknown[]) ?? [];
      return aggregate(items);
    } else {
      throw new Error(`Unknown IO action: ${action}`);
    }
  }
}