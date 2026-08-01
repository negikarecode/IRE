/**
 * Core Domain-Driven Design (DDD) Base Constructs
 * Defines the foundation for Entities, Value Objects, Aggregate Roots, Domain Events, and Repositories.
 */

export abstract class Entity<TIdentifier> {
  constructor(public readonly id: TIdentifier) {}

  public equals(other?: Entity<TIdentifier>): boolean {
    if (other === null || other === undefined) return false;
    if (this === other) return true;
    return this.id === other.id;
  }
}

export abstract class ValueObject<TProps> {
  protected readonly props: TProps;

  constructor(props: TProps) {
    this.props = Object.freeze(props);
  }

  public equals(vo?: ValueObject<TProps>): boolean {
    if (vo === null || vo === undefined || vo.props === undefined) {
      return false;
    }
    return JSON.stringify(this.props) === JSON.stringify(vo.props);
  }
}

export interface IDomainEvent {
  eventId: string;
  occurredOn: Date;
  tenantId: string;
  aggregateId: string;
  eventType: string;
  payload: Record<string, unknown>;
}

export abstract class AggregateRoot<TIdentifier> extends Entity<TIdentifier> {
  private _domainEvents: IDomainEvent[] = [];

  get domainEvents(): ReadonlyArray<IDomainEvent> {
    return this._domainEvents;
  }

  public addDomainEvent(event: IDomainEvent): void {
    this._domainEvents.push(event);
  }

  public clearEvents(): void {
    this._domainEvents = [];
  }
}

export interface IRepository<T extends AggregateRoot<TIdentifier>, TIdentifier> {
  findById(id: TIdentifier, tenantId: string): Promise<T | null>;
  save(aggregate: T, tenantId: string): Promise<void>;
  delete(id: TIdentifier, tenantId: string): Promise<void>;
}

export class TenantId extends ValueObject<{ value: string }> {
  get value(): string {
    return this.props.value;
  }

  public static create(id: string): TenantId {
    if (!id || id.trim().length === 0) {
      throw new Error("TenantId cannot be empty");
    }
    return new TenantId({ value: id });
  }
}

export class ClaimId extends ValueObject<{ value: string }> {
  get value(): string {
    return this.props.value;
  }

  public static create(id: string): ClaimId {
    if (!id || id.trim().length === 0) {
      throw new Error("ClaimId cannot be empty");
    }
    return new ClaimId({ value: id });
  }
}
