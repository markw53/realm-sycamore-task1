/**
 * Job model definitions.
 */

import * as crypto from "crypto";

export enum JobStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  RETRYING = "retrying",
}

export enum JobPriority {
  CRITICAL = 0,
  HIGH = 1,
  MEDIUM = 5,
  LOW = 8,
  BACKGROUND = 10,
}

export class InvalidJobStateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidJobStateError";
    Object.setPrototypeOf(this, InvalidJobStateError.prototype);
  }
}

export interface JobOptions {
  priority: number;
  id: string;
  status: JobStatus;
  createdAt: number;
  startedAt: number | null;
  completedAt: number | null;
  result: unknown;
  error: string | null;
  retryCount: number;
  maxRetries: number;
  timeout: number;
  tags: string[];
}

export class Job {
  public name: string;
  public payload: Record<string, unknown>;
  public priority: number;
  public id: string;
  public status: JobStatus;
  public createdAt: number;
  public startedAt: number | null;
  public completedAt: number | null;
  public result: unknown;
  public error: string | null;
  public retryCount: number;
  public maxRetries: number;
  public timeout: number;
  public tags: string[];

  constructor(
    name: string,
    payload: Record<string, unknown>,
    options: Partial<JobOptions> = {}
  ) {
    this.name = name;
    this.payload = payload;
    this.priority = options.priority ?? JobPriority.MEDIUM;
    this.id = options.id ?? crypto.randomUUID();
    this.status = options.status ?? JobStatus.PENDING;
    this.createdAt = options.createdAt ?? Date.now() / 1000;
    this.startedAt = options.startedAt ?? null;
    this.completedAt = options.completedAt ?? null;
    this.result = options.result ?? null;
    this.error = options.error ?? null;
    this.retryCount = options.retryCount ?? 0;
    this.maxRetries = options.maxRetries ?? 3;
    this.timeout = options.timeout ?? 30.0;
    this.tags = options.tags ?? [];
  }

  start(): void {
    if (
      this.status !== JobStatus.PENDING &&
      this.status !== JobStatus.RETRYING
    ) {
      throw new InvalidJobStateError(
        `Cannot start job in state ${this.status}`
      );
    }
    this.status = JobStatus.RUNNING;
    this.startedAt = Date.now() / 1000;
  }

  complete(result: unknown = null): void {
    if (this.status !== JobStatus.RUNNING) {
      throw new InvalidJobStateError(
        `Cannot complete job in state ${this.status}`
      );
    }
    this.status = JobStatus.COMPLETED;
    this.result = result;
    this.completedAt = Date.now() / 1000;
  }

  fail(error: string): void {
    if (this.status !== JobStatus.RUNNING) {
      throw new InvalidJobStateError(
        `Cannot fail job in state ${this.status}`
      );
    }
    this.error = error;
    if (this.retryCount < this.maxRetries) {
      this.status = JobStatus.RETRYING;
      this.retryCount += 1;
    } else {
      this.status = JobStatus.FAILED;
      this.completedAt = Date.now() / 1000;
    }
  }

  cancel(): void {
    if (
      this.status === JobStatus.COMPLETED ||
      this.status === JobStatus.FAILED
    ) {
      throw new InvalidJobStateError(
        `Cannot cancel job in state ${this.status}`
      );
    }
    this.status = JobStatus.CANCELLED;
    this.completedAt = Date.now() / 1000;
  }

  get duration(): number | null {
    if (this.startedAt === null) {
      return null;
    }
    const end = this.completedAt ?? Date.now() / 1000;
    return end - this.startedAt;
  }

  get isTerminal(): boolean {
    return (
      this.status === JobStatus.COMPLETED ||
      this.status === JobStatus.FAILED ||
      this.status === JobStatus.CANCELLED
    );
  }

  toDict(): Record<string, unknown> {
    return {
      id: this.id,
      name: this.name,
      payload: this.payload,
      priority: this.priority,
      status: this.status,
      createdAt: this.createdAt,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
      result: this.result,
      error: this.error,
      retryCount: this.retryCount,
      maxRetries: this.maxRetries,
      timeout: this.timeout,
      tags: this.tags,
    };
  }

  static fromDict(data: Record<string, unknown>): Job {
    return new Job(data.name as string, data.payload as Record<string, unknown>, {
      priority: data.priority as number,
      id: data.id as string,
      status: data.status as JobStatus,
      createdAt: data.createdAt as number,
      startedAt: data.startedAt as number | null,
      completedAt: data.completedAt as number | null,
      result: data.result,
      error: data.error as string | null,
      retryCount: data.retryCount as number,
      maxRetries: data.maxRetries as number,
      timeout: data.timeout as number,
      tags: data.tags as string[],
    });
  }
}