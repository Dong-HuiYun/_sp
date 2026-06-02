import os
import sys

pid = os.fork()

if pid < 0:
    print("fork 失敗", file=sys.stderr)
    sys.exit(1)

elif pid == 0:
    # 子行程
    print(f"[子] pid={os.getpid()}, 父 pid={os.getppid()}")
    sys.exit(0)

else:
    # 父行程
    print(f"[父] pid={os.getpid()}, 子 pid={pid}")
    _, status = os.waitpid(pid, 0)
    print(f"[父] 子行程結束，exit code={os.WEXITSTATUS(status)}")
