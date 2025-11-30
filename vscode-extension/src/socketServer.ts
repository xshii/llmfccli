/**
 * Unix Socket Server for CLI Communication
 *
 * 监听 Unix socket，接收来自 CLI 的 JSON-RPC 请求
 */

import * as net from 'net';
import * as fs from 'fs';
import * as vscode from 'vscode';
import { JsonRpcServer, JsonRpcRequest, JsonRpcResponse } from './jsonRpcServer';

const DEFAULT_SOCKET_PATH = '/tmp/claude-qwen.sock';

export class SocketServer {
    private server: net.Server | null = null;
    private rpcServer: JsonRpcServer;
    private outputChannel: vscode.OutputChannel;
    private socketPath: string;
    private clients: Set<net.Socket> = new Set();

    constructor(outputChannel: vscode.OutputChannel, socketPath: string = DEFAULT_SOCKET_PATH) {
        this.outputChannel = outputChannel;
        this.socketPath = socketPath;
        this.rpcServer = new JsonRpcServer();
    }

    /**
     * 启动 socket 服务器
     */
    async start(): Promise<boolean> {
        if (this.server) {
            this.outputChannel.appendLine('Socket server already running');
            return true;
        }

        // 清理旧的 socket 文件
        try {
            if (fs.existsSync(this.socketPath)) {
                fs.unlinkSync(this.socketPath);
            }
        } catch (error) {
            this.outputChannel.appendLine(`Failed to remove old socket: ${error}`);
        }

        return new Promise((resolve) => {
            this.server = net.createServer((socket) => {
                this.handleConnection(socket);
            });

            this.server.on('error', (error) => {
                this.outputChannel.appendLine(`Socket server error: ${error.message}`);
                resolve(false);
            });

            this.server.listen(this.socketPath, () => {
                this.outputChannel.appendLine(`Socket server listening on ${this.socketPath}`);

                // 设置 socket 文件权限
                try {
                    fs.chmodSync(this.socketPath, 0o666);
                } catch (error) {
                    this.outputChannel.appendLine(`Failed to set socket permissions: ${error}`);
                }

                resolve(true);
            });
        });
    }

    /**
     * 停止 socket 服务器
     */
    async stop(): Promise<void> {
        // 关闭所有客户端连接
        for (const client of this.clients) {
            client.destroy();
        }
        this.clients.clear();

        if (this.server) {
            return new Promise((resolve) => {
                this.server!.close(() => {
                    this.outputChannel.appendLine('Socket server stopped');
                    this.server = null;

                    // 清理 socket 文件
                    try {
                        if (fs.existsSync(this.socketPath)) {
                            fs.unlinkSync(this.socketPath);
                        }
                    } catch (error) {
                        // ignore
                    }

                    resolve();
                });
            });
        }
    }

    /**
     * 检查服务器是否运行
     */
    isRunning(): boolean {
        return this.server !== null;
    }

    /**
     * 处理新连接
     */
    private handleConnection(socket: net.Socket): void {
        this.outputChannel.appendLine('New CLI connection');
        this.clients.add(socket);

        let buffer = '';

        socket.on('data', async (data) => {
            buffer += data.toString();

            // 处理完整的 JSON 行
            while (buffer.includes('\n')) {
                const newlineIndex = buffer.indexOf('\n');
                const line = buffer.substring(0, newlineIndex).trim();
                buffer = buffer.substring(newlineIndex + 1);

                if (!line) continue;

                try {
                    const request: JsonRpcRequest = JSON.parse(line);
                    this.outputChannel.appendLine(`[RPC] Request: ${request.method}`);

                    const response = await this.rpcServer.processRequest(request);

                    this.outputChannel.appendLine(`[RPC] Response: ${JSON.stringify(response).substring(0, 100)}...`);

                    socket.write(JSON.stringify(response) + '\n');
                } catch (error: any) {
                    this.outputChannel.appendLine(`[RPC] Parse error: ${error.message}`);

                    // 发送错误响应
                    const errorResponse = {
                        jsonrpc: '2.0',
                        id: null as any,
                        error: {
                            code: -32700,
                            message: 'Parse error'
                        }
                    };
                    socket.write(JSON.stringify(errorResponse) + '\n');
                }
            }
        });

        socket.on('close', () => {
            this.outputChannel.appendLine('CLI disconnected');
            this.clients.delete(socket);
        });

        socket.on('error', (error) => {
            this.outputChannel.appendLine(`Socket error: ${error.message}`);
            this.clients.delete(socket);
        });
    }
}
