@echo off
echo ========================================
echo Building Windows Launcher (PyWebView)...
echo ========================================

echo 1. Installing dependencies...
py -m pip install -r requirements.txt

echo.
echo 2. Building with PyInstaller...
py -m PyInstaller -y -F -w --name "AirServe" --icon="logo.ico" --add-data "bin;bin" --add-data "gui;gui" main.py

echo.
echo ========================================
echo Build complete! Check the dist folder for AirServe.exe
echo ========================================
pause
