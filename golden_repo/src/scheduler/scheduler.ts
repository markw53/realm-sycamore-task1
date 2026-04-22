/**
 * Main scheduler orchestrator.
 */

import { QueueConfig } from "../config";
import { Job, JobStatus } from "../models/job";
import { TaskQueue } from "../models/queue";
import { JobResult } from "../models/result";
import { PriorityScheduler } from "./priority";
import { RoundRobinScheduler } from "./round_robin";
import { BaseWorker } from "../workers/base";
import { CpuWorker } from "../workers/cpu_worker";
import { IoWorker } from "../workers/io_worker";
import { getLogger } from "../utils/logging";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class Scheduler {
  public config: QueueConfig;
  public queue: TaskQueue;
  private _results: Map<string, JobResult>;
  private _running: boolean;
  private _strategy: PriorityScheduler | RoundRobinScheduler;
  private _workers: BaseWorker[];

  constructor(config: QueueConfig) {
    this.config = config;
    this.queue = new TaskQueue(config.maxQueueSize);
    this._results = new Map();
    this._running = false;

    if (config.schedulingStrategy === "priority") {
      this._strategy = new PriorityScheduler();
    } else {
      this._strategy = new RoundRobinScheduler();
    }

    this._workers = [];
    for (let i = 0; i < config.maxWorkers; i++) {
      if (i % 2 === 0) {
        this._workers.push(new CpuWorker(`cpu-${i}`, config.timeoutSeconds));
      } else {
        this._workers.push(new IoWorker(`io-${i}`, config.timeoutSeconds));
      }
    }
  }

  submit(job: Job): string {
    if (job.priority < 0 || job.priority > 10) {
      throw new Error(`Priority must be 0-10, got ${job.priority}`);
    }
    this.queue.push(job);
    const logger = getLogger();
    logger.info("job_submitted", {
      job_id: job.id,
      name: job.name,
      priority: job.priority,
    });
    return job.id;
  }

  async processNext(): Promise<JobResult | null> {
    const worker = this.getAvailableWorker();
    if (worker === null) return null;

    const job = this._strategy.nextJob(this.queue);
    if (job === null) return null;

    job.start();
    const result = await worker.run(job);

    if (result.success) {
      job.complete(result.value);
    } else {
      job.fail(result.error || "Unknown error");
      if (job.status === JobStatus.RETRYING) {
        const logger = getLogger();
        logger.info("job_retrying", {
          job_id: job.id,
          attempt: job.retryCount,
        });
        this.queue.push(job);
        return result;
      }
    }

    this._results.set(job.id, result);
    return result;
  }

  async runAll(): Promise<JobResult[]> {
    const results: JobResult[] = [];
    this._running = true;
    while (!this.queue.isEmpty && this._running) {
      const result = await this.processNext();
      if (result) {
        results.push(result);
      } else {
        await sleep(10);
      }
    }
    this._running = false;
    return results;
  }

  stop(): void {
    this._running = false;
  }

  getResult(jobId: string): JobResult | null {
    return this._results.get(jobId) ?? null;
  }

  getAllResults(): JobResult[] {
    return Array.from(this._results.values());
  }

  getStats(): Record<string, unknown> {
    return {
      queueSize: this.queue.size,
      totalResults: this._results.size,
      successful: Array.from(this._results.values()).filter((r) => r.success)
        .length,
      failed: Array.from(this._results.values()).filter((r) => !r.success)
        .length,
      strategy: this._strategy.name,
      workers: this._workers.map((w) => w.stats),
    };
  }

  private getAvailableWorker(): BaseWorker | null {
    for (const worker of this._workers) {
      if (!worker.isBusy) return worker;
    }
    return null;
  }
}