export interface LoggerContext {
    serviceName: string;
    tenantId?: string;
    traceId?: string;
    spanId?: string;
}
export declare class Logger {
    private context;
    constructor(context: LoggerContext);
    private format;
    info(message: string, meta?: Record<string, unknown>): void;
    error(message: string, meta?: Record<string, unknown>): void;
    warn(message: string, meta?: Record<string, unknown>): void;
    debug(message: string, meta?: Record<string, unknown>): void;
}
