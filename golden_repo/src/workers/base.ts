/**
 * Base worker interface.
 */

import { Job } from "../models/job";
import { JobResult } from "../models/result";
import { getLogger } from "../utils/logging";

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TimeoutError";
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number
): Promise<T> {
  let timer: NodeJS.Timeout;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(
      () => reject(new TimeoutError(`Timeout after ${timeoutMs / 1000}s`)),
      timeoutMs
    );
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

export abstract class BaseWorker {
  public workerId: string;
  public timeout: number;
  private _isBusy: boolean;
  private _jobsProcessed: number;
  private _totalExecutionTime: number;

  constructor(workerId: string, timeout: number = 30.0) {
    this.workerId = workerId;
    this.timeout = timeout;
    this._isBusy = false;
    this._jobsProcessed = 0;
    this._totalExecutionTime = 0.0;
  }

  abstract execute(job: Job): Promise<unknown>;

  async run(job: Job): Promise<JobResult> {
    this._isBusy = true;
    const start = Date.now() / 1000;
    const logger = getLogger();

    try {
      const timeoutSeconds = job.timeout || this.timeout;
      const result = await withTimeout(
        this.execute(job),
        timeoutSeconds * 1000
      );
      const elapsed = Date.now() / 1000 - start;
      this._jobsProcessed += 1;
      this._totalExecutionTime += elapsed;

      logger.info("job_completed", {
        worker: this.workerId,
        job_id: job.id,
        elapsed: Math.round(elapsed * 1000) / 1000,
      });

      return JobResult.ok(job.id, result, { worker: this.workerId });
    } catch (e) {
      const elapsed = Date.now() / 1000 - start;

      if (e instanceof TimeoutError) {
        logger.warning("job_timeout", {
          worker: this.workerId,
          job_id: job.id,
          timeout: job.timeout,
        });
        return JobResult.err(
          job.id,
          `Timeout after ${job.timeout}s`,
          { worker: this.workerId }
        );
      }

      const errorMessage = e instanceof Error ? e.message : String(e);
      logger.error("job_failed", {
        worker: this.workerId,
        job_id: job.id,
        error: errorMessage,
      });
      return JobResult.err(job.id, errorMessage, {
        worker: this.workerId,
      });
    } finally {
      this._isBusy = false;
    }
  }

  get isBusy(): boolean {
    return this._isBusy;
  }

  get stats(): Record<string, unknown> {
    const avg =
      this._jobsProcessed > 0
        ? this._totalExecutionTime / this._jobsProcessed
        : 0.0;
    return {
      workerId: this.workerId,
      jobsProcessed: this._jobsProcessed,
      totalExecutionTime:
        Math.round(this._totalExecutionTime * 1000) / 1000,
      averageExecutionTime: Math.round(avg * 1000) / 1000,
      isBusy: this._isBusy,
    };
  }
}