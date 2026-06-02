import threading, queue, sys

# 建議將提示字元統一管理
_PROMPT_TEXT  = "mini-os@user:~$ "
_output_queue = queue.Queue()
_gui_callback = None  # 新增：用來存放 GUI 的回傳函式

def set_gui_callback(callback):
    """讓 GUI 註冊一個用來接收文字的函式"""
    global _gui_callback
    _gui_callback = callback

def _writer():
    while True:
        item = _output_queue.get()
        kind = item[0]
        
        if kind == "print":
            text = item[1] + item[2]
            # 1. 依然印到終端機 (方便除錯)
            sys.stdout.write(text)
            sys.stdout.flush()
            
            # 2. 如果 GUI 有註冊掛鉤，就傳給 GUI
            if _gui_callback:
                _gui_callback(text)
            
        elif kind == "prompt_request":
            sys.stdout.flush()
            item[1].set()
            
        elif kind == "stop":
            _output_queue.task_done()
            break
        _output_queue.task_done()

# 啟動 IO 執行緒
_writer_thread = threading.Thread(target=_writer, daemon=True, name="io-writer")
_writer_thread.start()

def safe_print(*args, sep=" ", end="\n", **kwargs):
    text = sep.join(str(a) for a in args)
    _output_queue.put(("print", text, end))

def prompt_input(prompt_text=_PROMPT_TEXT) -> str:
    event = threading.Event()
    
    # 傳送請求給 writer 執行緒
    _output_queue.put(("prompt_request", event)) 
    
    # 等待 writer 執行緒回報：現在螢幕輸出已經排隊處理完畢了
    event.wait()
    
    # 核心修改：將 prompt_text 直接傳入 input()
    # readline 模組會將這個字串註冊為真正的「提示字元」
    # 這樣按上下鍵重繪時，它才懂得重新印出這個提示字元。
    return input(prompt_text)

def stop_writer():
    _output_queue.put(("stop", None))