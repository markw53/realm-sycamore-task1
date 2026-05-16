/**
 * Abstract storage backend interface.
 */

export abstract class StorageBackend {
  abstract save(key: string, data: Record<string, unknown>): Promise<void>;
  abstract load(key: string): Promise<Record<string, unknown> | null>;
  abstract delete(key: string): Promise<boolean>;
  abstract exists(key: string): Promise<boolean>;
  abstract listKeys(prefix?: string): Promise<string[]>;
}