/**
 * Core Domain-Driven Design (DDD) Base Constructs
 * Defines the foundation for Entities, Value Objects, Aggregate Roots, Domain Events, and Repositories.
 */
export declare abstract class Entity<TIdentifier> {
    readonly id: TIdentifier;
    constructor(id: TIdentifier);
    equals(other?: Entity<TIdentifier>): boolean;
}
export declare abstract class ValueObject<TProps> {
    protected readonly props: TProps;
    constructor(props: TProps);
    equals(vo?: ValueObject<TProps>): boolean;
}
export interface IDomainEvent {
    eventId: string;
    occurredOn: Date;
    tenantId: string;
    aggregateId: string;
    eventType: string;
    payload: Record<string, unknown>;
}
export declare abstract class AggregateRoot<TIdentifier> extends Entity<TIdentifier> {
    private _domainEvents;
    get domainEvents(): ReadonlyArray<IDomainEvent>;
    addDomainEvent(event: IDomainEvent): void;
    clearEvents(): void;
}
export interface IRepository<T extends AggregateRoot<TIdentifier>, TIdentifier> {
    findById(id: TIdentifier, tenantId: string): Promise<T | null>;
    save(aggregate: T, tenantId: string): Promise<void>;
    delete(id: TIdentifier, tenantId: string): Promise<void>;
}
export declare class TenantId extends ValueObject<{
    value: string;
}> {
    get value(): string;
    static create(id: string): TenantId;
}
export declare class ClaimId extends ValueObject<{
    value: string;
}> {
    get value(): string;
    static create(id: string): ClaimId;
}
