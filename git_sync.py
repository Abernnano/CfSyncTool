#!/usr/bin/env python3
# Git操作辅助脚本
# 用于CloudflareSyncTool项目的版本控制
# 参考git_helper.py的结构，使用菜单方式操作

import os
import subprocess
import sys

# 颜色设置
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"

# 远程仓库地址
REMOTE_URL = "https://github.com/Abernnano/CfSyncTool.git"

def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if e.stderr:
            try:
                print(f'{YELLOW}错误: {e.stderr.strip()}{RESET}')
            except:
                print(f'{YELLOW}错误: 命令执行失败{RESET}')
        else:
            print(f'{YELLOW}错误: 命令执行失败{RESET}')
        return None
    except Exception as e:
        print(f'{YELLOW}错误: {e}{RESET}')
        return None

def check_git_installed():
    """检查Git是否安装"""
    result = run_command("git --version")
    if result:
        print(f"{GREEN}Git 已安装: {result}{RESET}")
        return True
    else:
        print(f"{YELLOW}错误: Git 未安装，请先安装 Git{RESET}")
        return False

def init_git_repo():
    """初始化Git仓库"""
    if not os.path.exists(".git"):
        print(f"{YELLOW}初始化 Git 仓库...{RESET}")
        result = run_command("git init")
        if result:
            print(f"{GREEN}Git 仓库初始化成功{RESET}")
            return True
        else:
            print(f"{YELLOW}Git 仓库初始化失败{RESET}")
            return False
    else:
        print(f"{GREEN}Git 仓库已存在{RESET}")
        return True

def create_gitignore():
    """创建.gitignore文件"""
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
    """创建README.md文件"""
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
    # 先检查是否有更改
    status_result = run_command('git status')
    if status_result and 'nothing to commit' in status_result:
        print(f'{YELLOW}没有可提交的更改！{RESET}')
        return None
    
    message = input('请输入提交信息: ')
    if not message:
        print(f'{YELLOW}提交信息不能为空！{RESET}')
        return None
    
    print(f"{CYAN}添加更改...{RESET}")
    if run_command("git add .") is None:
        return None
    
    print(f"{CYAN}提交更改: {message}{RESET}")
    result = run_command(f"git commit -m '{message}'")
    if result is not None:
        print(f"{GREEN}提交成功{RESET}")
    return result

def setup_remote_repo():
    """设置远程仓库"""
    print(f"{CYAN}添加远程仓库: {REMOTE_URL}{RESET}")
    
    # 检查是否已存在远程仓库
    result = run_command("git remote -v")
    if "origin" in result:
        print(f"{YELLOW}远程仓库已存在，更新远程仓库 URL...{RESET}")
        result = run_command(f"git remote set-url origin {REMOTE_URL}")
    else:
        result = run_command(f"git remote add origin {REMOTE_URL}")
    
    if result is None:
        return False
    print(f"{GREEN}远程仓库设置成功{RESET}")
    return True

def push_to_github():
    """推送代码到GitHub"""
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

def pull_from_github():
    """从GitHub拉取代码"""
    print(f"{CYAN}拉取最新代码...{RESET}")
    result = run_command("git pull origin main")
    if result is not None:
        print(f"{GREEN}拉取完成！{RESET}")
    return result

def check_status():
    """查看Git状态"""
    print(f"{CYAN}查看当前状态...{RESET}")
    result = run_command("git status")
    if result is not None:
        print(result)
    return result

def view_log():
    """查看提交历史"""
    print(f"{CYAN}查看提交历史...{RESET}")
    result = run_command("git log --oneline")
    if result is not None:
        print(result)
    return result

def menu():
    """显示菜单"""
    print(f'\n{GREEN}=== CloudflareSyncTool Git 同步脚本 ==={RESET}')
    print('请选择要执行的操作:')
    print('1. 检查Git安装状态')
    print('2. 初始化Git仓库')
    print('3. 创建.gitignore文件')
    print('4. 创建README.md文件')
    print('5. 添加并提交更改')
    print('6. 设置远程仓库')
    print('7. 推送代码到GitHub')
    print('8. 从GitHub拉取代码')
    print('9. 查看Git状态')
    print('10. 查看提交历史')
    print('0. 退出')

def main():
    """主函数"""
    while True:
        menu()
        try:
            choice = int(input('请输入数字选择操作: '))
        except ValueError:
            print(f'{YELLOW}请输入有效的数字！{RESET}')
            continue
        
        if choice == 0:
            print(f'{GREEN}退出脚本...{RESET}')
            break
        elif choice == 1:
            check_git_installed()
        elif choice == 2:
            init_git_repo()
        elif choice == 3:
            create_gitignore()
        elif choice == 4:
            create_readme()
        elif choice == 5:
            add_and_commit()
        elif choice == 6:
            setup_remote_repo()
        elif choice == 7:
            push_to_github()
        elif choice == 8:
            pull_from_github()
        elif choice == 9:
            check_status()
        elif choice == 10:
            view_log()
        else:
            print(f'{YELLOW}无效的选择，请重新输入！{RESET}')
        
        input('\n按回车键继续...')

if __name__ == "__main__":
    main()
