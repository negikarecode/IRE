"use strict";
/**
 * Core Domain-Driven Design (DDD) Base Constructs
 * Defines the foundation for Entities, Value Objects, Aggregate Roots, Domain Events, and Repositories.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClaimId = exports.TenantId = exports.AggregateRoot = exports.ValueObject = exports.Entity = void 0;
class Entity {
    id;
    constructor(id) {
        this.id = id;
    }
    equals(other) {
        if (other === null || other === undefined)
            return false;
        if (this === other)
            return true;
        return this.id === other.id;
    }
}
exports.Entity = Entity;
class ValueObject {
    props;
    constructor(props) {
        this.props = Object.freeze(props);
    }
    equals(vo) {
        if (vo === null || vo === undefined || vo.props === undefined) {
            return false;
        }
        return JSON.stringify(this.props) === JSON.stringify(vo.props);
    }
}
exports.ValueObject = ValueObject;
class AggregateRoot extends Entity {
    _domainEvents = [];
    get domainEvents() {
        return this._domainEvents;
    }
    addDomainEvent(event) {
        this._domainEvents.push(event);
    }
    clearEvents() {
        this._domainEvents = [];
    }
}
exports.AggregateRoot = AggregateRoot;
class TenantId extends ValueObject {
    get value() {
        return this.props.value;
    }
    static create(id) {
        if (!id || id.trim().length === 0) {
            throw new Error("TenantId cannot be empty");
        }
        return new TenantId({ value: id });
    }
}
exports.TenantId = TenantId;
class ClaimId extends ValueObject {
    get value() {
        return this.props.value;
    }
    static create(id) {
        if (!id || id.trim().length === 0) {
            throw new Error("ClaimId cannot be empty");
        }
        return new ClaimId({ value: id });
    }
}
exports.ClaimId = ClaimId;
//# sourceMappingURL=index.js.map