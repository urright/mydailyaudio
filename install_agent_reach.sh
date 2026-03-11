#!/bin/bash
set -e

echo "=== Agent Reach 安装开始 ==="

# Step 1: Install agent-reach package
echo "1/5: 正在安装 agent-reach..."
pip install https://github.com/Panniantong/agent-reach/archive/main.zip

# Step 2: Run automatic installation
echo "2/5: 正在运行 agent-reach install (自动检测环境并安装依赖)..."
agent-reach install --env=auto

# Step 3: Check doctor status
echo "3/5: 检查安装状态..."
agent-reach doctor || true

# Step 4: Check for updates
echo "4/5: 检查版本更新..."
agent-reach check-update || true

# Step 5: Final status
echo "5/5: 安装完成！"
echo ""
echo "=== 后续配置 ==="
echo "某些渠道需要额外配置："
echo "  - Twitter 搜索: agent-reach configure twitter-cookies \"...\""
echo "  - 代理 (Reddit/Bilibili): agent-reach configure proxy http://... "
echo "  - 小宇宙播客: agent-reach configure groq-key gsk_xxx"
echo "  - 小红书: docker运行后 agent-reach configure xhs-cookies \"...\""
echo ""
echo "运行 'agent-reach doctor' 查看各渠道状态"