<div align="center">

  <img src="gui/logo.png" alt="AirServe Logo" width="96" height="96" style="border-radius: 22px; margin-bottom: 12px;" />

  # AirServe

  **极简、优雅的本地原型交付与静态 Web 服务工具**
  
  *Apple 设计美学 · 零依赖即开即用 · 一键导出单文件独立原型 EXE*

  <p align="center">
    <a href="https://github.com/Bing-b/AirServerApp/releases"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-007AFF?style=flat-square&logo=apple" alt="Platform"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://pywebview.flowrl.com/"><img src="https://img.shields.io/badge/GUI-PyWebView%205.0-34C759?style=flat-square" alt="GUI"></a>
    <a href="https://github.com/svenstaro/miniserve"><img src="https://img.shields.io/badge/Core-Miniserve%20Rust-DEA584?style=flat-square&logo=rust" alt="Miniserve"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License"></a>
  </p>

</div>

---

## 📸 应用预览 (Screenshot)

<div align="center">
  <img src="airServer.png" alt="AirServe 软件界面截图" width="700" style="border-radius: 12px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15); margin: 16px 0;" />
</div>

---

## 💡 为什么选择 AirServe？

在日常研发与产品交付场景中，产品经理、UI/UX 设计师或前端工程师经常需要向客户、领导或投资人演示 **AI 生成的原型、Vite/React/Vue 构建产物或 Axure HTML**。

传统方式面临诸多痛点：
- ❌ 客户电脑没有 Node.js / Python 环境，无法启动本地服务器；
- ❌ 直接用浏览器双击 `index.html` 会触发跨域（CORS）与路由失效（SPA 404）；
- ❌ 发给客户一个包含成百上千碎文件的 zip 压缩包，客户容易解压错或找不到入口；
- ❌ 命令行工具界面粗糙、缺少按压反馈，易发生端口冲突或后台残留孤儿进程。

**AirServe 为此而生**：它不仅是一款拥有 **macOS 级毛玻璃质感**的本地轻量服务器，更是一套专为**高保真原型交付**设计的桌面工具。

---

## ✨ 核心特性

| 功能特性 | 说明 |
| :--- | :--- |
| 🍎 **苹果级原生质感 UI** | 遵循 Apple 设计语言，支持浅色/深色主题、真实背景高斯模糊 (`Backdrop Blur`) 与微交互弹性动画。 |
| 📦 **一键导出单文件独立 EXE** | 选定静态目录，**1 秒生成完全独立的单文件 `.exe`**。客户电脑无需安装任何环境，双击直接运行并自动弹出浏览器演示。 |
| 🎮 **智能二合一主控 (Scheme A)** | 宽幅呼吸发光主控按钮，启动后平滑形变为停止态，并自动滑出次级 `🔄` 一键重启按钮。 |
| 🔌 **智能端口冲突检测** | 自由设定端口；若目标端口被占用，支持**智能毫秒级自动递增切换**至空闲端口，彻底告别冲突。 |
| 🕒 **历史路径记忆与精准管理** | 自动记录历史使用目录，支持下拉列表一键切换、单条精准删除 (`×`) 与一键彻底清空。 |
| 🛡️ **入口文件校验与智能定位** | 启动前自动检查 `index.html`；若用户误选项目根目录，将自动探测并修正为 `dist/` 或 `build/` 子路径。 |
| 🌐 **Safari 风格地址胶囊** | 集成带呼吸脉冲的实时状态指示、一键复制访问链接与快速直达浏览器。 |
| ⚡ **SPA 单页应用原生支持** | 默认开启 `--spa` 路由回退并内置强效防缓存请求头，完美适配 Vue Router / React Router。 |
| 🧹 **全生命周期进程安全** | 绑定窗口关闭事件与全局退出钩子，退出时递归销毁子进程树 (`taskkill /F /T`)，绝无后台残留。 |

---

## 🎯 典型场景：产品经理原型交付工作流

```mermaid
graph LR
    A[AI 生成原型 / 前端构建] --> B[选定 dist 静态目录]
    B --> C[点击 '📦 导出独立 EXE']
    C --> D[生成 某某项目原型.exe]
    D --> E[发给客户 / 投资人]
    E --> F[客户双击秒开体验]
```

1. **导出**：产品经理选择包含 `index.html` 的原型目录，点击 **“📦 导出独立 EXE”**。
2. **交付**：将生成的单个 `.exe` 文件（如 `智慧园区原型演示.exe`）通过微信/邮件直接发送给客户。
3. **演示**：客户双击运行，程序自动拉起微服务并在默认浏览器中加载页面；关闭控制框自动退出，零系统残留。

---

## 🚀 快速开始

### 源码运行

1. **克隆仓库**：
   ```bash
   git clone https://github.com/Bing-b/AirServerApp.git
   cd AirServerApp
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **启动程序**：
   ```bash
   python main.py
   ```

---

## 📦 独立客户端打包

项目内置了针对 Windows 与 macOS 的一键全量打包脚本：

### 🪟 Windows (.exe)：
```cmd
build_win.bat
```
构建产物位于 `dist/AirServe.exe`，免安装直接运行。

### 🍎 macOS (.app)：
```bash
chmod +x build_mac.sh && ./build_mac.sh
```
构建产物位于 `dist/AirServe.app`，适配 Apple Silicon (M系列) 与 Intel 芯片。

---

## 🛠️ 技术架构

- **GUI 渲染容器**：[PyWebView 5.0+](https://pywebview.flowrl.com/)（调用系统原生 Edge WebView2 / macOS WebKit，无需打包笨重 Chromium）
- **UI 前端界面**：HTML5 + Modern Vanilla CSS3（无第三方打包体积开销）
- **高性能服务内核**：[Miniserve](https://github.com/svenstaro/miniserve)（Rust 高性能轻量静态服务器）
- **跨平台独立封包引擎**：PyInstaller 6.0+ 单文件沙盒打包技术

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源发布。
