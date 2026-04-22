/**
 * Round-robin scheduling strategy.
 */

import { Job } from "../models/job";
import { TaskQueue } from "../models/queue";

export class RoundRobinScheduler {
  private _name = "round_robin";

  get name(): string {
    return this._name;
  }

  nextJob(queue: TaskQueue): Job | null {
    return queue.pop();
  }

  shouldPreempt(_current: Job, _incoming: Job): boolean {
    return false;
  }
}