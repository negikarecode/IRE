export abstract class DomainException extends Error {
  public abstract readonly statusCode: number;
  public abstract readonly errorCode: string;

  constructor(message: string, public readonly details?: Record<string, unknown>) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);
  }

  public toRFC7807(instancePath: string): Record<string, unknown> {
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

export class NotFoundException extends DomainException {
  public readonly statusCode = 404;
  public readonly errorCode = "RESOURCE_NOT_FOUND";
}

export class ValidationException extends DomainException {
  public readonly statusCode = 400;
  public readonly errorCode = "VALIDATION_FAILED";
}

export class TenantAccessDeniedException extends DomainException {
  public readonly statusCode = 403;
  public readonly errorCode = "TENANT_ACCESS_DENIED";
}

export class RuleExecutionException extends DomainException {
  public readonly statusCode = 500;
  public readonly errorCode = "RULE_EXECUTION_ERROR";
}
