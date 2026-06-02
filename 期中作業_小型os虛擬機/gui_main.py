import sys
import threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QTextCursor

# 導入你原本的核心模組
from os_kernel import SimpleOS
from vm import VirtualMachine
from shell import DISK
import io_utils

# 訊號橋接器：負責把背景執行緒的 Log 傳給 GUI 主執行緒
class SignalBridge(QObject):
    log_received = pyqtSignal(str)

class MiniOSGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Mini-OS Visualizer")
        self.resize(1100, 800)

        # 1. 初始化核心
        self.vm = VirtualMachine()
        self.os = SimpleOS(self.vm)
        self.os_thread = None

        # 2. 初始化訊號橋接
        self.bridge = SignalBridge()
        self.bridge.log_received.connect(self.append_log)
        io_utils.set_gui_callback(self.bridge.log_received.emit)

        self.init_ui()

        # 3. 定時刷新 UI (行程表、記憶體)
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_dashboard)
        self.ui_timer.start(500) # 每 0.5 秒更新一次

    def init_ui(self):
        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # --- 左側：控制與行程列表 ---
        left_panel = QVBoxLayout()
        
        # 控制按鈕
        ctrl_group = QGroupBox("System Control")
        ctrl_layout = QGridLayout()
        
        self.btn_start = QPushButton("🚀 Start Scheduler")
        self.btn_start.clicked.connect(self.start_os)
        
        self.btn_reset = QPushButton("♻️ Reset")
        self.btn_reset.clicked.connect(self.reset_os)
        
        self.prog_combo = QComboBox()
        self.prog_combo.addItems(list(DISK.keys()))

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 20) # 限制優先權範圍 1~20
        self.priority_spin.setValue(1)     # 預設值
        
        self.btn_run = QPushButton("➕ Load Process")
        self.btn_run.clicked.connect(self.load_process)

        ctrl_layout.addWidget(QLabel("Select Program:"), 0, 0)
        ctrl_layout.addWidget(self.prog_combo, 0, 1)
        ctrl_layout.addWidget(QLabel("Pri:"), 0, 2)       # 標籤
        ctrl_layout.addWidget(self.priority_spin, 0, 3)    # 數字輸入框
        ctrl_layout.addWidget(self.btn_run, 0, 4)
        ctrl_layout.addWidget(self.btn_start, 1, 0, 1, 2)
        ctrl_layout.addWidget(self.btn_reset, 1, 2)
        ctrl_group.setLayout(ctrl_layout)
        left_panel.addWidget(ctrl_group)

        # 行程表格
        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "State", "Pri", "Instr", "Wait(s)"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_panel.addWidget(QLabel("Processes:"))
        left_panel.addWidget(self.proc_table)

        main_layout.addLayout(left_panel, stretch=2)

        modify_pri_layout = QHBoxLayout()
        self.new_pri_spin = QSpinBox()
        self.new_pri_spin.setRange(1, 20)
        self.btn_update_pri = QPushButton("Update Selected Priority")
        self.btn_update_pri.clicked.connect(self.update_selected_priority)
        
        modify_pri_layout.addWidget(QLabel("New Pri:"))
        modify_pri_layout.addWidget(self.new_pri_spin)
        modify_pri_layout.addWidget(self.btn_update_pri)
        left_panel.addLayout(modify_pri_layout)

        # --- 右側：記憶體與 Log ---
        right_panel = QVBoxLayout()

        # 記憶體視覺化 (簡單文字版或表格版)
        self.mem_status = QTextEdit()
        self.mem_status.setReadOnly(True)
        self.mem_status.setFixedHeight(200)
        self.mem_status.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        right_panel.addWidget(QLabel("Memory Frames / Page Tables:"))
        right_panel.addWidget(self.mem_status)

        # 系統日誌
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: #000; color: #fff; font-family: Consolas;")
        right_panel.addWidget(QLabel("System Logs:"))
        right_panel.addWidget(self.log_display)

        main_layout.addLayout(right_panel, stretch=3)

    def append_log(self, text):
        """接收來自 io_utils 的訊號並更新 UI"""
        self.log_display.insertPlainText(text)
        # 自動捲動到底部
        self.log_display.moveCursor(QTextCursor.MoveOperation.End)

    def load_process(self):
        prog_name = self.prog_combo.currentText()
        # 從輸入框讀取優先權
        pri = self.priority_spin.value() 
        pid = self.os.create_process(DISK[prog_name], priority=pri)
        if pid: 
            self.append_log(f"[GUI] Loaded {prog_name} as PID {pid} (Priority: {pri})\n")

    def start_os(self):
        if self.os_thread and self.os_thread.is_alive():
            return
        # 在背景執行緒啟動 OS 循環
        self.os_thread = threading.Thread(target=self.os.run, args=(2,), daemon=True)
        self.os_thread.start()
        self.btn_start.setEnabled(False)
        self.append_log("[GUI] Scheduler Started.\n")

    def reset_os(self):
        self.os.reset_system()
        self.btn_start.setEnabled(True)
        self.log_display.clear()
        self.append_log("[GUI] System Reset.\n")

    def update_dashboard(self):
        """定時抓取 OS 數據並更新畫面"""
        # 1. 更新行程表
        procs = self.os.get_all_processes()
        self.proc_table.setRowCount(len(procs))
        for i, p in enumerate(procs):
            self.proc_table.setItem(i, 0, QTableWidgetItem(str(p.pid)))
            self.proc_table.setItem(i, 1, QTableWidgetItem(p.state.name))
            self.proc_table.setItem(i, 2, QTableWidgetItem(str(p.priority)))
            self.proc_table.setItem(i, 3, QTableWidgetItem(str(p.stats.cpu_instructions)))
            self.proc_table.setItem(i, 4, QTableWidgetItem(f"{p.stats.waiting_time:.1f}"))

        # 2. 更新記憶體資訊
        self.mem_status.setPlainText(self.os.memory_mgr.status())
        
    def update_selected_priority(self):
        # 獲取目前表格選中的行
        current_row = self.proc_table.currentRow()
        if current_row < 0:
            self.append_log("[GUI] Please select a process in the table first.\n")
            return
            
        pid = int(self.proc_table.item(current_row, 0).text())
        new_pri = self.new_pri_spin.value()
        
        # 在 OS 中尋找該行程並修改
        all_ps = self.os.get_all_processes()
        target = next((p for p in all_ps if p.pid == pid), None)
        
        if target:
            old_pri = target.priority
            target.priority = new_pri
            target.original_priority = new_pri # 同時修改原始值防止老化機制混亂
            self.append_log(f"[GUI] PID {pid} priority updated: {old_pri} -> {new_pri}\n")
        else:
            self.append_log(f"[GUI] Error: PID {pid} not found.\n")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 設定外觀樣式
    app.setStyle("Fusion")
    
    gui = MiniOSGui()
    gui.show()
    sys.exit(app.exec())