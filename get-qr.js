#!/usr/bin/env node
const qrcode = require('qrcode');
const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const workspaceDir = '/home/jeremy/.openclaw/workspace';
const outputPath = path.join(workspaceDir, 'whatsapp-qr.png');

console.log('Starting WhatsApp login to get QR code...');

// 尝试获取二维码数据
// 方法：运行 openclaw channels login 并等待它输出二维码
// 但我们需要捕获二维码文本，然后转成图片

// 先终止任何现有的进程
try {
  execSync('pkill -f "openclaw channels login"', { stdio: 'ignore' });
} catch (e) {}

// 启动登录，捕获输出
const proc = spawn('openclaw', ['channels', 'login', '--channel', 'whatsapp'], {
  stdio: ['ignore', 'pipe', 'pipe'],
});

let qrText = '';
let inQrSection = false;

proc.stdout.on('data', (data) => {
  const text = data.toString();
  process.stdout.write(text); // 同时输出到控制台

  // 检测二维码开始
  if (text.includes('Scan this QR in WhatsApp')) {
    inQrSection = true;
  }

  // 如果进入二维码区域，收集行
  if (inQrSection) {
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.includes('▄') || line.includes('█')) {
        qrText += line + '\n';
      }
      if (line.includes('Waiting for WhatsApp connection')) {
        // 结束标记
        break;
      }
    }
  }
});

proc.stderr.on('data', (data) => {
  process.stderr.write(data);
});

// 等待几秒让二维码生成
setTimeout(() => {
  proc.kill('SIGTERM');

  if (qrText && qrText.includes('▄')) {
    console.log('\n✓ QR code text captured. Generating PNG...');

    // 将ASCII艺术转换为二维码数据是比较复杂的
    // 更简单：直接用Dashboard，或者让用户访问Dashboard
    console.log('\n二维码字符画已捕获。但自动转PNG较复杂。');
    console.log('建议：访问 Dashboard 查看二维码图片:');
    console.log('http://127.0.0.1:18790/\n');

    // 将字符画保存为文本文件作为备用
    fs.writeFileSync(path.join(workspaceDir, 'whatsapp-qr.txt'), qrText);
    console.log(`字符画已保存到: ${path.join(workspaceDir, 'whatsapp-qr.txt')}`);
  } else {
    console.log('未能捕获二维码，请手动访问Dashboard');
  }
}, 10000);
