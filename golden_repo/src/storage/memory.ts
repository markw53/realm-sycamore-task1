/**
 * In-memory storage backend.
 */

import { StorageBackend } from "./backend";

export class MemoryStorage extends StorageBackend {
  private store: Map<string, Record<string, unknown>>;

  constructor() {
    super();
    this.store = new Map();
  }

  async save(key: string, data: Record<string, unknown>): Promise<void> {
    this.store.set(key, JSON.parse(JSON.stringify(data)));
  }

  async load(key: string): Promise<Record<string, unknown> | null> {
    const val = this.store.get(key);
    if (val === undefined) return null;
    return JSON.parse(JSON.stringify(val));
  }

  async delete(key: string): Promise<boolean> {
    if (this.store.has(key)) {
      this.store.delete(key);
      return true;
    }
    return false;
  }

  async exists(key: string): Promise<boolean> {
    return this.store.has(key);
  }

  async listKeys(prefix: string = ""): Promise<string[]> {
    const keys: string[] = [];
    for (const k of this.store.keys()) {
      if (k.startsWith(prefix)) {
        keys.push(k);
      }
    }
    return keys.sort();
  }
}