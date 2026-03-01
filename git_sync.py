#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

# 颜色设置
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_green(text):
    print(f"{Colors.GREEN}{text}{Colors.RESET}")

def print_yellow(text):
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")

def print_cyan(text):
    print(f"{Colors.CYAN}{text}{Colors.RESET}")

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_git():
    """检查 Git 是否安装"""
    code, _, _ = run_command("git --version")
    return code == 0

def init_git_repo():
    """初始化 Git 仓库"""
    if not os.path.exists(".git"):
        print_yellow("初始化 Git 仓库...")
        code, _, stderr = run_command("git init")
        if code != 0:
            print_yellow(f"初始化 Git 仓库失败: {stderr}")
            return False
    return True

def create_gitignore():
    """创建 .gitignore 文件"""
    if not os.path.exists(".gitignore"):
        print_yellow("创建 .gitignore 文件...")
        gitignore_content = """# 虚拟环境
.venv/

# 结果文件
*.csv
*.json

# 临时文件
*.tmp
*.temp

# 日志文件
*.log

# 可执行文件
*.exe
*.bat

# 配置文件
config_*.json
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

def create_readme():
    """创建 README.md 文件"""
    if not os.path.exists("README.md"):
        print_yellow("创建 README.md 文件...")
        readme_content = """# CloudflareSyncTool

Cloudflare IP同步工具，用于优化网络连接

## 功能
- 自动同步 Cloudflare IP 地址
- 提供 GUI 界面操作
- 支持 IPv4 和 IPv6
- 生成优化的 IP 列表

## 快速开始

### 环境要求
- Python 3.7+
- Windows 操作系统

### 使用方法
1. 运行 `CloudflareSyncGUI.py` 启动图形界面
2. 配置相关参数
3. 点击开始按钮进行 IP 同步

## 命令行工具
- `cfst_3proxy.bat` - 用于 3proxy 配置
- `cfst_hosts.bat` - 用于 hosts 文件配置

## 配置文件
- `config_v18_final.json` - 主要配置文件

## 注意事项
- 请确保网络连接正常
- 定期更新 IP 列表以获得最佳效果

## 许可证
MIT
"""
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

def add_and_commit():
    """添加文件到暂存区并提交"""
    print_cyan("添加文件到暂存区...")
    code, _, stderr = run_command("git add .")
    if code != 0:
        print_yellow(f"添加文件失败: {stderr}")
        return False

    print_cyan("提交更改...")
    code, _, stderr = run_command('git commit -m "初始化项目"')
    if code != 0:
        print_yellow(f"提交失败，可能没有更改: {stderr}")
    return True

def push_to_github():
    """推送代码到 GitHub"""
    print_yellow("请在 GitHub 上创建一个新的开源仓库，然后输入仓库 URL:")
    repo_url = input("GitHub 仓库 URL: ").strip()
    
    if not repo_url:
        print_yellow("仓库 URL 不能为空")
        return False

    print_cyan("添加远程仓库...")
    code, _, stderr = run_command(f"git remote add origin {repo_url}")
    if code != 0:
        print_yellow(f"添加远程仓库失败: {stderr}")
        return False

    print_cyan("推送代码到 GitHub...")
    code, _, stderr = run_command("git push -u origin master")
    if code != 0:
        print_yellow(f"推送失败，请检查网络连接和仓库权限: {stderr}")
        return False

    print_green(f"同步完成！项目已成功上传到 GitHub")
    print_green(f"仓库地址: {repo_url}")
    return True

def main():
    """主函数"""
    print_green("=== CloudflareSyncTool Git 同步脚本 ===")
    print_cyan("开始执行脚本...")

    # 检查 Git 是否安装
    if not check_git():
        print_yellow("错误: Git 未安装，请先安装 Git")
        sys.exit(1)

    # 初始化 Git 仓库
    if not init_git_repo():
        sys.exit(1)

    # 创建必要的文件
    create_gitignore()
    create_readme()

    # 添加并提交更改
    if not add_and_commit():
        sys.exit(1)

    # 推送代码到 GitHub
    if not push_to_github():
        sys.exit(1)

if __name__ == "__main__":
    main()
