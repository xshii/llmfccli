#!/bin/bash
# SSH 隧道将本地 11434 端口转发到远端 Ollama 服务
# 使用方法: ./setup_ollama_tunnel.sh [user@host]
# 示例: ./setup_ollama_tunnel.sh your_user@192.168.3.41

HOST=${1:-"your_user@192.168.3.41"}

echo "正在建立 SSH 隧道到 $HOST ..."
echo "本地端口 11434 -> 远端 localhost:11434"
echo "按 Ctrl+C 停止隧道"
echo ""

ssh -N -L 11434:localhost:11434 "$HOST"
