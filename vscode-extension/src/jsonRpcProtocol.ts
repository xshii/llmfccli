/**
 * Pure JSON-RPC 2.0 Protocol Handler
 *
 * This module handles JSON-RPC protocol logic without any VSCode dependencies.
 * It can be tested independently in Node.js environment.
 */

// JSON-RPC 2.0 Types
export interface JsonRpcRequest {
    jsonrpc: '2.0';
    id: number | string;
    method: string;
    params?: any;
}

export interface JsonRpcSuccessResponse {
    jsonrpc: '2.0';
    id: number | string;
    result: any;
}

export interface JsonRpcErrorResponse {
    jsonrpc: '2.0';
    id: number | string;
    error: {
        code: number;
        message: string;
        data?: any;
    };
}

export type JsonRpcResponse = JsonRpcSuccessResponse | JsonRpcErrorResponse;

// Standard JSON-RPC 2.0 Error Codes
export const JSON_RPC_ERRORS = {
    PARSE_ERROR: -32700,
    INVALID_REQUEST: -32600,
    METHOD_NOT_FOUND: -32601,
    INVALID_PARAMS: -32602,
    INTERNAL_ERROR: -32603,
} as const;

// Handler type
export type MethodHandler = (params: any) => Promise<any>;

/**
 * Pure JSON-RPC 2.0 Protocol Handler
 *
 * Handles:
 * - Request validation
 * - Response formatting
 * - Error handling
 * - Method routing
 *
 * Does NOT handle:
 * - VSCode API calls (delegated to handlers)
 * - Transport layer (stdin/stdout, HTTP, etc.)
 */
export class JsonRpcProtocol {
    private handlers: Map<string, MethodHandler> = new Map();

    /**
     * Register a method handler
     */
    registerMethod(method: string, handler: MethodHandler): void {
        this.handlers.set(method, handler);
    }

    /**
     * Unregister a method handler
     */
    unregisterMethod(method: string): boolean {
        return this.handlers.delete(method);
    }

    /**
     * Get all registered method names
     */
    getRegisteredMethods(): string[] {
        return Array.from(this.handlers.keys());
    }

    /**
     * Check if a method is registered
     */
    hasMethod(method: string): boolean {
        return this.handlers.has(method);
    }

    /**
     * Validate JSON-RPC request format
     */
    validateRequest(request: any): { valid: boolean; error?: string } {
        if (typeof request !== 'object' || request === null) {
            return { valid: false, error: 'Request must be an object' };
        }

        if (request.jsonrpc !== '2.0') {
            return { valid: false, error: 'Invalid JSON-RPC version, must be "2.0"' };
        }

        if (request.id === undefined || request.id === null) {
            return { valid: false, error: 'Request must have an id' };
        }

        if (typeof request.method !== 'string' || request.method.length === 0) {
            return { valid: false, error: 'Method must be a non-empty string' };
        }

        return { valid: true };
    }

    /**
     * Parse JSON string to request object
     */
    parseRequest(jsonString: string): { request?: JsonRpcRequest; error?: JsonRpcErrorResponse } {
        try {
            const parsed = JSON.parse(jsonString);
            const validation = this.validateRequest(parsed);

            if (!validation.valid) {
                return {
                    error: this.createErrorResponse(
                        parsed?.id ?? null,
                        JSON_RPC_ERRORS.INVALID_REQUEST,
                        validation.error!
                    )
                };
            }

            return { request: parsed as JsonRpcRequest };
        } catch (e) {
            return {
                error: this.createErrorResponse(
                    null as any,
                    JSON_RPC_ERRORS.PARSE_ERROR,
                    'Parse error: Invalid JSON'
                )
            };
        }
    }

    /**
     * Process a validated JSON-RPC request
     */
    async processRequest(request: JsonRpcRequest): Promise<JsonRpcResponse> {
        const { id, method, params } = request;

        // Check if method exists
        const handler = this.handlers.get(method);
        if (!handler) {
            return this.createErrorResponse(
                id,
                JSON_RPC_ERRORS.METHOD_NOT_FOUND,
                `Method not found: ${method}`
            );
        }

        // Execute handler
        try {
            const result = await handler(params);
            return this.createSuccessResponse(id, result);
        } catch (error: any) {
            return this.createErrorResponse(
                id,
                JSON_RPC_ERRORS.INTERNAL_ERROR,
                error.message || 'Internal error'
            );
        }
    }

    /**
     * Process raw JSON string request
     */
    async processRawRequest(jsonString: string): Promise<JsonRpcResponse> {
        const { request, error } = this.parseRequest(jsonString);

        if (error) {
            return error;
        }

        return this.processRequest(request!);
    }

    /**
     * Create a success response
     */
    createSuccessResponse(id: number | string, result: any): JsonRpcSuccessResponse {
        return {
            jsonrpc: '2.0',
            id,
            result
        };
    }

    /**
     * Create an error response
     */
    createErrorResponse(id: number | string, code: number, message: string, data?: any): JsonRpcErrorResponse {
        const response: JsonRpcErrorResponse = {
            jsonrpc: '2.0',
            id,
            error: {
                code,
                message
            }
        };

        if (data !== undefined) {
            response.error.data = data;
        }

        return response;
    }

    /**
     * Check if response is an error
     */
    static isErrorResponse(response: JsonRpcResponse): response is JsonRpcErrorResponse {
        return 'error' in response;
    }

    /**
     * Check if response is successful
     */
    static isSuccessResponse(response: JsonRpcResponse): response is JsonRpcSuccessResponse {
        return 'result' in response;
    }

    /**
     * Serialize response to JSON string
     */
    static serializeResponse(response: JsonRpcResponse): string {
        return JSON.stringify(response);
    }
}
