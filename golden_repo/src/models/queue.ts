/**
 * Priority queue implementation using a min-heap.
 */

import { Job } from "./job";

export class QueueFullError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "QueueFullError";
    Object.setPrototypeOf(this, QueueFullError.prototype);
  }
}

export class DuplicateJobError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DuplicateJobError";
    Object.setPrototypeOf(this, DuplicateJobError.prototype);
  }
}

interface HeapEntry {
  priority: number;
  counter: number;
  job: Job;
}

export class TaskQueue {
  private maxSize: number;
  private heap: HeapEntry[];
  private counter: number;
  private jobIndex: Map<string, Job>;

  constructor(maxSize: number = 1000) {
    this.maxSize = maxSize;
    this.heap = [];
    this.counter = 0;
    this.jobIndex = new Map();
  }

  push(job: Job): void {
    if (this.jobIndex.size >= this.maxSize) {
      throw new QueueFullError(`Queue is full (max size: ${this.maxSize})`);
    }
    if (this.jobIndex.has(job.id)) {
      throw new DuplicateJobError(`Job ${job.id} already in queue`);
    }
    const entry: HeapEntry = {
      priority: job.priority,
      counter: this.counter,
      job,
    };
    this.counter += 1;
    this.heap.push(entry);
    this.siftUp(this.heap.length - 1);
    this.jobIndex.set(job.id, job);
  }

  pop(): Job | null {
    while (this.heap.length > 0) {
      const entry = this.heapPop();
      if (entry && this.jobIndex.has(entry.job.id)) {
        this.jobIndex.delete(entry.job.id);
        return entry.job;
      }
    }
    return null;
  }

  peek(): Job | null {
    for (const entry of this.heap) {
      if (this.jobIndex.has(entry.job.id)) {
        return entry.job;
      }
    }
    return null;
  }

  remove(jobId: string): boolean {
    if (this.jobIndex.has(jobId)) {
      this.jobIndex.delete(jobId);
      return true;
    }
    return false;
  }

  getJob(jobId: string): Job | null {
    return this.jobIndex.get(jobId) ?? null;
  }

  get size(): number {
    return this.jobIndex.size;
  }

  get isEmpty(): boolean {
    return this.jobIndex.size === 0;
  }

  get isFull(): boolean {
    return this.jobIndex.size >= this.maxSize;
  }

  getAllJobs(): Job[] {
    return Array.from(this.jobIndex.values());
  }

  clear(): number {
    const count = this.jobIndex.size;
    this.heap = [];
    this.jobIndex.clear();
    this.counter = 0;
    return count;
  }

  // --- Min-heap operations ---

  private compare(a: HeapEntry, b: HeapEntry): number {
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return a.counter - b.counter;
  }

  private siftUp(i: number): void {
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (this.compare(this.heap[i], this.heap[parent]) < 0) {
        [this.heap[i], this.heap[parent]] = [this.heap[parent], this.heap[i]];
        i = parent;
      } else {
        break;
      }
    }
  }

  private siftDown(i: number): void {
    const n = this.heap.length;
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;

      if (left < n && this.compare(this.heap[left], this.heap[smallest]) < 0) {
        smallest = left;
      }
      if (
        right < n &&
        this.compare(this.heap[right], this.heap[smallest]) < 0
      ) {
        smallest = right;
      }

      if (smallest !== i) {
        [this.heap[i], this.heap[smallest]] = [
          this.heap[smallest],
          this.heap[i],
        ];
        i = smallest;
      } else {
        break;
      }
    }
  }

  private heapPop(): HeapEntry | undefined {
    if (this.heap.length === 0) return undefined;
    if (this.heap.length === 1) return this.heap.pop();

    const top = this.heap[0];
    this.heap[0] = this.heap.pop()!;
    this.siftDown(0);
    return top;
  }
}