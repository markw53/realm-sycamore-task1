/**
 * Configuration management for the task queue.
 */

export interface QueueConfigOptions {
  maxWorkers: number;
  maxQueueSize: number;
  defaultPriority: number;
  schedulingStrategy: "priority" | "round_robin";
  storageBackend: "memory" | "file";
  storagePath: string;
  retryLimit: number;
  timeoutSeconds: number;
  logLevel: string;
}

export class QueueConfig {
  public readonly maxWorkers: number;
  public readonly maxQueueSize: number;
  public readonly defaultPriority: number;
  public readonly schedulingStrategy: "priority" | "round_robin";
  public readonly storageBackend: "memory" | "file";
  public readonly storagePath: string;
  public readonly retryLimit: number;
  public readonly timeoutSeconds: number;
  public readonly logLevel: string;

  constructor(options: Partial<QueueConfigOptions> = {}) {
    this.maxWorkers = options.maxWorkers ?? 4;
    this.maxQueueSize = options.maxQueueSize ?? 1000;
    this.defaultPriority = options.defaultPriority ?? 5;
    this.schedulingStrategy = options.schedulingStrategy ?? "priority";
    this.storageBackend = options.storageBackend ?? "memory";
    this.storagePath = options.storagePath ?? "./task_store";
    this.retryLimit = options.retryLimit ?? 3;
    this.timeoutSeconds = options.timeoutSeconds ?? 30.0;
    this.logLevel = options.logLevel ?? "INFO";

    if (this.maxWorkers < 1) {
      throw new Error("maxWorkers must be >= 1");
    }
    if (this.maxQueueSize < 1) {
      throw new Error("maxQueueSize must be >= 1");
    }
    if (this.defaultPriority < 0 || this.defaultPriority > 10) {
      throw new Error("defaultPriority must be between 0 and 10");
    }
    if (this.retryLimit < 0) {
      throw new Error("retryLimit must be >= 0");
    }
    if (this.timeoutSeconds <= 0) {
      throw new Error("timeoutSeconds must be > 0");
    }
  }
}