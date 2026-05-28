import threading, queue, sys

# 建議將提示字元統一管理
_PROMPT_TEXT  = "mini-os@user:~$ "
_output_queue = queue.Queue()

def _writer():
    while True:
        item = _output_queue.get()
        kind = item[0]
        
        if kind == "print":
            # 正常印出 OS 的 Log
            sys.stdout.write(item[1] + item[2])
            sys.stdout.flush()
            
        elif kind == "prompt_request":
            # --- 關鍵修改點 ---
            # 這裡「不要」印出 _PROMPT_TEXT！
            # 因為我們要交給接下來的 input(_PROMPT_TEXT) 來印。
            # 我們只需要確保之前的輸出都已經印完了，並換行（可選）。
            # sys.stdout.write("\n") # 如果你希望提示字元前多一個空行可以加上這句
            sys.stdout.flush()
            
            # 通知 prompt_input 執行緒：螢幕現在是乾淨的，你可以開始 input() 了
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