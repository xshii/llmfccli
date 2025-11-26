/**
 * JSON-RPC server for handling requests from Claude-Qwen CLI
 */

import * as vscode from 'vscode';
import { JsonRpcRequest, JsonRpcResponse, FileInfo, Selection, DiffParams, ApplyChangesParams, OpenFileParams } from './types';

export class JsonRpcServer {
    private requestHandlers: Map<string, (params: any) => Promise<any>>;

    constructor() {
        this.requestHandlers = new Map();
        this.registerHandlers();
    }

    /**
     * Register all JSON-RPC method handlers
     */
    private registerHandlers(): void {
        this.requestHandlers.set('getActiveFile', this.handleGetActiveFile.bind(this));
        this.requestHandlers.set('getSelection', this.handleGetSelection.bind(this));
        this.requestHandlers.set('showDiff', this.handleShowDiff.bind(this));
        this.requestHandlers.set('applyChanges', this.handleApplyChanges.bind(this));
        this.requestHandlers.set('openFile', this.handleOpenFile.bind(this));
        this.requestHandlers.set('getWorkspaceFolder', this.handleGetWorkspaceFolder.bind(this));
    }

    /**
     * Process incoming JSON-RPC request
     */
    async processRequest(request: JsonRpcRequest): Promise<JsonRpcResponse> {
        const { id, method, params } = request;

        try {
            const handler = this.requestHandlers.get(method);
            if (!handler) {
                return this.errorResponse(id, -32601, `Method not found: ${method}`);
            }

            const result = await handler(params);
            return this.successResponse(id, result);
        } catch (error: any) {
            return this.errorResponse(id, -32603, error.message || 'Internal error');
        }
    }

    /**
     * Handle getActiveFile request
     */
    private async handleGetActiveFile(params: any): Promise<{ success: boolean; file?: FileInfo; error?: string }> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return { success: false, error: 'No active file' };
        }

        const document = editor.document;
        const fileInfo: FileInfo = {
            path: document.uri.fsPath,
            content: document.getText(),
            language: document.languageId,
            lineCount: document.lineCount
        };

        return { success: true, file: fileInfo };
    }

    /**
     * Handle getSelection request
     */
    private async handleGetSelection(params: any): Promise<{ success: boolean; selection?: Selection; error?: string }> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return { success: false, error: 'No active editor' };
        }

        const selection = editor.selection;
        if (selection.isEmpty) {
            return { success: false, error: 'No text selected' };
        }

        const selectionData: Selection = {
            text: editor.document.getText(selection),
            start: {
                line: selection.start.line,
                character: selection.start.character
            },
            end: {
                line: selection.end.line,
                character: selection.end.character
            }
        };

        return { success: true, selection: selectionData };
    }

    /**
     * Handle showDiff request
     */
    private async handleShowDiff(params: DiffParams): Promise<{ success: boolean; message?: string; error?: string }> {
        try {
            const { title, originalPath, modifiedContent } = params;

            // Create URIs for diff view
            const originalUri = vscode.Uri.file(originalPath);
            const modifiedUri = vscode.Uri.parse(`claude-qwen:${originalPath}?modified`);

            // Register text document content provider for modified content
            const provider = new (class implements vscode.TextDocumentContentProvider {
                provideTextDocumentContent(uri: vscode.Uri): string {
                    return modifiedContent;
                }
            })();

            const registration = vscode.workspace.registerTextDocumentContentProvider('claude-qwen', provider);

            // Show diff
            await vscode.commands.executeCommand('vscode.diff', originalUri, modifiedUri, title);

            // Dispose registration after a delay
            setTimeout(() => registration.dispose(), 60000);

            return { success: true, message: `Diff shown: ${title}` };
        } catch (error: any) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Handle applyChanges request
     */
    private async handleApplyChanges(params: ApplyChangesParams): Promise<{ success: boolean; message?: string; error?: string }> {
        try {
            const { path, oldStr, newStr } = params;
            const uri = vscode.Uri.file(path);

            // Open document
            const document = await vscode.workspace.openTextDocument(uri);
            const text = document.getText();

            // Find and replace
            const newText = text.replace(oldStr, newStr);
            if (text === newText) {
                return { success: false, error: 'Old string not found in file' };
            }

            // Apply edit
            const edit = new vscode.WorkspaceEdit();
            const fullRange = new vscode.Range(
                document.positionAt(0),
                document.positionAt(text.length)
            );
            edit.replace(uri, fullRange, newText);

            const applied = await vscode.workspace.applyEdit(edit);
            if (!applied) {
                return { success: false, error: 'Failed to apply edit' };
            }

            // Save document
            await document.save();

            return { success: true, message: `Applied changes to ${path}` };
        } catch (error: any) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Handle openFile request
     */
    private async handleOpenFile(params: OpenFileParams): Promise<{ success: boolean; message?: string; error?: string }> {
        try {
            const { path, line, column } = params;
            const uri = vscode.Uri.file(path);

            // Open document
            const document = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(document);

            // Jump to position if specified
            if (line !== undefined) {
                const position = new vscode.Position(line - 1, column || 0);
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
            }

            return { success: true, message: `Opened file: ${path}` };
        } catch (error: any) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Handle getWorkspaceFolder request
     */
    private async handleGetWorkspaceFolder(params: any): Promise<{ success: boolean; folder?: string; error?: string }> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return { success: false, error: 'No workspace folder open' };
        }

        return { success: true, folder: workspaceFolder.uri.fsPath };
    }

    /**
     * Create success response
     */
    private successResponse(id: number | string, result: any): JsonRpcResponse {
        return {
            jsonrpc: '2.0',
            id,
            result
        };
    }

    /**
     * Create error response
     */
    private errorResponse(id: number | string, code: number, message: string): JsonRpcResponse {
        return {
            jsonrpc: '2.0',
            id,
            error: {
                code,
                message
            }
        };
    }
}
