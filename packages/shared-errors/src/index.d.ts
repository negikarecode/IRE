export declare abstract class DomainException extends Error {
    readonly details?: Record<string, unknown> | undefined;
    abstract readonly statusCode: number;
    abstract readonly errorCode: string;
    constructor(message: string, details?: Record<string, unknown> | undefined);
    toRFC7807(instancePath: string): Record<string, unknown>;
}
export declare class NotFoundException extends DomainException {
    readonly statusCode = 404;
    readonly errorCode = "RESOURCE_NOT_FOUND";
}
export declare class ValidationException extends DomainException {
    readonly statusCode = 400;
    readonly errorCode = "VALIDATION_FAILED";
}
export declare class TenantAccessDeniedException extends DomainException {
    readonly statusCode = 403;
    readonly errorCode = "TENANT_ACCESS_DENIED";
}
export declare class RuleExecutionException extends DomainException {
    readonly statusCode = 500;
    readonly errorCode = "RULE_EXECUTION_ERROR";
}
