# -*- coding: utf-8 -*-
"""NSP 打包工具（独立 GUI，与 krkr2renpy.py 无关）

内置了通用引擎骨架（exefs 引擎 + romfs 运行库 + logo + 占位图标），
用户只需指定「转换器输出的 game 目录」+ 填好 titleid/游戏名，即可一键打包。

用法：py nsp_pack_gui.py
"""
from __future__ import unicode_literals

import os
import queue
import shutil
import subprocess
import threading
import traceback

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

HERE = os.path.dirname(os.path.abspath(__file__))

# 内置引擎骨架目录（exefs + romfs 运行库 + control + logo + 占位图标）
DEFAULT_TPL = os.path.join(HERE, "template")
# 发行商默认值（通用，可改）
DEFAULT_PUB = "CCB"


class NspPackApp(object):

    def __init__(self, root):
        self.root = root
        self.worker = None
        self.q = queue.Queue()
        root.title("NSP 打包工具")
        root.geometry("840x700")
        root.minsize(720, 620)
        self._setup_style()
        self._build()

    # ------------------------------------------------------------------ 样式
    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        BG = "#f5f6f9"
        FG = "#2c3038"
        MUTED = "#7a8090"
        ACCENT = "#3b82f6"
        ACCENT_HOVER = "#2f6ad0"
        self.root.configure(bg=BG)
        style.configure(".", background=BG, foreground=FG,
                         font=("Microsoft YaHei UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Title.TLabel", background=BG, foreground="#1b1b2f",
                        font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED,
                        font=("Microsoft YaHei UI", 9))
        style.configure("Hint.TLabel", background=BG, foreground="#b06a00",
                        font=("Microsoft YaHei UI", 9))
        style.configure("TLabelframe", background=BG, bordercolor="#e2e4ea")
        style.configure("TLabelframe.Label", background=BG, foreground="#4a5060",
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TButton", background="#ffffff", foreground=FG,
                        bordercolor="#d5d8e0", padding=(12, 6))
        style.map("TButton",
                  background=[("active", "#eef0f5"), ("disabled", "#eceef2")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                        bordercolor=ACCENT, font=("Microsoft YaHei UI", 12, "bold"),
                        padding=(20, 10))
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER), ("disabled", "#c9cbd3")])
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor="#d5d8e0")

    # ------------------------------------------------------------------ 布局
    def _build(self):
        pad = {"padx": 14, "pady": 6}

        ttk.Label(self.root, text="NSP 打包工具", style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 0))
        ttk.Label(self.root,
                  text="引擎骨架已内置，只需指定转换器输出的 game 目录 + 填好标题，点一下即可打包。",
                  style="Sub.TLabel").pack(anchor="w", padx=16)

        # 输入
        inp = ttk.LabelFrame(self.root, text=" 输入 ")
        inp.pack(fill="x", **pad)
        inp.columnconfigure(1, weight=1)

        ttk.Label(inp, text="游戏目录（转换器输出）").grid(row=0, column=0, sticky="w", padx=6, pady=5)
        self.var_game = tk.StringVar(value="")
        ttk.Entry(inp, textvariable=self.var_game).grid(row=0, column=1, sticky="we", padx=6, pady=5)
        ttk.Button(inp, text="浏览…", command=lambda: self._pick_dir(self.var_game)).grid(row=0, column=2, padx=6, pady=5)

        ttk.Label(inp, text="引擎骨架目录").grid(row=1, column=0, sticky="w", padx=6, pady=5)
        self.var_tpl = tk.StringVar(value=DEFAULT_TPL)
        ttk.Entry(inp, textvariable=self.var_tpl).grid(row=1, column=1, sticky="we", padx=6, pady=5)
        ttk.Button(inp, text="浏览…", command=lambda: self._pick_dir(self.var_tpl)).grid(row=1, column=2, padx=6, pady=5)
        ttk.Label(inp, text="一般不用改；这里内置了引擎、运行库、任天堂 logo 和占位图标",
                  style="Sub.TLabel").grid(row=2, column=1, sticky="w", padx=6, pady=(0, 5))

        # 参数
        par = ttk.LabelFrame(self.root, text=" 打包参数 ")
        par.pack(fill="x", **pad)
        par.columnconfigure(1, weight=1)

        ttk.Label(par, text="Title ID").grid(row=0, column=0, sticky="w", padx=6, pady=5)
        self.var_titleid = tk.StringVar(value="")
        ttk.Entry(par, textvariable=self.var_titleid).grid(row=0, column=1, sticky="we", padx=6, pady=5)
        ttk.Label(par, text="16 位十六进制；每款唯一；不能以 01-0f 开头（官方范围），建议 10 开头以上",
                  style="Hint.TLabel").grid(row=0, column=2, sticky="w", padx=6, pady=5)

        ttk.Label(par, text="游戏名称").grid(row=1, column=0, sticky="w", padx=6, pady=5)
        self.var_title = tk.StringVar(value="")
        ttk.Entry(par, textvariable=self.var_title).grid(row=1, column=1, sticky="we", padx=6, pady=5)

        ttk.Label(par, text="发行商").grid(row=2, column=0, sticky="w", padx=6, pady=5)
        self.var_pub = tk.StringVar(value=DEFAULT_PUB)
        ttk.Entry(par, textvariable=self.var_pub).grid(row=2, column=1, sticky="we", padx=6, pady=5)

        # 可选
        opt = ttk.LabelFrame(self.root, text=" 可选（留空则用骨架内置的）")
        opt.pack(fill="x", **pad)
        opt.columnconfigure(1, weight=1)

        ttk.Label(opt, text="图标文件").grid(row=0, column=0, sticky="w", padx=6, pady=5)
        self.var_icon = tk.StringVar(value="")
        ttk.Entry(opt, textvariable=self.var_icon).grid(row=0, column=1, sticky="we", padx=6, pady=5)
        ttk.Button(opt, text="浏览…", command=lambda: self._pick_file(self.var_icon, [("图片", "*.jpg *.jpeg *.png"), ("所有文件", "*.*")])).grid(row=0, column=2, padx=6, pady=5)
        ttk.Label(opt, text="256×256 的 JPEG；留空用占位图标", style="Sub.TLabel").grid(row=0, column=3, sticky="w", padx=6, pady=5)

        ttk.Label(opt, text="引擎 NSO").grid(row=1, column=0, sticky="w", padx=6, pady=5)
        self.var_nso = tk.StringVar(value="")
        ttk.Entry(opt, textvariable=self.var_nso).grid(row=1, column=1, sticky="we", padx=6, pady=5)
        ttk.Button(opt, text="浏览…", command=lambda: self._pick_file(self.var_nso, [("NSO", "*.nso"), ("所有文件", "*.*")])).grid(row=1, column=2, padx=6, pady=5)
        ttk.Label(opt, text="留空用内置引擎（已修崩溃）", style="Sub.TLabel").grid(row=1, column=3, sticky="w", padx=6, pady=5)

        # 输出
        out = ttk.LabelFrame(self.root, text=" 输出 ")
        out.pack(fill="x", **pad)
        out.columnconfigure(1, weight=1)
        ttk.Label(out, text="NSP 输出目录").grid(row=0, column=0, sticky="w", padx=6, pady=5)
        self.var_out = tk.StringVar(value=os.path.join(HERE, "NSP"))
        ttk.Entry(out, textvariable=self.var_out).grid(row=0, column=1, sticky="we", padx=6, pady=5)
        ttk.Button(out, text="浏览…", command=lambda: self._pick_dir(self.var_out)).grid(row=0, column=2, padx=6, pady=5)

        # 操作
        act = ttk.Frame(self.root)
        act.pack(fill="x", **pad)
        self.btn_pack = ttk.Button(act, text="▶  打包 NSP", style="Accent.TButton", command=self.pack)
        self.btn_pack.pack(side="left", padx=(2, 8))
        self.btn_open = ttk.Button(act, text="打开输出目录", command=self.open_out, state="disabled")
        self.btn_open.pack(side="left", padx=6)
        ttk.Button(act, text="退出", command=self.root.destroy).pack(side="right")

        # 日志
        log = ttk.LabelFrame(self.root, text=" 日志 ")
        log.pack(fill="both", expand=True, **pad)
        self.logbox = ScrolledText(log, height=16, state="disabled", wrap="word",
                                   font=("Consolas", 9), bg="#1b1b2f", fg="#e6e6ea",
                                   insertbackground="#ffffff", relief="flat", padx=10, pady=8)
        self.logbox.pack(fill="both", expand=True, padx=6, pady=6)

    # ------------------------------------------------------------------ 交互
    def _pick_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or HERE)
        if d:
            var.set(d)

    def _pick_file(self, var, filetypes):
        f = filedialog.askopenfilename(initialdir=HERE, filetypes=filetypes)
        if f:
            var.set(f)

    def _log(self, text):
        self.logbox.config(state="normal")
        self.logbox.insert("end", text.rstrip("\n") + "\n")
        self.logbox.see("end")
        self.logbox.config(state="disabled")

    def _set_log(self, text):
        self.logbox.config(state="normal")
        self.logbox.delete("1.0", "end")
        if text:
            self.logbox.insert("end", text)
        self.logbox.config(state="disabled")

    def open_out(self):
        path = self.var_out.get()
        if os.path.isdir(path):
            try:
                os.startfile(path)
            except Exception:
                pass
        else:
            messagebox.showinfo("提示", "输出目录尚不存在：%s" % path)

    # ------------------------------------------------------------------ 打包
    def pack(self):
        if self.worker and self.worker.is_alive():
            return
        game_dir = self.var_game.get().strip()
        tpl_dir = self.var_tpl.get().strip()
        titleid = self.var_titleid.get().strip()
        title = self.var_title.get().strip()
        pub = self.var_pub.get().strip()
        icon_path = self.var_icon.get().strip()
        nso = self.var_nso.get().strip()
        outdir = self.var_out.get().strip()

        if not os.path.isdir(game_dir):
            messagebox.showerror("错误", "游戏目录不存在（应是转换器输出的 game 目录）：\n%s" % game_dir)
            return
        if not os.path.isdir(tpl_dir):
            messagebox.showerror("错误", "引擎骨架目录不存在：\n%s" % tpl_dir)
            return
        if not titleid or not title:
            messagebox.showerror("错误", "Title ID 和游戏名称不能为空。")
            return
        if not (len(titleid) == 16 and all(c in "0123456789abcdefABCDEF" for c in titleid)):
            messagebox.showerror("错误", "Title ID 必须是 16 位十六进制（0-9、a-f）。")
            return
        if 0x01 <= int(titleid[:2], 16) <= 0x0f:
            messagebox.showerror(
                "错误",
                "Title ID 不能以 01-0f 开头（这是官方应用保留范围）。\n请用 10-ff 开头，例如 11452656e7071140。")
            return
        os.makedirs(outdir, exist_ok=True)

        self._set_log("")
        self.btn_pack.config(state="disabled")
        self.btn_open.config(state="disabled")
        self.worker = threading.Thread(
            target=self._work,
            args=(game_dir, tpl_dir, nso, icon_path, titleid, title, pub, outdir),
            daemon=True)
        self.worker.start()
        self.root.after(80, self._poll)

    def _work(self, game_dir, tpl_dir, nso, icon_path, titleid, title, pub, outdir):
        # hacbrewpack 是 MSYS 程序，其运行时只认工具所在盘，所以工作目录和
        # 临时 NSP 输出都必须放在工具目录下，打包完成后再用 Python 复制到目标目录
        work = os.path.join(HERE, "_pack_work")
        tmp_nsp = os.path.join(HERE, "_nsp_out")
        try:
            # 0) 准备临时目录
            for d in (work, tmp_nsp):
                if os.path.isdir(d):
                    shutil.rmtree(d)
            os.makedirs(tmp_nsp, exist_ok=True)
            self.q.put(("log", "1/4 复制引擎骨架（exefs/romfs/control/logo）..."))
            shutil.copytree(tpl_dir, work)

            # 1) 游戏内容
            self.q.put(("log", "2/4 复制游戏内容到 romfs/Contents/game ...（大文件可能需几十秒）"))
            game_dst = os.path.join(work, "romfs", "Contents", "game")
            shutil.copytree(game_dir, game_dst)

            # 2) 引擎 NSO（可选）
            if nso and os.path.isfile(nso):
                shutil.copyfile(nso, os.path.join(work, "exefs", "main"))
                self.q.put(("log", "引擎：%s -> exefs\\main" % nso))

            # 3) 图标（可选，否则用骨架里的占位 icon.jpg）
            icon = icon_path if (icon_path and os.path.isfile(icon_path)) else os.path.join(work, "icon.jpg")
            icon_dst = os.path.join(work, "control", "icon_AmericanEnglish.dat")
            if os.path.isfile(icon):
                shutil.copyfile(icon, icon_dst)
                self.q.put(("log", "图标：%s -> control\\icon_AmericanEnglish.dat" % icon))
            else:
                self.q.put(("log", "未找到图标文件，跳过"))

            # 4) hacbrewpack（工具目录自带），先打包到工具目录下的临时 NSP 目录
            exe = os.path.join(HERE, "hacbrewpack.exe")
            key_path = os.path.join(HERE, "prod.keys")
            if not os.path.isfile(exe):
                exe = os.path.join(tpl_dir, "hacbrewpack.exe")
            if not os.path.isfile(key_path):
                key_path = os.path.join(tpl_dir, "prod.keys")
            cmd = [exe,
                   "--titleid", titleid,
                   "--titlename", title,
                   "--titlepublisher", pub,
                   "--nspdir", tmp_nsp,
                   "-k", key_path]
            self.q.put(("log", "3/4 调用 hacbrewpack 打包..."))
            self.q.put(("log", "执行：%s" % subprocess.list2cmdline(cmd)))
            self.q.put(("log", ""))

            env = dict(os.environ)
            env["MSYS2_ARG_CONV_EXCL"] = "*"
            proc = subprocess.Popen(
                cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", env=env, bufsize=1)
            for line in proc.stdout:
                self.q.put(("log", line))
            code = proc.wait()

            # 5) 把 NSP 从工具目录临时位置复制到用户目标目录（可能是别的盘）
            made = []
            if code == 0 and os.path.isdir(tmp_nsp):
                os.makedirs(outdir, exist_ok=True)
                for f in sorted(os.listdir(tmp_nsp)):
                    if f.lower().endswith(".nsp"):
                        src = os.path.join(tmp_nsp, f)
                        dst = os.path.join(outdir, f)
                        shutil.copyfile(src, dst)
                        made.append(dst)
                        self.q.put(("log", "复制 NSP：%s -> %s" % (src, dst)))
            self.q.put(("done", code, outdir, made))
        except Exception:
            self.q.put(("error", traceback.format_exc()))
        finally:
            for d in (work, tmp_nsp):
                try:
                    if os.path.isdir(d):
                        shutil.rmtree(d)
                except Exception:
                    pass
            self.q.put(("log", "4/4 清理临时文件完成"))

    def _poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                if item[0] == "log":
                    self._log(item[1])
                elif item[0] == "done":
                    code, outdir, made = item[1], item[2], item[3]
                    self._log("")
                    if code == 0:
                        if made:
                            self._log("==== 打包完成 ====")
                            self._log("NSP 已生成：")
                            for m in made:
                                self._log("  %s" % m)
                            self.btn_open.config(state="normal")
                            messagebox.showinfo("打包完成", "NSP 已生成：\n" + "\n".join(made))
                        else:
                            self._log("==== 打包结束但未找到 NSP 文件，请看上方日志 ====")
                            messagebox.showerror("打包异常", "hacbrewpack 退出码 0，但没有生成 NSP 文件，请查看日志。")
                    else:
                        self._log("==== 打包失败，退出码 %s ====" % code)
                        messagebox.showerror("打包失败", "hacbrewpack 退出码 %s，详见日志。" % code)
                    self.btn_pack.config(state="normal")
                    return
                elif item[0] == "error":
                    self._log(item[1])
                    self.btn_pack.config(state="normal")
                    messagebox.showerror("打包出错", item[1][-1500:])
                    return
        except queue.Empty:
            pass
        if self.worker and self.worker.is_alive():
            self.root.after(100, self._poll)


def main():
    try:
        import tkinter  # noqa
    except Exception:
        print("当前 Python 没有 tkinter，无法启动图形界面。")
        return 1
    root = tk.Tk()
    NspPackApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
