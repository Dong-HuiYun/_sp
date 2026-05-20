import threading
import queue
import sys

_output_queue = queue.Queue()
_PROMPT = "\nmini-os@user:~$ "

def _writer():
    while True:
        item = _output_queue.get()
        kind = item[0]
        if kind == "print":
            sys.stdout.write(item[1] + item[2])
            sys.stdout.flush()
        elif kind == "prompt":
            sys.stdout.write(_PROMPT)
            sys.stdout.flush()
            item[1].set()
        elif kind == "stop":
            _output_queue.task_done()
            break
        _output_queue.task_done()

_writer_thread = threading.Thread(target=_writer, daemon=True, name="io-writer")
_writer_thread.start()


def safe_print(*args, sep=" ", end="\n", **kwargs):
    text = sep.join(str(a) for a in args)
    _output_queue.put(("print", text, end))


def prompt_input() -> str:
    event = threading.Event()
    _output_queue.put(("prompt", event))
    event.wait()
    return input()


def stop_writer():
    _output_queue.put(("stop", None))