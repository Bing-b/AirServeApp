import os
import sys
import platform
import subprocess
import threading
import webbrowser
import time
import socket
import json
import webview
import shutil
import tempfile
import uuid

# 确定运行时的基础路径
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# 配置文件路径（保存于用户主目录下）
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".airserve_config.json")
OLD_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".miniserve_config.json")


def load_config() -> dict:
    """读取本地持久化配置"""
    default_config = {
        "recent_dirs": [],
        "last_port": 8080,
        "auto_port": True
    }
    cfg_to_read = CONFIG_FILE if os.path.exists(CONFIG_FILE) else OLD_CONFIG_FILE
    if os.path.exists(cfg_to_read):
        try:
            with open(cfg_to_read, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_config.update(data)
        except Exception:
            pass
    return default_config


def save_config(config: dict):
    """保存配置到本地文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """检查指定端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int, max_tries: int = 50) -> int | None:
    """从 start_port 开始寻找下一个可用端口"""
    for p in range(start_port, min(65536, start_port + max_tries)):
        if is_port_available(p):
            return p
    return None


def get_executable_path(base_path: str) -> str | None:
    """获取对应平台的 miniserve 可执行文件路径"""
    sys_name = platform.system()
    if sys_name == "Windows":
        executable = "miniserve-win.exe"
        exe_path = os.path.join(base_path, "bin", executable)
        return exe_path if os.path.exists(exe_path) else None
    elif sys_name == "Darwin":
        arch = platform.machine().lower()
        if arch in ["arm64", "aarch64"]:
            candidates = ["miniserve-mac-arm64", "miniserve-mac-x64", "miniserve-osx", "miniserve"]
        else:
            candidates = ["miniserve-mac-x64", "miniserve-mac-arm64", "miniserve-osx", "miniserve"]

        for cand in candidates:
            p = os.path.join(base_path, "bin", cand)
            if os.path.exists(p):
                try:
                    os.chmod(p, 0o755)
                except Exception:
                    pass
                return p
        return None
    else:
        return None


class Api:
    """提供给前端 JS 调用的 API 接口"""
    def __init__(self, window_holder: dict):
        self.window_holder = window_holder
        self.server_process = None
        self.current_port = 8080
        self.config = load_config()

    def get_config(self) -> dict:
        """获取初始化配置"""
        self.config = load_config()
        recent = [d for d in self.config.get("recent_dirs", []) if os.path.exists(d)]
        return {
            "recent_dirs": recent,
            "last_port": self.config.get("last_port", 8080),
            "auto_port": self.config.get("auto_port", True)
        }

    def select_folder(self, initial_dir: str = "") -> str:
        """调用系统原生文件夹选择对话框"""
        window = self.window_holder.get("window")
        if not window:
            return ""
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        try:
            dialog_type = getattr(webview.FileDialog, 'FOLDER', webview.FOLDER_DIALOG) if hasattr(webview, 'FileDialog') else webview.FOLDER_DIALOG
            result = window.create_file_dialog(dialog_type, directory=initial_dir)
            if result and len(result) > 0:
                return os.path.normpath(result[0])
        except Exception as e:
            print("File dialog error:", e)
        return ""

    def save_file_dialog(self, default_name: str = "PrototypeDemo.exe") -> str:
        """调用系统原生保存文件对话框"""
        window = self.window_holder.get("window")
        if not window:
            return ""
        try:
            dialog_type = getattr(webview.FileDialog, 'SAVE', webview.SAVE_DIALOG) if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
            result = window.create_file_dialog(
                dialog_type,
                save_filename=default_name,
                file_types=('Executable (*.exe)', 'All files (*.*)')
            )
            if result:
                if isinstance(result, (list, tuple)) and len(result) > 0:
                    return os.path.normpath(result[0])
                elif isinstance(result, str):
                    return os.path.normpath(result)
        except Exception as e:
            print("Save file dialog error:", e)
        return ""

    def export_standalone_exe(self, target_dir: str, save_path: str, project_name: str, port: int) -> dict:
        """一键封包生成独立的单文件 EXE 原型演示程序"""
        target_dir = os.path.normpath(target_dir.strip())
        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            return {"success": False, "message": "静态文件目录不存在！"}

        index_file = os.path.join(target_dir, "index.html")
        if not os.path.exists(index_file):
            return {"success": False, "message": "所选目录中未包含 index.html 入口文件！"}

        if not save_path:
            return {"success": False, "message": "未指定导出保存路径！"}

        save_path = os.path.normpath(save_path.strip())
        if not save_path.lower().endswith(".exe"):
            save_path += ".exe"

        project_name = project_name.strip() or "原型演示"
        try:
            port = int(port)
        except Exception:
            port = 8080

        # 创建独立临时构建沙箱
        build_id = uuid.uuid4().hex[:8]
        build_tmp = os.path.join(tempfile.gettempdir(), f"miniserve_export_{build_id}")
        os.makedirs(build_tmp, exist_ok=True)

        try:
            # 1. 复制 runner_template 并注入参数
            template_path = os.path.join(BASE_PATH, "runner_template.py")
            if not os.path.exists(template_path):
                return {"success": False, "message": "找不到 runner_template.py 模板文件！"}

            with open(template_path, "r", encoding="utf-8") as f:
                runner_code = f.read()

            runner_code = runner_code.replace('PROJECT_NAME = "项目原型演示"', f'PROJECT_NAME = {repr(project_name)}')
            runner_code = runner_code.replace('DEFAULT_PORT = 8080', f'DEFAULT_PORT = {port}')

            runner_target = os.path.join(build_tmp, "runner.py")
            with open(runner_target, "w", encoding="utf-8") as f:
                f.write(runner_code)

            # 2. 复制 bin 目录
            bin_target = os.path.join(build_tmp, "bin")
            os.makedirs(bin_target, exist_ok=True)
            miniserve_src = get_executable_path(BASE_PATH)
            if not miniserve_src or not os.path.exists(miniserve_src):
                return {"success": False, "message": "找不到 miniserve 内核可执行程序！"}
            shutil.copy2(miniserve_src, os.path.join(bin_target, os.path.basename(miniserve_src)))

            # 3. 复制静态文件目录为 site
            site_target = os.path.join(build_tmp, "site")
            shutil.copytree(target_dir, site_target, dirs_exist_ok=True)

            # 4. 复制图标
            ico_src = os.path.join(BASE_PATH, "gui", "logo.ico")
            if not os.path.exists(ico_src):
                ico_src = os.path.join(BASE_PATH, "logo.ico")
            ico_target = os.path.join(build_tmp, "logo.ico")
            if os.path.exists(ico_src):
                shutil.copy2(ico_src, ico_target)

            # 5. 调用 PyInstaller 执行单文件构建
            pyinstaller_cmd = [
                sys.executable, "-m", "PyInstaller",
                "-y",
                "-F",
                "-w",
                "--clean",
                "--name", "demo_bundle",
                "--add-data", f"{bin_target};bin",
                "--add-data", f"{site_target};site",
            ]
            if os.path.exists(ico_target):
                pyinstaller_cmd.extend(["--icon", ico_target])
            pyinstaller_cmd.append(runner_target)

            creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            proc = subprocess.run(
                pyinstaller_cmd,
                cwd=build_tmp,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            if proc.returncode != 0:
                return {"success": False, "message": f"构建失败:\n{proc.stderr[:300]}"}

            dist_exe = os.path.join(build_tmp, "dist", "demo_bundle.exe")
            if not os.path.exists(dist_exe):
                return {"success": False, "message": "打包成功但未找到输出产物！"}

            # 6. 将生成的 exe 移动至用户指定的保存路径
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            if os.path.exists(save_path):
                os.remove(save_path)
            shutil.move(dist_exe, save_path)

            # 7. 自动在 Windows 资源管理器中选中高亮生成的文件
            if platform.system() == "Windows":
                try:
                    subprocess.Popen(f'explorer /select,"{os.path.abspath(save_path)}"')
                except Exception:
                    pass

            return {
                "success": True,
                "message": f"独立演示程序导出成功！",
                "output_path": save_path
            }

        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            try:
                shutil.rmtree(build_tmp, ignore_errors=True)
            except Exception:
                pass

    def delete_history_item(self, directory: str) -> dict:
        """删除指定的一条历史目录"""
        norm_dir = os.path.normpath(directory.strip())
        recent = self.config.get("recent_dirs", [])
        if norm_dir in recent:
            recent.remove(norm_dir)
        self.config["recent_dirs"] = recent
        save_config(self.config)
        return {"success": True, "recent_dirs": recent}

    def clear_history(self) -> dict:
        """清空所有历史目录"""
        self.config["recent_dirs"] = []
        save_config(self.config)
        return {"success": True, "recent_dirs": []}

    def start_server(self, target_dir: str, port: int, auto_port: bool) -> dict:
        """启动静态文件服务"""
        if self.server_process:
            self.stop_server()

        target_dir = os.path.normpath(target_dir.strip())
        if not os.path.exists(target_dir):
            return {"success": False, "message": f"目录不存在:\n{target_dir}"}

        if not os.path.isdir(target_dir):
            return {"success": False, "message": f"所选路径不是有效文件夹:\n{target_dir}"}

        # 检查目录下是否存在 index.html 入口文件
        index_file = os.path.join(target_dir, "index.html")
        if not os.path.exists(index_file):
            # 智能检测：是否在 dist 或 build 子目录下
            dist_index = os.path.join(target_dir, "dist", "index.html")
            build_index = os.path.join(target_dir, "build", "index.html")
            if os.path.exists(dist_index):
                return {
                    "success": False,
                    "message": "当前目录未包含 index.html，已自动为您定位到子目录 dist！请再次点击启动。",
                    "suggest_dir": os.path.normpath(os.path.join(target_dir, "dist"))
                }
            elif os.path.exists(build_index):
                return {
                    "success": False,
                    "message": "当前目录未包含 index.html，已自动为您定位到子目录 build！请再次点击启动。",
                    "suggest_dir": os.path.normpath(os.path.join(target_dir, "build"))
                }
            else:
                return {
                    "success": False,
                    "message": "所选文件夹内未找到 index.html 入口文件！请选择包含 index.html 的静态目录。"
                }

        try:
            port = int(port)
            if not (1 <= port <= 65535):
                return {"success": False, "message": "端口号必须在 1-65535 之间"}
        except ValueError:
            return {"success": False, "message": "端口号必须为整数"}

        port_switched = False
        if not is_port_available(port):
            if auto_port:
                next_port = find_available_port(port + 1)
                if next_port:
                    port = next_port
                    port_switched = True
                else:
                    return {"success": False, "message": f"端口 {port} 及后续端口均被占用"}
            else:
                return {"success": False, "message": f"端口 {port} 已被占用，请更换端口"}

        exe_path = get_executable_path(BASE_PATH)
        if not exe_path:
            return {"success": False, "message": "找不到 bin 目录下的 miniserve 服务程序！"}

        self.current_port = port

        try:
            cmd = [
                exe_path,
                "--index", "index.html",
                "--spa",
                "--port", str(port),
                "--header", "Cache-Control: no-cache, no-store, must-revalidate",
                "--header", "Pragma: no-cache",
                "--header", "Expires: 0",
                target_dir
            ]

            creationflags = 0
            if platform.system() == "Windows":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )

            # 异步消费子进程管道避免阻塞
            def drain(stream):
                try:
                    while stream and not stream.closed:
                        line = stream.readline()
                        if not line:
                            break
                except Exception:
                    pass

            threading.Thread(target=drain, args=(self.server_process.stdout,), daemon=True).start()
            threading.Thread(target=drain, args=(self.server_process.stderr,), daemon=True).start()

            # 记录历史目录
            recent = self.config.get("recent_dirs", [])
            if target_dir in recent:
                recent.remove(target_dir)
            recent.insert(0, target_dir)
            self.config["recent_dirs"] = recent[:10]
            self.config["last_port"] = port
            self.config["auto_port"] = auto_port
            save_config(self.config)

            # 自动在默认浏览器中打开页面
            self.open_browser(port)

            return {
                "success": True,
                "port": port,
                "port_switched": port_switched,
                "recent_dirs": self.config["recent_dirs"]
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def stop_server(self) -> dict:
        """彻底停止静态文件服务并销毁子进程树"""
        if self.server_process:
            kill_process_tree(self.server_process)
            self.server_process = None
        return {"success": True}

    def open_browser(self, port: int = None):
        """在系统浏览器中打开当前服务"""
        p = port or self.current_port
        url = f"http://127.0.0.1:{p}/?t={int(time.time())}"
        webbrowser.open(url)


def kill_process_tree(proc):
    """跨平台强制终结进程树，防止后台残留孤儿进程"""
    if not proc:
        return
    try:
        pid = proc.pid
        if platform.system() == "Windows":
            # Windows 下递归强制杀死进程树 (/F 强制, /T 递归子进程)
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


def set_window_icon():
    """在 Windows 下为原生窗口设置 logo 图标"""
    if platform.system() != "Windows":
        return

    import ctypes
    time.sleep(0.3)  # 等待窗口句柄创建完成
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "AirServe")
        if hwnd:
            ico_path = os.path.abspath(os.path.join(BASE_PATH, "gui", "logo.ico"))
            if not os.path.exists(ico_path):
                ico_path = os.path.abspath(os.path.join(BASE_PATH, "logo.ico"))

            if os.path.exists(ico_path):
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1

                h_icon_big = user32.LoadImageW(None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                h_icon_small = user32.LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

                if h_icon_big:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
                if h_icon_small:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
    except Exception as e:
        print("Set window icon error:", e)


def main():
    import atexit
    window_holder = {}
    api = Api(window_holder)
    html_path = os.path.join(BASE_PATH, "gui", "index.html")

    # 注册程序退出钩子，确保任意异常退出均能销毁 miniserve 进程
    atexit.register(api.stop_server)

    window = webview.create_window(
        title="AirServe",
        url=html_path,
        js_api=api,
        width=590,
        height=488,
        resizable=False,
        text_select=False
    )
    window_holder["window"] = window

    def on_closing():
        api.stop_server()

    def on_shown():
        # 后台线程设置窗口原生图标
        threading.Thread(target=set_window_icon, daemon=True).start()

    window.events.closing += on_closing
    window.events.closed += on_closing
    webview.start(func=on_shown, debug=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("crash.log", "w") as f:
            f.write(traceback.format_exc())


