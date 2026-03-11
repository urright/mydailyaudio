#!/bin/bash
echo "=== Agent Reach 状态检查 ==="
if command -v agent-reach &> /dev/null; then
    echo "✅ agent-reach 已安装"
    agent-reach --version
    echo ""
    echo "=== 运行 doctor 检查 ==="
    agent-reach doctor
else
    echo "❌ agent-reach 未安装"
    exit 1
fi