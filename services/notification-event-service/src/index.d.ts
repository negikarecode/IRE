import { CloudEvent } from "@ire/shared-events";
export declare class WebhookDispatcher {
    dispatch(webhookUrl: string, event: CloudEvent): Promise<void>;
}
