/**
 * JSON-RPC server for handling requests from Claude-Qwen CLI
 *
 * This module handles VSCode-specific operations.
 * Protocol logic is delegated to JsonRpcProtocol.
 */

import * as vscode from 'vscode';
import { JsonRpcProtocol, JsonRpcRequest, JsonRpcResponse } from './jsonRpcProtocol';
import { FileInfo, Selection, DiffParams, ApplyChangesParams, OpenFileParams } from './types';

export class JsonRpcServer {
    private protocol: JsonRpcProtocol;
    private currentDiffEditor: vscode.TextEditor | undefined;

    constructor() {
        this.protocol = new JsonRpcProtocol();
        this.registerHandlers();
    }

    /**
     * Register all JSON-RPC method handlers
     */
    private registerHandlers(): void {
        this.protocol.registerMethod('ping', this.handlePing.bind(this));
        this.protocol.registerMethod('getActiveFile', this.handleGetActiveFile.bind(this));
        this.protocol.registerMethod('getSelection', this.handleGetSelection.bind(this));
        this.protocol.registerMethod('showDiff', this.handleShowDiff.bind(this));
        this.protocol.registerMethod('closeDiff', this.handleCloseDiff.bind(this));
        this.protocol.registerMethod('applyChanges', this.handleApplyChanges.bind(this));
        this.protocol.registerMethod('openFile', this.handleOpenFile.bind(this));
        this.protocol.registerMethod('getWorkspaceFolder', this.handleGetWorkspaceFolder.bind(this));
    }

    /**
     * Handle ping request (heartbeat)
     */
    private async handlePing(params: any): Promise<{ pong: boolean }> {
        return { pong: true };
    }

    /**
     * Process incoming JSON-RPC request
     */
    async processRequest(request: JsonRpcRequest): Promise<JsonRpcResponse> {
        return this.protocol.processRequest(request);
    }

    /**
     * Process raw JSON string request
     */
    async processRawRequest(jsonString: string): Promise<JsonRpcResponse> {
        return this.protocol.processRawRequest(jsonString);
    }

    /**
     * Get the underlying protocol handler (for testing)
     */
    getProtocol(): JsonRpcProtocol {
        return this.protocol;
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
     * 返回选中区域或光标位置
     */
    private async handleGetSelection(params: any): Promise<{ success: boolean; selection?: Selection; error?: string }> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return { success: false, error: 'No active editor' };
        }

        const selection = editor.selection;

        // 即使没有选中文本，也返回光标位置
        const selectionData: Selection = {
            text: selection.isEmpty ? '' : editor.document.getText(selection),
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

            // Create URIs for diff view with unique timestamp to ensure refresh
            const originalUri = vscode.Uri.file(originalPath);
            const timestamp = Date.now();
            const modifiedUri = vscode.Uri.parse(`claude-qwen:${originalPath}?modified=${timestamp}`);

            // Register text document content provider for modified content
            const provider = new (class implements vscode.TextDocumentContentProvider {
                provideTextDocumentContent(uri: vscode.Uri): string {
                    return modifiedContent;
                }
            })();

            const registration = vscode.workspace.registerTextDocumentContentProvider('claude-qwen', provider);

            // Show diff and save editor reference
            await vscode.commands.executeCommand('vscode.diff', originalUri, modifiedUri, title);
            this.currentDiffEditor = vscode.window.activeTextEditor;

            // Dispose registration after a delay
            setTimeout(() => registration.dispose(), 60000);

            return { success: true, message: `Diff shown: ${title}` };
        } catch (error: any) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Handle closeDiff request
     */
    private async handleCloseDiff(params: any): Promise<{ success: boolean; message?: string; error?: string }> {
        try {
            if (this.currentDiffEditor && !this.currentDiffEditor.document.isClosed) {
                // Close the diff editor
                await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                this.currentDiffEditor = undefined;
                return { success: true, message: 'Diff closed' };
            }
            return { success: true, message: 'No diff to close' };
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
}

// Re-export types for convenience
export { JsonRpcRequest, JsonRpcResponse, JsonRpcProtocol } from './jsonRpcProtocol';
