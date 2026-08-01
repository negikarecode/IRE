"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RuleExecutionException = exports.TenantAccessDeniedException = exports.ValidationException = exports.NotFoundException = exports.DomainException = void 0;
class DomainException extends Error {
    details;
    constructor(message, details) {
        super(message);
        this.details = details;
        Object.setPrototypeOf(this, new.target.prototype);
    }
    toRFC7807(instancePath) {
        return {
            type: `https://ire.health/errors/${this.errorCode.toLowerCase()}`,
            title: this.name,
            status: this.statusCode,
            detail: this.message,
            errorCode: this.errorCode,
            instance: instancePath,
            invalidParams: this.details
        };
    }
}
exports.DomainException = DomainException;
class NotFoundException extends DomainException {
    statusCode = 404;
    errorCode = "RESOURCE_NOT_FOUND";
}
exports.NotFoundException = NotFoundException;
class ValidationException extends DomainException {
    statusCode = 400;
    errorCode = "VALIDATION_FAILED";
}
exports.ValidationException = ValidationException;
class TenantAccessDeniedException extends DomainException {
    statusCode = 403;
    errorCode = "TENANT_ACCESS_DENIED";
}
exports.TenantAccessDeniedException = TenantAccessDeniedException;
class RuleExecutionException extends DomainException {
    statusCode = 500;
    errorCode = "RULE_EXECUTION_ERROR";
}
exports.RuleExecutionException = RuleExecutionException;
//# sourceMappingURL=index.js.map