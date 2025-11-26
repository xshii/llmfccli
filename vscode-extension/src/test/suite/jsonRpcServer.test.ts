/**
 * JSON-RPC Server Tests
 *
 * Tests the RPC server functionality without requiring CLI
 */

import * as assert from 'assert';
import { JsonRpcServer } from '../../jsonRpcServer';

suite('JSON-RPC Server Test Suite', () => {
    let server: JsonRpcServer;

    setup(() => {
        server = new JsonRpcServer();
    });

    teardown(() => {
        // Cleanup
    });

    test('Server initialization', () => {
        assert.ok(server, 'Server should be created');
    });

    test('Process valid JSON-RPC request', async () => {
        const request = {
            jsonrpc: '2.0' as const,
            id: 1,
            method: 'getActiveFile',
            params: {}
        };

        const response = await server.processRequest(request);

        assert.strictEqual(response.jsonrpc, '2.0');
        assert.strictEqual(response.id, 1);
        assert.ok('result' in response || 'error' in response);
    });

    test('Handle unknown method', async () => {
        const request = {
            jsonrpc: '2.0' as const,
            id: 2,
            method: 'unknownMethod',
            params: {}
        };

        const response = await server.processRequest(request);

        assert.strictEqual(response.jsonrpc, '2.0');
        assert.strictEqual(response.id, 2);
        assert.ok('error' in response);
        if ('error' in response && response.error) {
            assert.strictEqual(response.error.code, -32601); // Method not found
        }
    });

    test('Validate JSON-RPC 2.0 format', async () => {
        const request = {
            jsonrpc: '2.0' as const,
            id: 3,
            method: 'getWorkspaceFolder',
            params: {}
        };

        const response = await server.processRequest(request);

        assert.strictEqual(response.jsonrpc, '2.0', 'Response should have jsonrpc 2.0');
        assert.strictEqual(response.id, 3, 'Response ID should match request ID');
    });

    test('Handle requests without parameters', async () => {
        const request = {
            jsonrpc: '2.0' as const,
            id: 4,
            method: 'getSelection',
            params: {}
        };

        const response = await server.processRequest(request);

        assert.ok(response, 'Should return response');
        assert.strictEqual(response.id, 4);
    });
});
