import os

# 寫入
fd = os.open("hello.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
os.write(fd, b"Hello, File I/O!\n")
os.close(fd)

# 讀取
fd = os.open("hello.txt", os.O_RDONLY)
while True:
    data = os.read(fd, 128)
    if not data:       # read 回傳空 bytes → EOF
        break
    os.write(1, data)  # 直接寫到 stdout (fd=1)
os.close(fd)

# 附加
fd = os.open("hello.txt", os.O_WRONLY | os.O_APPEND)
os.write(fd, "附加一行\n".encode())
os.close(fd)
