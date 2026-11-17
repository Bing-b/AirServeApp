import os
import sys
import time
import json
import shutil
import tempfile
import urllib.request
import socket
from main import Api, get_executable_path, is_port_available, find_available_port, load_config, save_config, BASE_PATH

def test_all():
    print("=== 开始 miniServerApp (AirServe) 全量自测 ===")
    tmp_root = tempfile.mkdtemp(prefix="airserve_test_")
    
    try:
        # 1. 测试内核路径探测
        print("[1/7] 测试 miniserve 内核探测...")
        exe_path = get_executable_path(BASE_PATH)
        assert exe_path is not None, "未探测到 miniserve 路径"
        assert os.path.exists(exe_path), f"miniserve 文件不存在: {exe_path}"
        print(f"  -> 内核路径正常: {exe_path}")

        # 2. 测试端口检测与自动避让逻辑
        print("[2/7] 测试端口可用性与避让算法...")
        # 占用一个临时端口
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            occupied_port = s.getsockname()[1]
            assert not is_port_available(occupied_port), f"端口 {occupied_port} 应被占用"
            next_avail = find_available_port(occupied_port)
            assert next_avail > occupied_port, f"自动避让应返回大于占用端口的新端口, got {next_avail}"
            assert is_port_available(next_avail), f"返回的新端口 {next_avail} 应当可用"
        print(f"  -> 端口占用与避让逻辑正常 (测试端口 {occupied_port} -> 避让至 {next_avail})")

        # 3. 测试目录校验与智能入口探测 (dist / build)
        print("[3/7] 测试目录校验与智能定位...")
        holder = {}
        api = Api(holder)
        # 禁用自动打开浏览器以便自动化测试
        api.open_browser = lambda p=None: None
        
        # 3.1 路径不存在
        res = api.start_server(os.path.join(tmp_root, "not_exist"), 8080, True)
        assert not res["success"] and "不存在" in res["message"]
        
        # 3.2 目录无 index.html
        empty_dir = os.path.join(tmp_root, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        res = api.start_server(empty_dir, 8080, True)
        assert not res["success"] and "未找到 index.html" in res["message"]
        
        # 3.3 包含 dist/index.html
        proj_dir = os.path.join(tmp_root, "my_project")
        dist_dir = os.path.join(proj_dir, "dist")
        os.makedirs(dist_dir, exist_ok=True)
        with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Dist Test</h1></body></html>")
        res = api.start_server(proj_dir, 8080, True)
        assert not res["success"] and res.get("suggest_dir") == os.path.normpath(dist_dir)
        print("  -> 智能定位 dist/ 成功")

        # 4. 测试启动 HTTP 服务、SPA 路由与缓存头
        print("[4/7] 测试 HTTP 静态服务与 SPA 路由...")
        site_dir = os.path.join(tmp_root, "site")
        os.makedirs(site_dir, exist_ok=True)
        with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Hello AirServe</h1></body></html>")
        with open(os.path.join(site_dir, "test.json"), "w", encoding="utf-8") as f:
            f.write('{"status":"ok"}')

        test_port = find_available_port(8200)
        start_res = api.start_server(site_dir, test_port, True)
        assert start_res["success"], f"服务启动失败: {start_res}"
        active_port = start_res["port"]
        
        # 验证 HTTP 响应与 SPA 行为
        time.sleep(0.6)
        base_url = f"http://127.0.0.1:{active_port}"
        
        # 首页
        with urllib.request.urlopen(f"{base_url}/") as r:
            body = r.read().decode("utf-8")
            assert "Hello AirServe" in body
            cc = r.headers.get("Cache-Control", "")
            assert "no-cache" in cc, f"缺少防缓存头: {cc}"

        # 静态文件
        with urllib.request.urlopen(f"{base_url}/test.json") as r:
            assert json.loads(r.read().decode("utf-8")) == {"status": "ok"}

        # SPA 路由 fallback 测试 (/dashboard/users 回退到 index.html)
        with urllib.request.urlopen(f"{base_url}/dashboard/users") as r:
            spa_body = r.read().decode("utf-8")
            assert "Hello AirServe" in spa_body, "SPA 路由回退未返回 index.html"

        print("  -> HTTP 服务响应、防缓存头、SPA 路由回退均完全正常")

        # 5. 测试服务停止与清理
        print("[5/7] 测试进程树销毁与端口释放...")
        stop_res = api.stop_server()
        assert stop_res["success"]
        time.sleep(0.5)
        assert is_port_available(active_port), f"服务停止后端口 {active_port} 应被释放"
        print("  -> 进程树正常终止，端口完全释放")

        # 6. 测试历史记录与持久化
        print("[6/7] 测试历史记录增删与清理...")
        hist_dir = os.path.normpath(site_dir)
        del_res = api.delete_history_item(hist_dir)
        assert hist_dir not in del_res["recent_dirs"]
        clear_res = api.clear_history()
        assert clear_res["recent_dirs"] == []
        print("  -> 历史记录增删改查正常")

        # 7. 测试 Windows 原生 C# 单文件 EXE 动态编译封包
        print("[7/7] 测试独立单文件 EXE 封包与编译 (csc.exe)...")
        if sys.platform == "win32":
            output_exe = os.path.join(tmp_root, "DemoExport.exe")
            export_res = api.export_standalone_exe(site_dir, output_exe, "自动化测试原型", 8300)
            assert export_res["success"], f"导出失败: {export_res.get('message')}"
            assert os.path.exists(output_exe), "未找到导出的 EXE 文件"
            file_size = os.path.getsize(output_exe)
            assert file_size > 1024 * 1024, f"导出的 EXE 文件大小异常: {file_size} 字节"
            print(f"  -> 单文件 EXE 编译成功! 产物大小: {file_size / (1024*1024):.2f} MB")

            # 运行编译出的 EXE 验证其实际可执行性与内置服务解压运行能力
            print("  -> 验证编译出的单文件 EXE 运行时自解压与服务响应...")
            import subprocess
            runner_proc = subprocess.Popen([output_exe])
            try:
                time.sleep(1.2)
                with urllib.request.urlopen("http://127.0.0.1:8300/") as r:
                    body = r.read().decode("utf-8")
                    assert "Hello AirServe" in body, "导出的 EXE 运行未返回预期的站点内容"
                print("  -> 导出的单文件 EXE 实测启动成功并正常提供 Web 服务！")
            finally:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(runner_proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.5)
        else:
            print("  -> 非 Windows 环境，跳过 csc 编译测试")

        print("\n🎉 === 全部 7 项功能自测圆满通过！ ===")

    finally:
        try:
            api.stop_server()
        except Exception:
            pass
        shutil.rmtree(tmp_root, ignore_errors=True)

if __name__ == "__main__":
    test_all()
