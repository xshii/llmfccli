/**
 * Type definitions for Claude-Qwen VSCode extension
 */

/**
 * JSON-RPC request structure
 */
export interface JsonRpcRequest {
    jsonrpc: '2.0';
    id: number | string;
    method: string;
    params: any;
}

/**
 * JSON-RPC response structure
 */
export interface JsonRpcResponse {
    jsonrpc: '2.0';
    id: number | string;
    result?: any;
    error?: {
        code: number;
        message: string;
        data?: any;
    };
}

/**
 * File information
 */
export interface FileInfo {
    path: string;
    content: string;
    language: string;
    lineCount: number;
}

/**
 * Text selection
 */
export interface Selection {
    text: string;
    start: {
        line: number;
        character: number;
    };
    end: {
        line: number;
        character: number;
    };
}

/**
 * Diff parameters
 */
export interface DiffParams {
    title: string;
    originalPath: string;
    modifiedContent: string;
}

/**
 * Apply changes parameters
 */
export interface ApplyChangesParams {
    path: string;
    oldStr: string;
    newStr: string;
}

/**
 * Open file parameters
 */
export interface OpenFileParams {
    path: string;
    line?: number;
    column?: number;
}

/**
 * Extension configuration
 */
export interface ExtensionConfig {
    cliPath: string;
    pythonPath: string;
    communicationMode: 'ipc' | 'socket';
    socketPath: string;
    autoStart: boolean;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
}
