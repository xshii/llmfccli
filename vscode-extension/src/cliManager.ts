/**
 * CLI Process Manager
 * Manages the claude-qwen CLI process and handles IPC communication
 */

import * as vscode from 'vscode';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import { JsonRpcRequest, JsonRpcResponse, ExtensionConfig } from './types';
import { JsonRpcServer } from './jsonRpcServer';

export class CliManager {
    private cliProcess: ChildProcessWithoutNullStreams | null = null;
    private rpcServer: JsonRpcServer;
    private outputChannel: vscode.OutputChannel;
    private config: ExtensionConfig;
    private requestBuffer: string = '';

    constructor(config: ExtensionConfig, outputChannel: vscode.OutputChannel) {
        this.config = config;
        this.outputChannel = outputChannel;
        this.rpcServer = new JsonRpcServer();
    }

    /**
     * Start the CLI process
     */
    async start(workspaceRoot: string): Promise<boolean> {
        if (this.cliProcess) {
            this.outputChannel.appendLine('CLI already running');
            return true;
        }

        try {
            this.outputChannel.appendLine(`Starting CLI: ${this.config.pythonPath} -m backend.cli --root ${workspaceRoot}`);

            // Spawn CLI process
            this.cliProcess = spawn(
                this.config.pythonPath,
                ['-m', 'backend.cli', '--root', workspaceRoot, '--skip-precheck'],
                {
                    cwd: workspaceRoot,
                    env: {
                        ...process.env,
                        VSCODE_INTEGRATION: 'true',
                        PYTHONUNBUFFERED: '1'
                    }
                }
            );

            // Handle stdout (JSON-RPC requests from CLI)
            this.cliProcess.stdout.on('data', (data) => {
                this.handleCliOutput(data);
            });

            // Handle stderr (CLI logs)
            this.cliProcess.stderr.on('data', (data) => {
                this.outputChannel.appendLine(`[CLI STDERR] ${data.toString()}`);
            });

            // Handle process exit
            this.cliProcess.on('exit', (code, signal) => {
                this.outputChannel.appendLine(`CLI process exited with code ${code}, signal ${signal}`);
                this.cliProcess = null;
            });

            // Handle process error
            this.cliProcess.on('error', (error) => {
                this.outputChannel.appendLine(`CLI process error: ${error.message}`);
                vscode.window.showErrorMessage(`Failed to start Claude-Qwen CLI: ${error.message}`);
                this.cliProcess = null;
            });

            this.outputChannel.appendLine('CLI started successfully');
            return true;
        } catch (error: any) {
            this.outputChannel.appendLine(`Failed to start CLI: ${error.message}`);
            vscode.window.showErrorMessage(`Failed to start Claude-Qwen CLI: ${error.message}`);
            return false;
        }
    }

    /**
     * Stop the CLI process
     */
    async stop(): Promise<void> {
        if (!this.cliProcess) {
            this.outputChannel.appendLine('CLI not running');
            return;
        }

        this.outputChannel.appendLine('Stopping CLI...');
        this.cliProcess.kill('SIGTERM');

        // Wait for process to exit
        await new Promise<void>((resolve) => {
            const timeout = setTimeout(() => {
                if (this.cliProcess) {
                    this.cliProcess.kill('SIGKILL');
                }
                resolve();
            }, 5000);

            if (this.cliProcess) {
                this.cliProcess.on('exit', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            } else {
                clearTimeout(timeout);
                resolve();
            }
        });

        this.cliProcess = null;
        this.outputChannel.appendLine('CLI stopped');
    }

    /**
     * Check if CLI is running
     */
    isRunning(): boolean {
        return this.cliProcess !== null;
    }

    /**
     * Handle CLI output (JSON-RPC requests)
     */
    private async handleCliOutput(data: Buffer): Promise<void> {
        const text = data.toString();
        this.requestBuffer += text;

        // Try to parse complete JSON-RPC requests
        const lines = this.requestBuffer.split('\n');
        this.requestBuffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('{')) {
                // Not a JSON line, could be CLI output
                this.outputChannel.appendLine(`[CLI] ${trimmed}`);
                continue;
            }

            try {
                const request: JsonRpcRequest = JSON.parse(trimmed);
                if (this.config.logLevel === 'debug') {
                    this.outputChannel.appendLine(`[RPC REQUEST] ${JSON.stringify(request)}`);
                }

                // Process request
                const response = await this.rpcServer.processRequest(request);

                if (this.config.logLevel === 'debug') {
                    this.outputChannel.appendLine(`[RPC RESPONSE] ${JSON.stringify(response)}`);
                }

                // Send response back to CLI
                this.sendResponse(response);
            } catch (error: any) {
                this.outputChannel.appendLine(`Failed to parse JSON-RPC request: ${error.message}`);
                this.outputChannel.appendLine(`Line: ${trimmed}`);
            }
        }
    }

    /**
     * Send JSON-RPC response to CLI
     */
    private sendResponse(response: JsonRpcResponse): void {
        if (!this.cliProcess || !this.cliProcess.stdin.writable) {
            this.outputChannel.appendLine('Cannot send response: CLI process not available');
            return;
        }

        try {
            const json = JSON.stringify(response) + '\n';
            this.cliProcess.stdin.write(json);
        } catch (error: any) {
            this.outputChannel.appendLine(`Failed to send response: ${error.message}`);
        }
    }

    /**
     * Send a command to CLI
     */
    async sendCommand(command: string): Promise<void> {
        if (!this.cliProcess || !this.cliProcess.stdin.writable) {
            throw new Error('CLI not running');
        }

        this.cliProcess.stdin.write(command + '\n');
    }
}
