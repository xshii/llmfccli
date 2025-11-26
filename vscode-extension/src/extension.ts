/**
 * Claude-Qwen VSCode Extension
 * Main entry point
 */

import * as vscode from 'vscode';
import { CliManager } from './cliManager';
import { ExtensionConfig } from './types';

let cliManager: CliManager | null = null;
let outputChannel: vscode.OutputChannel;

/**
 * Extension activation
 */
export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('Claude-Qwen');
    outputChannel.appendLine('Claude-Qwen extension activated');

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.start', async () => {
            await startCli();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.stop', async () => {
            await stopCli();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.testIntegration', async () => {
            await testIntegration();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.fixCompileErrors', async () => {
            await sendCliCommand('编译项目并修复所有错误');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.generateTests', async () => {
            await sendCliCommand('为当前文件生成单元测试');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('claude-qwen.explainCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor && !editor.selection.isEmpty) {
                const selectedText = editor.document.getText(editor.selection);
                await sendCliCommand(`解释这段代码:\n\n${selectedText}`);
            } else {
                vscode.window.showWarningMessage('Please select some code first');
            }
        })
    );

    // Auto-start if configured
    const config = getConfig();
    if (config.autoStart && vscode.workspace.workspaceFolders) {
        startCli();
    }

    outputChannel.appendLine('Commands registered successfully');
}

/**
 * Extension deactivation
 */
export function deactivate() {
    if (cliManager) {
        cliManager.stop();
    }
    outputChannel.appendLine('Claude-Qwen extension deactivated');
}

/**
 * Start CLI process
 */
async function startCli(): Promise<void> {
    if (cliManager?.isRunning()) {
        vscode.window.showInformationMessage('Claude-Qwen CLI is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const config = getConfig();
    cliManager = new CliManager(config, outputChannel);

    const started = await cliManager.start(workspaceFolder.uri.fsPath);
    if (started) {
        vscode.window.showInformationMessage('Claude-Qwen CLI started');
        outputChannel.show();
    } else {
        vscode.window.showErrorMessage('Failed to start Claude-Qwen CLI');
    }
}

/**
 * Stop CLI process
 */
async function stopCli(): Promise<void> {
    if (!cliManager) {
        vscode.window.showInformationMessage('Claude-Qwen CLI is not running');
        return;
    }

    await cliManager.stop();
    cliManager = null;
    vscode.window.showInformationMessage('Claude-Qwen CLI stopped');
}

/**
 * Test VSCode integration
 */
async function testIntegration(): Promise<void> {
    if (!cliManager?.isRunning()) {
        const start = await vscode.window.showInformationMessage(
            'CLI is not running. Start it now?',
            'Yes',
            'No'
        );
        if (start === 'Yes') {
            await startCli();
            // Wait a bit for CLI to start
            await new Promise(resolve => setTimeout(resolve, 2000));
        } else {
            return;
        }
    }

    if (cliManager) {
        try {
            await cliManager.sendCommand('/testvs');
            vscode.window.showInformationMessage('Integration test command sent to CLI');
            outputChannel.show();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to send test command: ${error.message}`);
        }
    }
}

/**
 * Send command to CLI
 */
async function sendCliCommand(command: string): Promise<void> {
    if (!cliManager?.isRunning()) {
        const start = await vscode.window.showInformationMessage(
            'CLI is not running. Start it now?',
            'Yes',
            'No'
        );
        if (start === 'Yes') {
            await startCli();
            // Wait a bit for CLI to start
            await new Promise(resolve => setTimeout(resolve, 2000));
        } else {
            return;
        }
    }

    if (cliManager) {
        try {
            await cliManager.sendCommand(command);
            outputChannel.show();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to send command: ${error.message}`);
        }
    }
}

/**
 * Get extension configuration
 */
function getConfig(): ExtensionConfig {
    const config = vscode.workspace.getConfiguration('claude-qwen');
    return {
        cliPath: config.get('cliPath', 'claude-qwen'),
        pythonPath: config.get('pythonPath', 'python3'),
        communicationMode: config.get('communicationMode', 'ipc'),
        socketPath: config.get('socketPath', '/tmp/claude-qwen.sock'),
        autoStart: config.get('autoStart', false),
        logLevel: config.get('logLevel', 'info')
    };
}
