/**
 * Structured logging configuration.
 */

export interface Logger {
  info(event: string, context?: Record<string, unknown>): void;
  warning(event: string, context?: Record<string, unknown>): void;
  error(event: string, context?: Record<string, unknown>): void;
}

class StructuredLogger implements Logger {
  private format(
    level: string,
    event: string,
    context: Record<string, unknown> = {}
  ): string {
    const entry: Record<string, unknown> = {
      timestamp: new Date().toISOString(),
      level,
      event,
      ...context,
    };
    return JSON.stringify(entry);
  }

  info(event: string, context: Record<string, unknown> = {}): void {
    console.log(this.format("info", event, context));
  }

  warning(event: string, context: Record<string, unknown> = {}): void {
    console.warn(this.format("warning", event, context));
  }

  error(event: string, context: Record<string, unknown> = {}): void {
    console.error(this.format("error", event, context));
  }
}

let logger: Logger = new StructuredLogger();

export function configureLogging(_level: string = "INFO"): void {
  // Level filtering could be added here if needed.
  // For now, the structured logger always emits.
  logger = new StructuredLogger();
}

export function getLogger(): Logger {
  return logger;
}