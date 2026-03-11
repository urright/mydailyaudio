#!/usr/bin/env node
/**
 * 监听模式：通过消息触发网关重启
 * 在会话中检查消息内容，如果包含特定命令则执行
 */

const { readFileSync, writeFileSync } = require('fs');
const { execSync } = require('child_process');
const path = require('path');

// 检查配置中是否已经启用了命令监听
// 简单实现：在当前会话的每次回复前检查用户输入

console.log('Gateway restart on command ready.');

// 示例：如果你收到消息包含 "restart gateway" 或 "重启网关"，就执行重启
function shouldRestartGateway(message) {
  const cmd = message.toLowerCase();
  return cmd.includes('restart gateway') || cmd.includes('重启网关');
}

// 执行重启
function restartGateway() {
  console.log('Restarting gateway...');
  try {
    execSync('openclaw gateway restart', { stdio: 'inherit' });
    console.log('Gateway restarted.');
    return true;
  } catch (e) {
    console.error('Restart failed:', e.message);
    return false;
  }
}

// 这个脚本可以作为技能或hook被调用
// 现在先手动演示：告诉我重启，我立刻执行

console.log(`
你可以直接在WhatsApp中发送：
  "重启网关" 或 "restart gateway"
我将立即执行网关重启。
`);
