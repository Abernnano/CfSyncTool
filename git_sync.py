#!/usr/bin/env python3

import os
import subprocess
import sys

# 颜色设置
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding="utf-8")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{YELLOW}命令执行失败: {e}{RESET}")
        print(f"{YELLOW}错误输出: {e.stderr}{RESET}")
        return None
    except UnicodeDecodeError:
        # 尝试使用 GBK 编码
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding="gbk")
            return result.stdout
        except Exception as e:
            print(f"{YELLOW}命令执行失败: {e}{RESET}")
            return None

def check_git_installed():
    """检查 Git 是否安装"""
    result = run_command("git --version")
    if result:
        print(f"{GREEN}Git 已安装: {result.strip()}{RESET}")
        return True
    else:
        print(f"{YELLOW}错误: Git 未安装，请先安装 Git{RESET}")
        return False

def init_git_repo():
    """初始化 Git 仓库"""
    if not os.path.exists(".git"):
        print(f"{YELLOW}初始化 Git 仓库...{RESET}")
        result = run_command("git init")
        if result:
            print(f"{GREEN}Git 仓库初始化成功{RESET}")
        else:
            print(f"{YELLOW}Git 仓库初始化失败{RESET}")
            return False
    else:
        print(f"{GREEN}Git 仓库已存在{RESET}")
    return True

def create_gitignore():
    """创建 .gitignore 文件"""
    if not os.path.exists(".gitignore"):
        print(f"{YELLOW}创建 .gitignore 文件...{RESET}")
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
        print(f"{GREEN}.gitignore 文件创建成功{RESET}")
    else:
        print(f"{GREEN}.gitignore 文件已存在{RESET}")

def create_readme():
    """创建 README.md 文件"""
    if not os.path.exists("README.md"):
        print(f"{YELLOW}创建 README.md 文件...{RESET}")
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
        print(f"{GREEN}README.md 文件创建成功{RESET}")
    else:
        print(f"{GREEN}README.md 文件已存在{RESET}")

def add_and_commit():
    """添加文件并提交"""
    print(f"{CYAN}添加文件到暂存区...{RESET}")
    result = run_command("git add .")
    if result is None:
        return False
    
    print(f"{CYAN}提交更改...{RESET}")
    result = run_command('git commit -m "初始化项目"')
    if result is None:
        print(f"{YELLOW}提交失败，可能没有更改{RESET}")
    else:
        print(f"{GREEN}提交成功{RESET}")
    return True

def setup_remote_repo():
    """设置远程仓库"""
    repo_url = "https://github.com/Abernnano/CfSyncTool.git"
    print(f"{CYAN}添加远程仓库: {repo_url}{RESET}")
    
    # 检查是否已存在远程仓库
    result = run_command("git remote -v")
    if "origin" in result:
        print(f"{YELLOW}远程仓库已存在，更新远程仓库 URL...{RESET}")
        result = run_command(f"git remote set-url origin {repo_url}")
    else:
        result = run_command(f"git remote add origin {repo_url}")
    
    if result is None:
        return False
    print(f"{GREEN}远程仓库设置成功{RESET}")
    return True

def push_to_github():
    """推送代码到 GitHub"""
    print(f"{CYAN}推送代码到 GitHub...{RESET}")
    result = run_command("git branch -M main")
    if result is None:
        return False
    
    print(f"{YELLOW}注意: GitHub 不再支持密码认证，需要使用个人访问令牌 (PAT){RESET}")
    print(f"{YELLOW}请按照以下步骤操作: {RESET}")
    print(f"{YELLOW}1. 登录 GitHub 账号{RESET}")
    print(f"{YELLOW}2. 进入 Settings > Developer settings > Personal access tokens{RESET}")
    print(f"{YELLOW}3. 创建一个新的令牌，选择 'repo' 权限{RESET}")
    print(f"{YELLOW}4. 复制生成的令牌{RESET}")
    print(f"{YELLOW}5. 当 Git 提示输入密码时，粘贴令牌作为密码{RESET}")
    
    # 尝试推送
    result = run_command("git push -u origin main")
    if result is None:
        print(f"{YELLOW}推送失败，请手动执行以下命令: {RESET}")
        print(f"{YELLOW}git push -u origin main{RESET}")
        return False
    print(f"{GREEN}代码推送成功{RESET}")
    return True

def main():
    """主函数"""
    print(f"{GREEN}=== CloudflareSyncTool Git 同步脚本 ==={RESET}")
    print(f"{CYAN}开始执行脚本...{RESET}")
    
    # 检查 Git 是否安装
    if not check_git_installed():
        sys.exit(1)
    
    # 初始化 Git 仓库
    if not init_git_repo():
        sys.exit(1)
    
    # 创建必要的文件
    create_gitignore()
    create_readme()
    
    # 添加并提交文件
    if not add_and_commit():
        sys.exit(1)
    
    # 设置远程仓库
    if not setup_remote_repo():
        sys.exit(1)
    
    # 推送代码到 GitHub
    if not push_to_github():
        sys.exit(1)
    
    print(f"{GREEN}同步完成！项目已成功上传到 GitHub{RESET}")
    print(f"{GREEN}仓库地址: https://github.com/Abernnano/CfSyncTool.git{RESET}")

if __name__ == "__main__":
    main()
