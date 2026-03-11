#!/usr/bin/env node

/**
 * 生成 WhatsApp 连接二维码图片
 * 步骤：
 * 1. 调用 openclaw agent RPC 启动登录，获取二维码字符串
 * 2. 将二维码数据转为图片
 * 3. 保存到工作区
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 工作区路径
const workspaceDir = '/home/jeremy/.openclaw/workspace';
const outputPath = path.join(workspaceDir, 'whatsapp-qr.png');

// 清理可能存在的旧会话
try {
  execSync('openclaw agent --to gw --message \'{"method":"web.login.start","params":{"channel":"whatsapp"}}\' --json', { stdio: 'pipe' });
} catch (e) {
  // 忽略错误，继续
}

console.log('Starting WhatsApp login...');

// 使用 openclaw channels login 的输出来获取二维码
// 但我们需要先确保没有残留的会话
// 尝试直接调用网关方法
const cmd = `openclaw agent --to gw --message '{"method":"web.login.start","params":{"channel":"whatsapp"}}' --json`;
console.log(`Running: ${cmd}`);

try {
  const result = execSync(cmd, { encoding: 'utf-8', maxBuffer: 1024 * 1024 });
  console.log('Result:', result);
} catch (e) {
  console.error('Error:', e.message);
}
