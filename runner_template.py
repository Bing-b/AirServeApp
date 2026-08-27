import os
import sys
import time
import socket
import platform
import subprocess
import webbrowser
import threading

# 由构建器动态注入的元数据
PROJECT_NAME = "项目原型演示"
DEFAULT_PORT = 8080


def is_port_available(port: int, host: str = '127.0.0.1') -> bool:
    """检测指定端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 8080, max_tries: int = 50) -> int:
    """寻找可用端口"""
    for p in range(start_port, start_port + max_tries):
        if is_port_available(p):
            return p
    return start_port


def kill_process_tree(proc):
    """跨平台递归强制杀死进程"""
    if not proc:
        return
    try:
        pid = proc.pid
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            proc.terminate()
            proc.wait(timeout=1.0)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main():
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    site_dir = os.path.join(base_dir, "site")
    exe_name = "miniserve-win.exe" if platform.system() == "Windows" else "miniserve-osx"
    exe_path = os.path.join(base_dir, "bin", exe_name)

    if not os.path.exists(exe_path):
        # 兼容备用路径
        exe_path = os.path.join(base_dir, exe_name)

    if not os.path.exists(exe_path) or not os.path.exists(site_dir):
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "找不到内置的静态资源或服务程序！", "AirServe 错误", 0x10)
        else:
            print("Missing bundled assets or executable!")
        sys.exit(1)

    port = find_available_port(DEFAULT_PORT)
    cmd = [
        exe_path,
        "--index", "index.html",
        "--spa",
        "--port", str(port),
        "--header", "Cache-Control: no-cache, no-store, must-revalidate",
        site_dir
    ]

    creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags
    )

    # 异步消费管道
    def drain(stream):
        try:
            while stream and not stream.closed:
                if not stream.readline():
                    break
        except Exception:
            pass

    threading.Thread(target=drain, args=(server_process.stdout,), daemon=True).start()
    threading.Thread(target=drain, args=(server_process.stderr,), daemon=True).start()

    # 打开浏览器
    time.sleep(0.3)
    url = f"http://127.0.0.1:{port}/?t={int(time.time())}"
    webbrowser.open(url)

    # 弹出轻量控制提示框
    if platform.system() == "Windows":
        import ctypes
        msg = f"【{PROJECT_NAME}】原型演示服务运行中！\n\n" \
              f"🌐 访问地址：http://127.0.0.1:{port}\n\n" \
              f"提示：页面已在默认浏览器中打开。\n" \
              f"点击【确定】退出并停止本地服务。"
        ctypes.windll.user32.MessageBoxW(0, msg, f"AirServe - {PROJECT_NAME}", 0x00000040 | 0x00000000)
    else:
        try:
            input(f"【{PROJECT_NAME}】服务正在运行 (http://127.0.0.1:{port})，按 Enter 键退出...")
        except EOFError:
            time.sleep(999999)

    # 清理退出
    kill_process_tree(server_process)
    sys.exit(0)


if __name__ == "__main__":
    main()
