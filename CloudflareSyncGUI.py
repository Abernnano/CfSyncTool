import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import subprocess
import os
import threading
import csv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import sys
import time

# --- 路径自动化处理 ---
# 确保在打包成 EXE 后或直接运行脚本时，都能正确定位到当前目录
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置文件与输出文件路径
CONFIG_FILE = os.path.join(BASE_DIR, "config_v18_final.json")
EXPORT_CSV_FILE = os.path.join(BASE_DIR, "final_results_all.csv")
CFST_EXE = os.path.join(BASE_DIR, "CloudflareST.exe")

# --- 地区数据库 ---
# 用于将 Cloudflare 的三字码 (Colo) 转换为人类可读的城市名称
REGIONS_DATA = {
    "🌏 亚洲": {
        "HK": [("HKG", "香港")], 
        "TW": [("TPE", "台北"), ("KHH", "高雄")],
        "JP": [("NRT", "东京"), ("HND", "羽田"), ("KIX", "大阪")],
        "SG": [("SIN", "新加坡")], 
        "KR": [("ICN", "首尔")], 
        "TH": [("BKK", "曼谷")],
        "CN": [("CAN", "广州"), ("PEK", "北京"), ("SHA", "上海"), ("SZX", "深圳"), ("HGH", "杭州")]
    },
    "🇺🇸 北美": {
        "US": [("LAX", "洛杉矶"), ("SJC", "圣何塞"), ("SEA", "西雅图"), ("SFO", "旧金山"), ("ORD", "芝加哥")]
    },
    "🇪🇺 欧洲": {
        "DE": [("FRA", "法兰克福")], 
        "GB": [("LHR", "伦敦")], 
        "FR": [("CDG", "巴黎")], 
        "NL": [("AMS", "阿姆斯特丹")]
    }
}

# 反向查询字典：通过 'HKG' 查到 ('HK', '香港')
COLO_LOOKUP = {code: (cc, name) for cont, ccs in REGIONS_DATA.items() for cc, colos in ccs.items() for code, name in colos}

def get_flag_emoji(country_code):
    """根据国家代码返回国旗表情"""
    flags = {
        "HK": "🇭🇰", "TW": "🇹🇼", "CN": "🇨🇳", "JP": "🇯🇵", "KR": "🇰🇷", 
        "SG": "🇸🇬", "US": "🇺🇸", "CA": "🇨🇦", "DE": "🇩🇪", "GB": "🇬🇧", 
        "FR": "🇫🇷", "NL": "🇳🇱", "TH": "🇹🇭"
    }
    return flags.get(country_code.upper(), "🌐")

class CFSTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CloudflareST Pro v19.6 (API 推送规范版)")
        self.root.geometry("1300x950")
        
        # --- 网络请求会话配置 ---
        # 针对 10054 等连接重置错误，配置自动重试机制
        self.session = requests.Session()
        retry = Retry(
            total=5, 
            backoff_factor=1, 
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({
            "User-Agent": "CfSyncTool/19.6",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        self.last_results = []  # 存储最近一次测速结果
        self.targets = []       # 推送目标列表
        self.selected_colos = set() # 用户选中的数据中心代码
        
        self.load_config()      # 加载配置
        self.setup_ui()        # 初始化界面

    def load_config(self):
        """从 JSON 文件加载用户配置，若无则使用默认值"""
        self.default_targets = [
            {
                "name": "Abern9-API同步", 
                "url": "https://你的域名/UUID/api/preferred-ips", 
                "mode": "JSON", 
                "push_type": "OVERWRITE", 
                "template": "{flag} {country}_{colo}_{speed}MB", 
                "separator": ",", 
                "active": True
            },
            {
                "name": "LiamZZR-KV推送", 
                "url": "https://cf-ip-provider.liamzzr9.dpdns.org/?key=357159", 
                "mode": "TEXT", 
                "push_type": "OVERWRITE", 
                "template": "{ip}:{port}#{flag} {country}_{colo}_{speed}", 
                "separator": "\\n", 
                "active": True
            }
        ]
        self.default_params = {
            "n": "200", "t": "4", "dn": "50", "dt": "5", "tp": "443", 
            "url": "https://cf.xiu2.xyz/url", "tl": "500", "sl": "2", 
            "ipc": "8", "remote_url": "", "ip_file": "ip.txt", 
            "ipv6": False, "selected_colos_list": ["SJC", "SEA", "SIN", "HKG"]
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.targets = cfg.get("targets", self.default_targets)
                    self.params = cfg.get("params", self.default_params)
                    self.selected_colos = set(self.params.get("selected_colos_list", []))
            except:
                self.targets = self.default_targets
                self.params = self.default_params
        else:
            self.targets = self.default_targets
            self.params = self.default_params

    def save_config(self):
        """将当前界面上的参数保存到配置文件"""
        self.params = {
            "n": self.ent_n.get(), "t": self.ent_t.get(), "dn": self.ent_dn.get(), 
            "dt": self.ent_dt.get(), "tp": self.ent_tp.get(), "url": self.ent_url.get(), 
            "tl": self.ent_tl.get(), "sl": self.ent_sl.get(), "ipc": self.ent_ipc.get(), 
            "remote_url": self.ent_remote.get(), "ip_file": self.ent_file.get(), 
            "ipv6": self.v6_var.get(), "selected_colos_list": list(self.selected_colos)
        }
        # 更新推送目标的激活状态
        for i, t in enumerate(self.targets):
            if i < len(self.target_vars):
                t['active'] = self.target_vars[i].get()
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"targets": self.targets, "params": self.params}, f, indent=4, ensure_ascii=False)

    def log(self, m):
        """向日志区域打印信息"""
        self.log_area.insert(tk.END, m + "\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def setup_ui(self):
        """构建 Tkinter 界面"""
        # 主布局：左侧参数区，右侧日志区
        p_main = ttk.PanedWindow(self.root, orient="horizontal")
        p_main.pack(fill="both", expand=True)
        
        left = ttk.Frame(p_main)
        p_main.add(left, weight=1)
        right = ttk.Frame(p_main)
        p_main.add(right, weight=2)
        
        # --- 1. 核心参数区 ---
        p1 = ttk.LabelFrame(left, text=" 1. 核心参数 ")
        p1.pack(fill="x", padx=10, pady=5)

        def make_entry(parent, label, key, default, row, col):
            ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=2)
            e = ttk.Entry(parent, width=8)
            e.insert(0, self.params.get(key, default))
            e.grid(row=row, column=col+1, sticky="w", padx=2, pady=2)
            return e

        self.ent_n = make_entry(p1, "线程:", "n", "200", 0, 0)
        self.ent_t = make_entry(p1, "次数:", "t", "4", 0, 2)
        self.ent_dn = make_entry(p1, "数量:", "dn", "50", 1, 0)
        self.ent_dt = make_entry(p1, "时间(s):", "dt", "5", 1, 2)
        self.ent_tl = make_entry(p1, "延迟:", "tl", "500", 2, 0)
        self.ent_ipc = make_entry(p1, "配额:", "ipc", "8", 2, 2)
        self.ent_tp = make_entry(p1, "端口:", "tp", "443", 3, 0)
        self.ent_sl = make_entry(p1, "速下限:", "sl", "2", 3, 2)
        
        self.v6_var = tk.BooleanVar(value=self.params.get("ipv6", False))
        ttk.Checkbutton(p1, text="IPv6 模式", variable=self.v6_var).grid(row=4, column=0, columnspan=2, pady=5)
        
        self.ent_url = ttk.Entry(p1)
        self.ent_url.insert(0, self.params.get("url", ""))
        self.ent_url.grid(row=5, column=0, columnspan=4, sticky="we", padx=5, pady=5)
        
        # --- 2. 数据源管理 ---
        p2 = ttk.LabelFrame(left, text=" 2. 数据源管理 ")
        p2.pack(fill="x", padx=10, pady=5)
        ttk.Button(p2, text="🌐 区域选择 (多轮测速)", command=self.show_region_selector).pack(fill="x", pady=2)
        
        self.ent_remote = ttk.Entry(p2)
        self.ent_remote.insert(0, self.params.get("remote_url", ""))
        self.ent_remote.pack(fill="x", pady=2)
        
        txt_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.txt')]
        self.ent_file = ttk.Combobox(p2, values=txt_files)
        self.ent_file.set(self.params.get("ip_file", "ip.txt"))
        self.ent_file.pack(fill="x", pady=2)

        # --- 3. 推送目标 ---
        p3 = ttk.LabelFrame(left, text=" 3. 推送目标管理 ")
        p3.pack(fill="both", expand=True, padx=10, pady=5)
        self.target_frame = ttk.Frame(p3)
        self.target_frame.pack(fill="both", expand=True)
        self.render_targets()
        ttk.Button(p3, text="➕ 添加新目标", command=self.edit_target_ui).pack(fill="x", pady=2)
        
        # --- 4. 运行日志与结果展示 ---
        p4 = ttk.LabelFrame(right, text=" 4. 实时监控 ")
        p4.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("IP", "Colo", "归属", "延迟", "速度")
        self.tree = ttk.Treeview(p4, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.log_area = scrolledtext.ScrolledText(right, bg="#0c0c0c", fg="#00ff41", font=("Consolas", 10), height=25)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 底部按钮
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill="x", padx=10, pady=10)
        self.run_btn = ttk.Button(btn_frame, text="🚀 启动全自动化流程", command=self.start_task)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=5)
        self.load_push_btn = ttk.Button(btn_frame, text="📂 加载缓存并推送", command=self.load_csv_and_push)
        self.load_push_btn.pack(side="right", fill="x", expand=True, padx=5)

    def show_region_selector(self):
        """弹出地区选择窗口"""
        win = tk.Toplevel(self.root)
        win.title("选择要测速的地区")
        win.geometry("400x600")
        
        canvas = tk.Canvas(win)
        sb = ttk.Scrollbar(win, command=canvas.yview)
        fr = ttk.Frame(canvas)
        
        fr.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=fr, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.config(yscrollcommand=sb.set)
        
        self.temp_vars = {}
        for continent, countries in REGIONS_DATA.items():
            cf = ttk.LabelFrame(fr, text=continent)
            cf.pack(fill="x", padx=10, pady=5)
            for cc, colos in countries.items():
                ttk.Label(cf, text=f"{get_flag_emoji(cc)} {cc}", font=("Arial", 9, "bold")).pack(anchor="w", padx=10)
                colo_box = ttk.Frame(cf)
                colo_box.pack(fill="x", padx=25)
                for idx, (code, name) in enumerate(colos):
                    var = tk.BooleanVar(value=(code in self.selected_colos))
                    self.temp_vars[code] = var
                    ttk.Checkbutton(colo_box, text=f"{name}({code})", variable=var).grid(row=idx//3, column=idx%3, sticky="w")
        
        def save_selection():
            self.selected_colos = {c for c, v in self.temp_vars.items() if v.get()}
            win.destroy()
            
        ttk.Button(win, text="保存选择", command=save_selection).pack(pady=10)

    def render_targets(self):
        """刷新左侧推送目标列表"""
        for w in self.target_frame.winfo_children():
            w.destroy()
        self.target_vars = []
        for i, t in enumerate(self.targets):
            r = ttk.Frame(self.target_frame)
            r.pack(fill="x", pady=2)
            v = tk.BooleanVar(value=t.get("active", True))
            self.target_vars.append(v)
            ttk.Checkbutton(r, variable=v).pack(side="left")
            ttk.Label(r, text=t['name'], width=25).pack(side="left")
            ttk.Button(r, text="✍️", width=3, command=lambda idx=i: self.edit_target_ui(idx)).pack(side="right")
            ttk.Button(r, text="🗑️", width=3, command=lambda idx=i: self.del_target(idx)).pack(side="right")

    def edit_target_ui(self, index=None):
        """添加或编辑推送目标的弹出框"""
        win = tk.Toplevel(self.root)
        win.title("编辑推送目标")
        
        # 如果是编辑已有项，填充数据
        if index is not None:
            t = self.targets[index]
        else:
            t = {"name":"", "url":"", "mode":"JSON", "push_type":"OVERWRITE", "template":"{flag} {country}_{colo}_{speed}", "separator":"\\n"}
            
        def save():
            new_target = {
                "name": e1.get(), "url": e2.get(), "mode": m.get(), 
                "push_type": pt.get(), "template": e3.get(), 
                "separator": e4.get(), "active": True
            }
            if index is not None:
                self.targets[index] = new_target
            else:
                self.targets.append(new_target)
            self.render_targets()
            win.destroy()

        ttk.Label(win, text="名称:").pack()
        e1 = ttk.Entry(win, width=30); e1.insert(0, t['name']); e1.pack()
        
        ttk.Label(win, text="API URL:").pack()
        e2 = ttk.Entry(win, width=40); e2.insert(0, t['url']); e2.pack()
        
        pt = tk.StringVar(value=t.get('push_type','OVERWRITE'))
        ttk.Radiobutton(win, text="覆盖清空模式", variable=pt, value="OVERWRITE").pack()
        ttk.Radiobutton(win, text="增量添加模式", variable=pt, value="APPEND").pack()
        
        m = tk.StringVar(value=t['mode'])
        ttk.Radiobutton(win, text="JSON 模式 (多用于 Abern9 接口)", variable=m, value="JSON").pack()
        ttk.Radiobutton(win, text="TEXT 模式 (多用于 LiamZZR 接口)", variable=m, value="TEXT").pack()
        
        ttk.Label(win, text="备注模板 (可用变量: {ip}, {port}, {flag}, {country}, {colo}, {speed}):").pack()
        e3 = ttk.Entry(win, width=40); e3.insert(0, t['template']); e3.pack()
        
        ttk.Label(win, text="文本分隔符 (仅在 TEXT 模式有效，如 \\n):").pack()
        e4 = ttk.Entry(win, width=20); e4.insert(0, t['separator']); e4.pack()
        
        ttk.Button(win, text="保存配置", command=save).pack(pady=10)

    def del_target(self, i):
        """删除推送目标"""
        del self.targets[i]
        self.render_targets()

    def start_task(self):
        """启动按钮的回调函数"""
        self.save_config()
        self.run_btn.config(state="disabled")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.log_area.delete(1.0, tk.END)
        # 开启新线程运行，防止 GUI 卡死
        threading.Thread(target=self.run_engine, daemon=True).start()

    def run_engine(self):
        """核心测速逻辑：循环调用 CloudflareST.exe"""
        if not os.path.exists(CFST_EXE):
            self.log("❌ 错误：找不到 CloudflareST.exe 文件！")
            self.run_btn.config(state="normal")
            return

        ip_file = os.path.join(BASE_DIR, self.ent_file.get())
        p = self.params
        ipc = int(p['ipc'])
        # 如果没有选地区，则默认跑一轮全量
        colos = list(self.selected_colos) if self.selected_colos else [None]
        self.last_results = []
        
        for idx, colo in enumerate(colos):
            self.log(f"\n>>> 🚀 正在开始第 [{idx+1}/{len(colos)}] 轮测速: {colo if colo else '全量测速'}")
            
            # 构建命令行参数
            cmd = [
                CFST_EXE, "-n", p['n'], "-t", p['t'], "-dn", str(p['dn']), 
                "-dt", p['dt'], "-tp", p['tp'], "-tl", p['tl'], "-sl", p['sl'], 
                "-url", p['url'], "-o", f"res_{idx}.csv", "-p", "0", "-f", ip_file
            ]
            if colo:
                cmd.extend(["-httping", "-cfcolo", colo])
            if self.v6_var.get():
                cmd.append("-v6")

            try:
                # 执行测速程序并实时捕获输出
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                    text=True, encoding='utf-8', cwd=BASE_DIR
                )
                for line in process.stdout: 
                    if "测速已完成" in line or "平均延迟" in line:
                        self.log(f"  [ST] {line.strip()}")
                process.wait()

                # 解析本轮测速产生的临时 CSV 文件
                csv_path = os.path.join(BASE_DIR, f"res_{idx}.csv")
                if os.path.exists(csv_path):
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        # 动态获取下载速度列名（防版本差异）
                        speed_col = next((h for h in reader.fieldnames if "下载速度" in h), "下载速度 (MB/s)")
                        count = 0
                        for r in reader:
                            if count >= ipc: break
                            ip = r.get('IP 地址')
                            real_colo = r.get(reader.fieldnames[-1], 'Any').strip()
                            speed = r.get(speed_col, '0.00').strip()
                            lat = r.get('平均延迟', '0.00').strip()
                            
                            cc_info = COLO_LOOKUP.get(real_colo, ("UN", "未知地区"))
                            
                            # 更新到界面表格
                            self.tree.insert("", "end", values=(ip, real_colo, cc_info[1], lat, speed))
                            # 存入结果列表
                            self.last_results.append({
                                "ip": ip, "port": p['tp'], "colo": real_colo, 
                                "country": cc_info[1], "speed": speed, 
                                "flag": get_flag_emoji(cc_info[0]), "lat": lat
                            })
                            count += 1
                    os.remove(csv_path) # 删除临时文件
            except Exception as e:
                self.log(f"❌ 程序执行报错: {e}")
            
        if self.last_results:
            self.export_to_csv()
            self.push_data(self.last_results)
            
        self.run_btn.config(state="normal")
        messagebox.showinfo("完成", "全自动化流程已结束")

    def export_to_csv(self):
        """将最终结果保存到本地 CSV 存档"""
        if not self.last_results: return
        try:
            with open(EXPORT_CSV_FILE, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=self.last_results[0].keys())
                writer.writeheader()
                writer.writerows(self.last_results)
        except:
            pass

    def load_csv_and_push(self):
        """手动加载上次的测速文件并推送"""
        if not os.path.exists(EXPORT_CSV_FILE):
            messagebox.showwarning("提示", "未找到历史结果文件")
            return
        try:
            self.last_results = []
            with open(EXPORT_CSV_FILE, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.last_results.append(row)
            self.push_data(self.last_results)
            messagebox.showinfo("成功", "缓存数据已重新推送")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")

    def push_data(self, nodes):
        """执行 API 推送逻辑"""
        self.log("\n>>> [API] 正在执行 API 数据推送...")
        for i, t in enumerate(self.targets):
            # 跳过未选中的目标
            if not self.target_vars[i].get():
                continue
            
            try:
                # 间隔 1 秒，防止请求过快
                time.sleep(1)

                # --- 1. 覆盖模式处理 ---
                if t.get('push_type') == "OVERWRITE":
                    self.log(f" 🔄 正在清空目标 [{t['name']}] 的旧数据...")
                    try:
                        self.session.delete(t['url'], json={"all": True}, timeout=10)
                    except Exception as de:
                        self.log(f" ⚠️ 清空操作异常 (可能接口不支持 DELETE，已跳过): {de}")

                # --- 2. 构造载荷并推送 ---
                if t['mode'] == "JSON":
                    # 构造 JSON 数组，适合 Abern9 类接口
                    payload = []
                    for n in nodes:
                        note = t['template'].format(**n)
                        payload.append({
                            "ip": n['ip'], 
                            "port": int(n['port']), 
                            "name": note
                        })
                    res = self.session.post(t['url'], json=payload, timeout=15)
                else:
                    # 构造纯文本，适合 LiamZZR 类接口
                    sep = t['separator'].replace("\\n", "\n").replace("\\t", "\t")
                    body_str = sep.join([t['template'].format(**n) for n in nodes])
                    res = self.session.post(t['url'], data=body_str.encode('utf-8'), timeout=15)
                
                res.raise_for_status()
                self.log(f" ✅ 推送成功: {t['name']}")
                
            except Exception as e:
                self.log(f" ❌ 推送失败 [{t['name']}]: {e}")

# --- 入口 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CFSTApp(root)
    root.mainloop()