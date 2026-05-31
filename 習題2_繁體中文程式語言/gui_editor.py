import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import compiler_vm  # 請確保你的 compiler_vm 也能處理 v3 的 AST 節點
import ctypes
import os

try:
    # 這裡的 ID 建議每次大改後稍微變動一下，例如加個版本號，強迫 Windows 更新快取
    my_app_id = 'my.chinese.lang.ide.v3.final.fix' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
except:
    pass

class ChineseLangIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("繁體中文程式語言 IDE")
        self.root.geometry("1200x900")

        # --- 雙重圖標設定邏輯 ---
        try:
            # 步驟 A：先載入 PNG 並套用給 iconphoto
            # 這一步主要是為了讓「任務列」抓到這張圖片
            if os.path.exists("images/繁.png"):
                self.app_icon_png = tk.PhotoImage(file="images/繁.png")
                # True 會套用到任務列與 Alt-Tab 畫面
                self.root.iconphoto(True, self.app_icon_png)
            
            # 步驟 B：再使用 iconbitmap 套用 ICO 檔案
            # 這一步會「覆蓋」視窗左上角的標題列圖示
            # 因為 ICO 檔案內含 16x16 尺寸，所以左上角會變得非常清晰
            if os.path.exists("images/繁.ico"):
                self.root.iconbitmap("images/繁.ico")

        except Exception as e:
            print(f"圖標設定失敗：{e}")

        # --- 之後接原本的介面配置 ---

        # --- 介面佈局 ---
        self.main_v_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
        self.main_v_pane.pack(fill=tk.BOTH, expand=True)

        self.top_h_pane = ttk.PanedWindow(self.main_v_pane, orient=tk.HORIZONTAL)
        self.main_v_pane.add(self.top_h_pane, weight=3)

        # --- 左側：指令工具箱 (v3 擴充版) ---
        palette_frame = ttk.Frame(self.top_h_pane)
        self.top_h_pane.add(palette_frame, weight=1)
        
        # 使用 Scrollbar 處理大量指令
        canvas = tk.Canvas(palette_frame, width=120)
        scrollbar = ttk.Scrollbar(palette_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.commands = [
            ("--- 基礎語法 ---", None),
            ("宣告整數", "令 變數 為 整數 等於 0。\n"),
            ("宣告列表", "令 數組 為 整數列表 等於 ［1，2，3］。\n"),
            ("詢問輸入", "詢問 「請輸入內容」 並存入 變數。\n"),
            ("顯示輸出", "顯示 「哈囉」。\n"),
            
            ("--- 流程控制 ---", None),
            ("如果判斷", "如果（1 等於 1）則：\n  顯示 「對」。\n。完\n"),
            ("當循環 (While)", "當（計數 小於 5）就：\n  令 計數 等於 計數 加 1。\n。完\n"),
            ("從到循環 (For)", "從 1 到 10 以 索引 做：\n  顯示 索引。\n。完\n"),
            
            ("--- 函數功能 ---", None),
            ("定義函數", "定義 函數名（參數）為：\n  回傳 0。\n。完\n"),
            ("函數回傳", "回傳 0。\n"),
            
            ("--- 列表操作 ---", None),
            ("添加元素", "添加 元素 於 數組。\n"),
            ("彈出元素", "彈出 數組 並存入 變數。\n"),
            ("取得長度", "長度（數組）"),
            
            ("--- 異常處理 ---", None),
            ("嘗試捕捉", "嘗試：\n  顯示 「嘗試執行」。\n。完若出錯：\n  顯示 「出錯了」。\n。完\n"),
            
            ("--- 算術與運算 ---", None),
            ("餘數", " 餘 "), ("次方", " 次方 "), ("不等於", " 不等於 "),
        ]

        for text, snippet in self.commands:
            if snippet is None:
                ttk.Label(scrollable_frame, text=text, foreground="gray", font=("", 10, "bold")).pack(fill=tk.X, padx=5, pady=(10, 2))
            else:
                btn = ttk.Button(scrollable_frame, text=text, command=lambda s=snippet: self.insert_code(s))
                btn.pack(fill=tk.X, padx=10, pady=2)

        # --- 中央：編輯區 ---
        editor_frame = ttk.Frame(self.top_h_pane)
        self.top_h_pane.add(editor_frame, weight=4)

        toolbar = ttk.Frame(editor_frame)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="▶ 執行", command=self.run_code).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(toolbar, text="📂 開啟", command=self.open_file).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(toolbar, text="💾 儲存", command=self.save_file).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(toolbar, text="🗑 清除", command=self.clear_editor).pack(side=tk.LEFT, padx=2, pady=5)

        self.text_editor = scrolledtext.ScrolledText(
            editor_frame, font=("Consolas", 14), undo=True, bg="#2b2b2b", fg="#f8f8f2", insertbackground="white"
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        self.text_editor.bind("<KeyRelease>", self.highlight_keywords)
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-o>", self.open_file)
        self.text_editor.bind("<Control-d>", self.delete_line)
        self.root.bind("<Control-l>", self.clear_editor_shortcut)
        # 設定錯誤行高亮的顏色：深紅色背景，白色文字
        self.text_editor.tag_config("errorline", background="#751d1d", foreground="white")

        # --- 下方：終端機 ---
        console_frame = ttk.LabelFrame(self.main_v_pane, text="終端機 (Terminal)")
        self.main_v_pane.add(console_frame, weight=1)
        self.console = scrolledtext.ScrolledText(console_frame, font=("Microsoft JhengHei", 12), bg="#1e1e1e", fg="#61afef", height=8)
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.config(state=tk.DISABLED)

        # 記住目前開啟的檔案路徑（供引入模組時定位用）
        self.current_file_path = None

    # --- 功能函數 ---
    def insert_code(self, snippet):
        self.text_editor.insert(tk.INSERT, snippet)
        self.highlight_keywords()

    def log(self, msg, is_error=False):
        self.console.config(state=tk.NORMAL)
        tag = "err" if is_error else "msg"
        self.console.insert(tk.END, f"{msg}\n", tag)
        self.console.tag_config("err", foreground="#e06c75")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def run_code(self):
        code = self.text_editor.get("1.0", tk.END).strip()
        if not code: return
        
        # 1. 執行前先清除舊的錯誤紅字
        self.text_editor.tag_remove("errorline", "1.0", tk.END)
        
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        
        self.log(">>> 正在執行...")
        try:
            import os
            base_dir = (
                os.path.dirname(os.path.abspath(self.current_file_path))
                if self.current_file_path else None
            )
            # 2. 呼叫編譯器執行
            outputs = compiler_vm.run_source(code, base_dir=base_dir)
            for line in outputs: 
                self.log(line)
            self.log("\n[執行完畢]")
            
        except Exception as e:
            # 3. 捕捉到錯誤時，解析行號
            err_msg = str(e)
            line_num = 0
            
            # 使用正則表達式尋找錯誤訊息中的「第X行」
            import re
            match = re.search(r"第(\d+)行", err_msg)
            if match:
                line_num = int(match.group(1))
            
            # 4. 重要：呼叫高亮功能畫出紅字
            self.highlight_error_line(line_num)
            
            # 5. 印出錯誤訊息到終端機
            self.log(err_msg, is_error=True)

    def open_file(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("繁體中文程式", "*.中文")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert(tk.END, f.read())
            self.current_file_path = path          # ← 記住開啟的檔案路徑
            self.root.title(f"繁體中文程式語言 IDE — {path}")
            self.highlight_keywords()

    def save_file(self, event=None):
        path = filedialog.asksaveasfilename(defaultextension=".中文")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_editor.get("1.0", tk.END))
            self.current_file_path = path          # ← 記住儲存的路徑
            self.root.title(f"繁體中文程式語言 IDE — {path}")
        return "break"
    
    def delete_line(self, event=None):
        """刪除游標所在的整行程式碼"""
        # "insert linestart" 到 "insert lineend + 1c" 會包含換行符一起刪除
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        return "break"  # 阻止 Tkinter 預設行為

    def clear_editor_shortcut(self, event=None):
        """快捷鍵觸發的一鍵清空"""
        self.clear_editor() # 呼叫你原本就有的清空方法
        return "break"
    
    def clear_editor(self):
        self.text_editor.delete("1.0", tk.END)
    
    def highlight_error_line(self, line_num):
        """在編輯器中標註錯誤行"""
        # 1. 先清除之前所有的錯誤標註
        self.text_editor.tag_remove("errorline", "1.0", tk.END)
        
        # 2. 如果行號有效，則標註該行
        if line_num > 0:
            start = f"{line_num}.0"
            end = f"{line_num}.end + 1c"
            self.text_editor.tag_add("errorline", start, end)
            self.text_editor.see(start)  # 自動捲動到錯誤行

    def highlight_keywords(self, event=None):
        # 清除舊標籤
        for tag in ["kw", "op", "str", "func"]:
            self.text_editor.tag_remove(tag, "1.0", tk.END)
        
        content = self.text_editor.get("1.0", tk.END)
        
        # v3 關鍵字清單
        keywords = ["令", "為", "等於", "顯示", "詢問", "並存入", "如果", "則", "否則", "當", "就", "完", 
                    "從", "到", "以", "做", "定義", "回傳", "跳出", "繼續", "引入", "嘗試", "若出錯", "添加", "彈出", "於"]
        operators = ["加", "減", "乘", "除", "餘", "次方", "且", "或", "非", "大於", "小於", "不等於"]
        builtins = ["長度", "整數", "字串", "整數列表", "字串列表"]

        def paint(words, tag, color, bold=False):
            for w in words:
                idx = "1.0"
                while True:
                    idx = self.text_editor.search(w, idx, stopindex=tk.END)
                    if not idx: break
                    end = f"{idx}+{len(w)}c"
                    self.text_editor.tag_add(tag, idx, end)
                    idx = end
            self.text_editor.tag_config(tag, foreground=color, font=("Consolas", 14, "bold" if bold else "normal"))

        paint(keywords, "kw", "#c678dd", True)
        paint(operators, "op", "#56b6c2")
        paint(builtins, "func", "#e5c07b")

        # 字串高亮
        import re
        for m in re.finditer(r"「.*?」", content):
            self.text_editor.tag_add("str", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        self.text_editor.tag_config("str", foreground="#98c379")

if __name__ == "__main__":
    root = tk.Tk()
    ChineseLangIDE(root)
    root.mainloop()