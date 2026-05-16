/**
 * Serialization utilities for jobs and results.
 */

import { Job } from "../models/job";
import { JobResult } from "../models/result";

export function serializeJob(job: Job): string {
  return JSON.stringify(job.toDict());
}

export function deserializeJob(data: string): Job {
  return Job.fromDict(JSON.parse(data));
}

export function serializeResult(result: JobResult): string {
  return JSON.stringify(result.toDict());
}

export function deserializeResult(data: string): JobResult {
  return JobResult.fromDict(JSON.parse(data));
}

export function serializeManyJobs(jobs: Job[]): string {
  return JSON.stringify(jobs.map((j) => j.toDict()));
}

export function deserializeManyJobs(data: string): Job[] {
  const arr = JSON.parse(data) as Record<string, unknown>[];
  return arr.map((d) => Job.fromDict(d));
}