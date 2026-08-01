"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TenantContextHolder = void 0;
const async_hooks_1 = require("async_hooks");
const tenantStorage = new async_hooks_1.AsyncLocalStorage();
class TenantContextHolder {
    static run(context, fn) {
        return tenantStorage.run(context, fn);
    }
    static getContext() {
        const ctx = tenantStorage.getStore();
        if (!ctx) {
            throw new Error("TenantContext missing! Request executed outside tenant context boundary.");
        }
        return ctx;
    }
    static getTenantId() {
        return TenantContextHolder.getContext().tenantId;
    }
}
exports.TenantContextHolder = TenantContextHolder;
//# sourceMappingURL=index.js.map