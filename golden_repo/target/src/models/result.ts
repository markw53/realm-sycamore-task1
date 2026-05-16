/**
 * Result container for job execution outcomes.
 */

export class JobResult {
  public jobId: string;
  public success: boolean;
  public value: unknown;
  public error: string | null;
  public executionTime: number;
  public timestamp: number;
  public metadata: Record<string, unknown>;

  constructor(
    jobId: string,
    success: boolean,
    options: {
      value?: unknown;
      error?: string | null;
      executionTime?: number;
      timestamp?: number;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    this.jobId = jobId;
    this.success = success;
    this.value = options.value ?? null;
    this.error = options.error ?? null;
    this.executionTime = options.executionTime ?? 0.0;
    this.timestamp = options.timestamp ?? Date.now() / 1000;
    this.metadata = options.metadata ?? {};
  }

  get isError(): boolean {
    return !this.success;
  }

  toDict(): Record<string, unknown> {
    return {
      jobId: this.jobId,
      success: this.success,
      value: this.value,
      error: this.error,
      executionTime: this.executionTime,
      timestamp: this.timestamp,
      metadata: this.metadata,
    };
  }

  static fromDict(data: Record<string, unknown>): JobResult {
    return new JobResult(data.jobId as string, data.success as boolean, {
      value: data.value,
      error: data.error as string | null,
      executionTime: data.executionTime as number,
      timestamp: data.timestamp as number,
      metadata: data.metadata as Record<string, unknown>,
    });
  }

  static ok(
    jobId: string,
    value: unknown = null,
    metadata: Record<string, unknown> = {}
  ): JobResult {
    return new JobResult(jobId, true, { value, metadata });
  }

  static err(
    jobId: string,
    error: string,
    metadata: Record<string, unknown> = {}
  ): JobResult {
    return new JobResult(jobId, false, { error, metadata });
  }
}