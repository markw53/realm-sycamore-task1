/**
 * Priority-based scheduling strategy.
 */

import { Job } from "../models/job";
import { TaskQueue } from "../models/queue";

export class PriorityScheduler {
  private _name = "priority";

  get name(): string {
    return this._name;
  }

  nextJob(queue: TaskQueue): Job | null {
    return queue.pop();
  }

  shouldPreempt(current: Job, incoming: Job): boolean {
    return incoming.priority < current.priority;
  }
}