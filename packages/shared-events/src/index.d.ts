export interface CloudEvent<TData = Record<string, unknown>> {
    specversion: "1.0";
    id: string;
    source: string;
    type: string;
    subject: string;
    time: string;
    datacontenttype: "application/json";
    tenantid: string;
    correlationid: string;
    data: TData;
}
export interface IEventPublisher {
    publish<T>(event: CloudEvent<T>): Promise<void>;
    publishBatch<T>(events: CloudEvent<T>[]): Promise<void>;
}
export interface IEventSubscriber {
    subscribe<T>(eventType: string, handler: (event: CloudEvent<T>) => Promise<void>): Promise<void>;
}
export interface OutboxRecord {
    id: string;
    aggregateType: string;
    aggregateId: string;
    tenantId: string;
    eventType: string;
    payload: string;
    createdAt: Date;
    processedAt?: Date;
    status: "PENDING" | "PUBLISHED" | "FAILED";
}
export interface IOutboxRepository {
    save(record: OutboxRecord): Promise<void>;
    fetchPending(batchSize: number): Promise<OutboxRecord[]>;
    markAsPublished(id: string): Promise<void>;
}
