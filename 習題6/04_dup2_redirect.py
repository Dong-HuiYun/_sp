import os

# 開啟目標檔案
fd = os.open("out.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

# dup2(fd, 1)：讓 fd 1 (stdout) 改指向 out.txt
os.dup2(fd, 1)
os.close(fd)

# 之後所有寫 stdout 的動作都進 out.txt
os.write(1, "這行會寫進 out.txt\n".encode())
os.write(2, "這行還是去終端機 (stderr)\n".encode())