export declare class ApiGatewayRouter {
    routeRequest(path: string, headers: Record<string, string>): {
        serviceTarget: string;
        tenantId: string;
    };
}
