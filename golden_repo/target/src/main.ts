/**
 * Entry point for the task queue system.
 */

import { QueueConfig } from "./config";
import { Job, JobPriority } from "./models/job";
import { Scheduler } from "./scheduler/scheduler";
import { configureLogging, getLogger } from "./utils/logging";

async function main(): Promise<void> {
  configureLogging("INFO");
  const logger = getLogger();

  const config = new QueueConfig({
    maxWorkers: 4,
    maxQueueSize: 100,
    schedulingStrategy: "priority",
    storageBackend: "memory",
  });

  const scheduler = new Scheduler(config);

  const jobs = [
    new Job("factorial-job", { action: "factorial", n: 20 }, {
      priority: JobPriority.HIGH,
    }),
    new Job("echo-job", { action: "echo", message: "hello", delay: 0.1 }, {
      priority: JobPriority.LOW,
    }),
    new Job("fibonacci-job", { action: "fibonacci", n: 30 }, {
      priority: JobPriority.MEDIUM,
    }),
    new Job("prime-check", { action: "prime_check", n: 97 }, {
      priority: JobPriority.CRITICAL,
    }),
    new Job(
      "transform-job",
      { action: "transform", data: { name: "test" }, operation: "uppercase" },
      { priority: JobPriority.MEDIUM }
    ),
    new Job("aggregate-job", { action: "aggregate", items: [1, 2, 3, 4, 5] }, {
      priority: JobPriority.BACKGROUND,
    }),
  ];

  for (const job of jobs) {
    scheduler.submit(job);
  }

  logger.info("starting_scheduler", { queue_size: scheduler.queue.size });
  const results = await scheduler.runAll();

  for (const result of results) {
    const status = result.success ? "✓" : "✗";
    logger.info("result", {
      status,
      job_id: result.jobId.substring(0, 8),
      value: result.value,
      error: result.error,
    });
  }

  const stats = scheduler.getStats();
  logger.info("final_stats", stats);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});