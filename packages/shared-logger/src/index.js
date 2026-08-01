"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Logger = void 0;
class Logger {
    context;
    constructor(context) {
        this.context = context;
    }
    format(level, message, meta) {
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
    info(message, meta) {
        console.log(this.format("INFO", message, meta));
    }
    error(message, meta) {
        console.error(this.format("ERROR", message, meta));
    }
    warn(message, meta) {
        console.warn(this.format("WARN", message, meta));
    }
    debug(message, meta) {
        console.debug(this.format("DEBUG", message, meta));
    }
}
exports.Logger = Logger;
//# sourceMappingURL=index.js.map