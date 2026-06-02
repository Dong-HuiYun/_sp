import os
import sys

pid = os.fork()

if pid == 0:
    # 子行程：用 ls -l 取代自己
    os.execvp("ls", ["ls", "-l"])
    # 到這裡代表 execvp 失敗
    print("execvp 失敗", file=sys.stderr)
    sys.exit(1)

else:
    _, status = os.waitpid(pid, 0)
    print(f"[父] ls 結束，exit code={os.WEXITSTATUS(status)}")
