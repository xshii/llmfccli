/**
 * Socket Server for CLI Communication
 *
 * 支持两种通信方式：
 * - Unix Domain Socket (Linux/macOS): /tmp/claude-qwen.sock
 * - TCP Socket (Windows/跨平台): localhost:11435
 */

import * as net from 'net';
import * as fs from 'fs';
import * as os from 'os';
import * as vscode from 'vscode';
import { JsonRpcServer, JsonRpcRequest, JsonRpcResponse } from './jsonRpcServer';

const DEFAULT_SOCKET_PATH = '/tmp/claude-qwen.sock';
const DEFAULT_TCP_PORT = 11435;

export class SocketServer {
    private server: net.Server | null = null;
    private rpcServer: JsonRpcServer;
    private outputChannel: vscode.OutputChannel;
    private socketPath: string;
    private clients: Set<net.Socket> = new Set();

    // TCP socket 配置
    private useTcp: boolean = false;
    private tcpHost: string = 'localhost';
    private tcpPort: number = DEFAULT_TCP_PORT;

    constructor(outputChannel: vscode.OutputChannel, socketPath: string = DEFAULT_SOCKET_PATH) {
        this.outputChannel = outputChannel;
        this.socketPath = socketPath;
        this.rpcServer = new JsonRpcServer();

        // 解析 socket 配置
        this._parseSocketConfig(socketPath);
    }

    /**
     * 解析 socket 配置
     * 支持格式：
     * - Unix socket: /tmp/claude-qwen.sock
     * - TCP socket: tcp://localhost:11435 或 localhost:11435
     */
    private _parseSocketConfig(socketPath: string): void {
        // 检测是否是 TCP 配置
        if (socketPath.startsWith('tcp://') || socketPath.includes(':')) {
            this.useTcp = true;

            // 移除 tcp:// 前缀
            let address = socketPath.replace('tcp://', '');

            // 解析 host:port
            const parts = address.split(':');
            if (parts.length === 2) {
                this.tcpHost = parts[0] || 'localhost';
                this.tcpPort = parseInt(parts[1], 10) || DEFAULT_TCP_PORT;
            } else {
                // 只有端口号
                this.tcpPort = parseInt(address, 10) || DEFAULT_TCP_PORT;
            }

            this.outputChannel.appendLine(`Parsed TCP config: ${this.tcpHost}:${this.tcpPort}`);
        } else {
            // Unix socket
            this.useTcp = false;

            // Windows 平台检测
            if (os.platform() === 'win32') {
                this.outputChannel.appendLine('WARNING: Unix socket on Windows is not fully supported');
                this.outputChannel.appendLine('Consider using TCP socket: tcp://localhost:11435');
            }
        }
    }

    /**
     * 启动 socket 服务器
     */
    async start(): Promise<boolean> {
        if (this.server) {
            this.outputChannel.appendLine('Socket server already running');
            return true;
        }

        return new Promise((resolve) => {
            this.server = net.createServer((socket) => {
                this.handleConnection(socket);
            });

            this.server.on('error', (error) => {
                this.outputChannel.appendLine(`Socket server error: ${error.message}`);
                resolve(false);
            });

            if (this.useTcp) {
                // TCP Socket 模式
                this.server.listen(this.tcpPort, this.tcpHost, () => {
                    this.outputChannel.appendLine(`Socket server (TCP) listening on ${this.tcpHost}:${this.tcpPort}`);
                    resolve(true);
                });
            } else {
                // Unix Socket 模式
                // 清理旧的 socket 文件
                try {
                    if (fs.existsSync(this.socketPath)) {
                        fs.unlinkSync(this.socketPath);
                    }
                } catch (error) {
                    this.outputChannel.appendLine(`Failed to remove old socket: ${error}`);
                }

                this.server.listen(this.socketPath, () => {
                    this.outputChannel.appendLine(`Socket server (Unix) listening on ${this.socketPath}`);

                    // 设置 socket 文件权限
                    try {
                        fs.chmodSync(this.socketPath, 0o666);
                    } catch (error) {
                        this.outputChannel.appendLine(`Failed to set socket permissions: ${error}`);
                    }

                    resolve(true);
                });
            }
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

                    // 只有 Unix socket 模式才需要清理文件
                    if (!this.useTcp) {
                        try {
                            if (fs.existsSync(this.socketPath)) {
                                fs.unlinkSync(this.socketPath);
                            }
                        } catch (error) {
                            // ignore
                        }
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
