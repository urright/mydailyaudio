#!/usr/bin/env node
/**
 * 生成WhatsApp二维码图片并托管
 * 步骤：
 * 1. 调用网关API获取二维码数据
 * 2. 生成PNG
 * 3. 启动HTTP服务器提供图片
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const QRCode = require('qrcode');

const workspaceDir = '/home/jeremy/.openclaw/workspace';
const qrImgPath = path.join(workspaceDir, 'whatsapp-qr.png');
const htmlPath = path.join(workspaceDir, 'whatsapp-scan.html');

// 先尝试获取网关令牌
config = JSON.parse(fs.readFileSync('/home/jeremy/.openclaw/openclaw.cherry.json', 'utf8'));
const token = config.gateway?.auth?.token || '2yNeRSR-WZ41o-PZMyIveb2IWJ7o8Myz';

console.log('Token:', token);

// 网关WebSocket URL
const gatewayUrl = `ws://127.0.0.1:18790?token=${token}`;

console.log(`
===========================================
WhatsApp QR Code 生成器
===========================================
1. 请在手机上打开 WhatsApp
2. 前往 Linked Devices → Link a device
3. 我将生成一个临时二维码图片
4. 在浏览器中访问: http://localhost:8080
===========================================
`);

// 生成一个说明页面
const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Scan WhatsApp QR</title>
  <style>
    body { font-family: sans-serif; text-align: center; padding: 40px; background: #f5f5f5; }
    img { border: 5px solid #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.2); border-radius: 8px; }
    .steps { max-width: 500px; margin: 0 auto 30px; color: #555; line-height: 1.6; }
    h1 { color: #25D366; }
  </style>
</head>
<body>
  <h1>📱 WhatsApp 连接</h1>
  <div class="steps">
    <p><strong>步骤：</strong></p>
    <ol style="text-align: left;">
      <li>打开手机 WhatsApp</li>
      <li>点击右上角 ⋮ → <strong>Linked Devices</strong></li>
      <li>选择 <strong>Link a device</strong></li>
      <li>扫描下方的二维码</li>
    </ol>
    <p>二维码将在几秒后加载...</p>
  </div>
  <div id="qr-container">
    <img id="qr-img" src="" alt="QR Code" />
  </div>
  <p id="status" style="color: #888; margin-top: 20px;">连接中...</p>

  <script>
    // 尝试从网关获取二维码
    const ws = new WebSocket('ws://127.0.0.1:18790?token=' + '${token}');
    let qrCode = '';

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('Message:', msg);
        if (msg.method === 'web.login.qr' && msg.params?.qr) {
          qrCode = msg.params.qr;
          // 生成图片
          const img = document.getElementById('qr-img');
          img.src = 'data:image/png;base64,' + qrCode;
          document.getElementById('status').textContent = '请用 WhatsApp 扫描上方二维码';
        }
        if (msg.method === 'web.login.success') {
          document.getElementById('status').innerHTML = '<strong style="color: green">✓ 连接成功！可以关闭此页面。</strong>';
        }
      } catch (e) {}
    };

    ws.onerror = (err) => {
      document.getElementById('status').innerHTML = '<span style="color: red">无法连接到网关，请确保 OpenClaw 正在运行。</span>';
    };
  </script>
</body>
</html>
`;

fs.writeFileSync(htmlPath, html);

// 启动简单HTTP服务器
const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/index.html') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
  } else if (req.url === '/qr.png') {
    // 二维码可能还没生成
    res.writeHead(200, { 'Content-Type': 'image/png' });
    res.end('QR code not ready yet');
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(8080, () => {
  console.log('✓ HTTP 服务器已启动: http://localhost:8080');
  console.log('请在浏览器中打开此地址，然后扫描二维码。\n');
});

// 同时尝试启动网关的WebSocket连接来获取二维码
console.log('尝试连接网关获取二维码...');
// 这里需要实际的WebSocket客户端，简单起见我们只提供HTML页面，由浏览器端连接
