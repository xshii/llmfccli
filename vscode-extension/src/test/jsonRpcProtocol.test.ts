/**
 * Standalone tests for JsonRpcProtocol
 *
 * These tests can run in pure Node.js environment without VSCode.
 * Run with: npx ts-node src/test/jsonRpcProtocol.test.ts
 * Or after compile: node out/test/jsonRpcProtocol.test.js
 */

import { JsonRpcProtocol, JSON_RPC_ERRORS } from '../jsonRpcProtocol';

// Simple test framework
let passed = 0;
let failed = 0;

function test(name: string, fn: () => void | Promise<void>): Promise<void> {
    return Promise.resolve(fn()).then(
        () => {
            console.log(`  ✓ ${name}`);
            passed++;
        },
        (err) => {
            console.log(`  ✗ ${name}`);
            console.log(`    Error: ${err.message}`);
            failed++;
        }
    );
}

function assert(condition: boolean, message: string): void {
    if (!condition) {
        throw new Error(message);
    }
}

function assertEqual<T>(actual: T, expected: T, message?: string): void {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

// Test suite
async function runTests() {
    console.log('\n' + '='.repeat(60));
    console.log('JsonRpcProtocol Unit Tests (No VSCode dependency)');
    console.log('='.repeat(60) + '\n');

    const protocol = new JsonRpcProtocol();

    // Test 1: Method registration
    console.log('Test Suite: Method Registration');
    console.log('-'.repeat(40));

    await test('registerMethod adds handler', () => {
        protocol.registerMethod('testMethod', async () => 'result');
        assert(protocol.hasMethod('testMethod'), 'Method should be registered');
    });

    await test('getRegisteredMethods returns all methods', () => {
        protocol.registerMethod('anotherMethod', async () => 'another');
        const methods = protocol.getRegisteredMethods();
        assert(methods.includes('testMethod'), 'Should include testMethod');
        assert(methods.includes('anotherMethod'), 'Should include anotherMethod');
    });

    await test('unregisterMethod removes handler', () => {
        const removed = protocol.unregisterMethod('anotherMethod');
        assert(removed, 'Should return true when method exists');
        assert(!protocol.hasMethod('anotherMethod'), 'Method should be removed');
    });

    // Test 2: Request validation
    console.log('\nTest Suite: Request Validation');
    console.log('-'.repeat(40));

    await test('validates correct request', () => {
        const result = protocol.validateRequest({
            jsonrpc: '2.0',
            id: 1,
            method: 'test'
        });
        assert(result.valid, 'Should be valid');
    });

    await test('rejects non-object request', () => {
        const result = protocol.validateRequest('not an object');
        assert(!result.valid, 'Should be invalid');
        assert(result.error!.includes('object'), 'Error should mention object');
    });

    await test('rejects wrong jsonrpc version', () => {
        const result = protocol.validateRequest({
            jsonrpc: '1.0',
            id: 1,
            method: 'test'
        });
        assert(!result.valid, 'Should be invalid');
        assert(result.error!.includes('2.0'), 'Error should mention 2.0');
    });

    await test('rejects missing id', () => {
        const result = protocol.validateRequest({
            jsonrpc: '2.0',
            method: 'test'
        });
        assert(!result.valid, 'Should be invalid');
        assert(result.error!.includes('id'), 'Error should mention id');
    });

    await test('rejects empty method', () => {
        const result = protocol.validateRequest({
            jsonrpc: '2.0',
            id: 1,
            method: ''
        });
        assert(!result.valid, 'Should be invalid');
        assert(result.error!.toLowerCase().includes('method'), 'Error should mention method');
    });

    // Test 3: Request parsing
    console.log('\nTest Suite: Request Parsing');
    console.log('-'.repeat(40));

    await test('parses valid JSON', () => {
        const { request, error } = protocol.parseRequest(
            '{"jsonrpc":"2.0","id":1,"method":"test"}'
        );
        assert(!error, 'Should not have error');
        assert(request !== undefined, 'Should have request');
        assertEqual(request!.method, 'test', 'Method should be test');
    });

    await test('returns parse error for invalid JSON', () => {
        const { request, error } = protocol.parseRequest('not json');
        assert(!request, 'Should not have request');
        assert(error !== undefined, 'Should have error');
        assertEqual(error!.error.code, JSON_RPC_ERRORS.PARSE_ERROR, 'Should be parse error');
    });

    await test('returns invalid request error for bad structure', () => {
        const { request, error } = protocol.parseRequest(
            '{"jsonrpc":"1.0","id":1,"method":"test"}'
        );
        assert(!request, 'Should not have request');
        assert(error !== undefined, 'Should have error');
        assertEqual(error!.error.code, JSON_RPC_ERRORS.INVALID_REQUEST, 'Should be invalid request');
    });

    // Test 4: Request processing
    console.log('\nTest Suite: Request Processing');
    console.log('-'.repeat(40));

    // Register a test handler
    protocol.registerMethod('echo', async (params: any) => params);
    protocol.registerMethod('add', async (params: { a: number; b: number }) => params.a + params.b);
    protocol.registerMethod('throwError', async () => { throw new Error('Test error'); });

    await test('processes valid request with result', async () => {
        const response = await protocol.processRequest({
            jsonrpc: '2.0',
            id: 1,
            method: 'echo',
            params: { message: 'hello' }
        });
        assert('result' in response, 'Should have result');
        assertEqual(response.id, 1, 'ID should match');
        assertEqual((response as any).result.message, 'hello', 'Result should echo params');
    });

    await test('processes request with computed result', async () => {
        const response = await protocol.processRequest({
            jsonrpc: '2.0',
            id: 2,
            method: 'add',
            params: { a: 2, b: 3 }
        });
        assert('result' in response, 'Should have result');
        assertEqual((response as any).result, 5, 'Result should be 5');
    });

    await test('returns method not found for unknown method', async () => {
        const response = await protocol.processRequest({
            jsonrpc: '2.0',
            id: 3,
            method: 'unknownMethod'
        });
        assert('error' in response, 'Should have error');
        assertEqual((response as any).error.code, JSON_RPC_ERRORS.METHOD_NOT_FOUND, 'Should be method not found');
    });

    await test('returns internal error when handler throws', async () => {
        const response = await protocol.processRequest({
            jsonrpc: '2.0',
            id: 4,
            method: 'throwError'
        });
        assert('error' in response, 'Should have error');
        assertEqual((response as any).error.code, JSON_RPC_ERRORS.INTERNAL_ERROR, 'Should be internal error');
        assert((response as any).error.message.includes('Test error'), 'Should include error message');
    });

    // Test 5: Raw request processing
    console.log('\nTest Suite: Raw Request Processing');
    console.log('-'.repeat(40));

    await test('processRawRequest handles full flow', async () => {
        const response = await protocol.processRawRequest(
            '{"jsonrpc":"2.0","id":10,"method":"add","params":{"a":10,"b":20}}'
        );
        assert('result' in response, 'Should have result');
        assertEqual((response as any).result, 30, 'Result should be 30');
    });

    await test('processRawRequest handles parse error', async () => {
        const response = await protocol.processRawRequest('invalid json');
        assert('error' in response, 'Should have error');
        assertEqual((response as any).error.code, JSON_RPC_ERRORS.PARSE_ERROR, 'Should be parse error');
    });

    // Test 6: Response helpers
    console.log('\nTest Suite: Response Helpers');
    console.log('-'.repeat(40));

    await test('createSuccessResponse format', () => {
        const response = protocol.createSuccessResponse(1, { data: 'test' });
        assertEqual(response.jsonrpc, '2.0', 'Should have jsonrpc 2.0');
        assertEqual(response.id, 1, 'Should have correct id');
        assertEqual(response.result.data, 'test', 'Should have result');
    });

    await test('createErrorResponse format', () => {
        const response = protocol.createErrorResponse(2, -32000, 'Custom error', { extra: 'data' });
        assertEqual(response.jsonrpc, '2.0', 'Should have jsonrpc 2.0');
        assertEqual(response.id, 2, 'Should have correct id');
        assertEqual(response.error.code, -32000, 'Should have error code');
        assertEqual(response.error.message, 'Custom error', 'Should have error message');
        assertEqual(response.error.data?.extra, 'data', 'Should have error data');
    });

    await test('isErrorResponse detects errors', () => {
        const errorResp = protocol.createErrorResponse(1, -32000, 'error');
        const successResp = protocol.createSuccessResponse(1, 'ok');
        assert(JsonRpcProtocol.isErrorResponse(errorResp), 'Should detect error response');
        assert(!JsonRpcProtocol.isErrorResponse(successResp), 'Should not detect success as error');
    });

    await test('isSuccessResponse detects success', () => {
        const errorResp = protocol.createErrorResponse(1, -32000, 'error');
        const successResp = protocol.createSuccessResponse(1, 'ok');
        assert(JsonRpcProtocol.isSuccessResponse(successResp), 'Should detect success response');
        assert(!JsonRpcProtocol.isSuccessResponse(errorResp), 'Should not detect error as success');
    });

    await test('serializeResponse produces valid JSON', () => {
        const response = protocol.createSuccessResponse(1, { test: true });
        const json = JsonRpcProtocol.serializeResponse(response);
        const parsed = JSON.parse(json);
        assertEqual(parsed.jsonrpc, '2.0', 'Should serialize correctly');
    });

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log(`Results: ${passed} passed, ${failed} failed`);
    console.log('='.repeat(60) + '\n');

    if (failed > 0) {
        process.exit(1);
    }
}

// Run tests
runTests().catch(console.error);
