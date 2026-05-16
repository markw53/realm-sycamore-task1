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
    process.stderr.write(this.format("info", event, context) + "\n");
  }

  warning(event: string, context: Record<string, unknown> = {}): void {
    process.stderr.write(this.format("warning", event, context) + "\n");
  }

  error(event: string, context: Record<string, unknown> = {}): void {
    process.stderr.write(this.format("error", event, context) + "\n");
  }
}

let logger: Logger = new StructuredLogger();

export function configureLogging(_level: string = "INFO"): void {
  logger = new StructuredLogger();
}

export function getLogger(): Logger {
  return logger;
}