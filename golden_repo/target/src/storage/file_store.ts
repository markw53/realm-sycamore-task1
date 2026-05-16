/**
 * File-based storage backend.
 */

import * as fs from "fs/promises";
import * as fsSync from "fs";
import * as path from "path";
import { StorageBackend } from "./backend";

export class FileStorage extends StorageBackend {
  private basePath: string;

  constructor(basePath: string = "./task_store") {
    super();
    this.basePath = basePath;
    fsSync.mkdirSync(basePath, { recursive: true });
  }

  private keyToPath(key: string): string {
    const safeKey = key.replace(/\//g, "_").replace(/\\/g, "_");
    return path.join(this.basePath, `${safeKey}.json`);
  }

  async save(key: string, data: Record<string, unknown>): Promise<void> {
    const filePath = this.keyToPath(key);
    await fs.writeFile(filePath, JSON.stringify(data), "utf-8");
  }

  async load(key: string): Promise<Record<string, unknown> | null> {
    const filePath = this.keyToPath(key);
    try {
      await fs.access(filePath);
    } catch {
      return null;
    }
    const content = await fs.readFile(filePath, "utf-8");
    return JSON.parse(content);
  }

  async delete(key: string): Promise<boolean> {
    const filePath = this.keyToPath(key);
    try {
      await fs.access(filePath);
      await fs.unlink(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async exists(key: string): Promise<boolean> {
    const filePath = this.keyToPath(key);
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async listKeys(prefix: string = ""): Promise<string[]> {
    const keys: string[] = [];
    let files: string[];
    try {
      files = await fs.readdir(this.basePath);
    } catch {
      return [];
    }
    files.sort();
    for (const fname of files) {
      if (fname.endsWith(".json")) {
        const key = fname.slice(0, -5);
        if (key.startsWith(prefix)) {
          keys.push(key);
        }
      }
    }
    return keys;
  }
}