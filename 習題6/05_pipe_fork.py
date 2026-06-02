import os

r_fd, w_fd = os.pipe()   # r_fd=讀端, w_fd=寫端

pid = os.fork()

if pid == 0:
    # 子行程：執行 ls，stdout → pipe 寫端
    os.close(r_fd)
    os.dup2(w_fd, 1)     # stdout → 寫端
    os.close(w_fd)
    os.execvp("ls", ["ls"])

else:
    # 父行程：執行 wc -l，stdin ← pipe 讀端
    os.close(w_fd)
    os.dup2(r_fd, 0)     # stdin ← 讀端
    os.close(r_fd)
    os.execvp("wc", ["wc", "-l"])
