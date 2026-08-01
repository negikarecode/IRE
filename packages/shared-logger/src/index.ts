export interface LoggerContext {
  serviceName: string;
  tenantId?: string;
  traceId?: string;
  spanId?: string;
}

export class Logger {
  constructor(private context: LoggerContext) {}

  private format(level: string, message: string, meta?: Record<string, unknown>): string {
    return JSON.stringify({
      timestamp: new Date().toISOString(),
      level,
      service: this.context.serviceName,
      tenantId: this.context.tenantId || "N/A",
      traceId: this.context.traceId || "N/A",
      message,
      ...meta
    });
  }

  public info(message: string, meta?: Record<string, unknown>): void {
    console.log(this.format("INFO", message, meta));
  }

  public error(message: string, meta?: Record<string, unknown>): void {
    console.error(this.format("ERROR", message, meta));
  }

  public warn(message: string, meta?: Record<string, unknown>): void {
    console.warn(this.format("WARN", message, meta));
  }

  public debug(message: string, meta?: Record<string, unknown>): void {
    console.debug(this.format("DEBUG", message, meta));
  }
}
