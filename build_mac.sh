#!/bin/bash
set -e

echo "========================================"
echo "  Building AirServe for macOS (.app)"
echo "========================================"

# 1. 确保安装基础依赖及 macOS PyWebView 所需的 Cocoa/WebKit 绑定
echo "1. Installing Python dependencies..."
python3 -m pip install -r requirements.txt
python3 -m pip install pyobjc-framework-WebKit pyobjc-framework-Cocoa 2>/dev/null || true

# 2. 赋予 bin 目录下二进制可执行权限
echo ""
echo "2. Setting executable permissions for miniserve binaries..."
chmod +x bin/miniserve* 2>/dev/null || true

# 3. 执行 PyInstaller 打包构建为原生 .app 独立包
echo ""
echo "3. Building AirServe.app with PyInstaller..."
ICON_PARAM=""
if [ -f "logo.icns" ]; then
    ICON_PARAM="--icon=logo.icns"
elif [ -f "gui/logo.png" ]; then
    ICON_PARAM="--icon=gui/logo.png"
fi

python3 -m PyInstaller -y -w \
    --name "AirServe" \
    $ICON_PARAM \
    --add-data "bin:bin" \
    --add-data "gui:gui" \
    --osx-bundle-identifier "com.airserve.app" \
    main.py

echo ""
echo "========================================"
echo "  Build complete! Output: dist/AirServe.app"
echo "========================================"
