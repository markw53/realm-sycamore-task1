/// <reference types="jest" />

import { QueueConfig } from "../config";

describe("QueueConfig", () => {
  test("creates with default values", () => {
    const cfg = new QueueConfig();
    expect(cfg.maxWorkers).toBe(4);
    expect(cfg.maxQueueSize).toBe(1000);
    expect(cfg.defaultPriority).toBe(5);
    expect(cfg.schedulingStrategy).toBe("priority");
    expect(cfg.storageBackend).toBe("memory");
    expect(cfg.storagePath).toBe("./task_store");
    expect(cfg.retryLimit).toBe(3);
    expect(cfg.timeoutSeconds).toBe(30.0);
    expect(cfg.logLevel).toBe("INFO");
  });

  test("accepts valid custom values", () => {
    const cfg = new QueueConfig({
      maxWorkers: 8,
      maxQueueSize: 500,
      defaultPriority: 3,
      schedulingStrategy: "round_robin",
      timeoutSeconds: 60.0,
    });
    expect(cfg.maxWorkers).toBe(8);
    expect(cfg.maxQueueSize).toBe(500);
    expect(cfg.schedulingStrategy).toBe("round_robin");
  });

  test("rejects maxWorkers < 1", () => {
    expect(() => new QueueConfig({ maxWorkers: 0 })).toThrow();
  });

  test("rejects maxQueueSize < 1", () => {
    expect(() => new QueueConfig({ maxQueueSize: 0 })).toThrow();
  });

  test("rejects defaultPriority out of 0-10 range", () => {
    expect(() => new QueueConfig({ defaultPriority: -1 })).toThrow();
    expect(() => new QueueConfig({ defaultPriority: 11 })).toThrow();
  });

  test("rejects retryLimit < 0", () => {
    expect(() => new QueueConfig({ retryLimit: -1 })).toThrow();
  });

  test("rejects timeoutSeconds <= 0", () => {
    expect(() => new QueueConfig({ timeoutSeconds: 0 })).toThrow();
    expect(() => new QueueConfig({ timeoutSeconds: -5 })).toThrow();
  });
});