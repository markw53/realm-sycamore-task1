/**
 * Input validation utilities.
 */

export function validatePayload(
  payload: unknown,
  requiredKeys: string[]
): string[] {
  const errors: string[] = [];
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    return ["Payload must be a dictionary"];
  }
  const dict = payload as Record<string, unknown>;
  for (const key of requiredKeys) {
    if (!(key in dict)) {
      errors.push(`Missing required key: ${key}`);
    }
  }
  return errors;
}

export function validatePriority(priority: number): boolean {
  return Number.isInteger(priority) && priority >= 0 && priority <= 10;
}

export function validateJobName(name: string): string[] {
  const errors: string[] = [];
  if (!name || typeof name !== "string") {
    errors.push("Job name must be a non-empty string");
  } else if (name.length > 256) {
    errors.push("Job name must be 256 characters or fewer");
  } else if (
    !name
      .replace(/_/g, "")
      .replace(/-/g, "")
      .replace(/\./g, "")
      .split("")
      .every((c) => /[a-zA-Z0-9]/.test(c))
  ) {
    errors.push(
      "Job name must contain only alphanumeric characters, hyphens, underscores, and dots"
    );
  }
  return errors;
}

export function sanitizeTags(tags: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const tag of tags) {
    const cleaned = tag.trim().toLowerCase();
    if (cleaned && !seen.has(cleaned)) {
      seen.add(cleaned);
      result.push(cleaned);
    }
  }
  return result;
}