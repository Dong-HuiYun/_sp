import os

# 兩條 pipe：parent→child, child→parent
p2c_r, p2c_w = os.pipe()
c2p_r, c2p_w = os.pipe()

pid = os.fork()

if pid == 0:
    # 子行程
    os.close(p2c_w)
    os.close(c2p_r)

    msg = os.read(p2c_r, 256)
    print(f"[子] 收到：{msg.decode().strip()}")
    os.close(p2c_r)

    reply = b"pong\n"
    os.write(c2p_w, reply)
    os.close(c2p_w)

else:
    # 父行程
    os.close(p2c_r)
    os.close(c2p_w)

    os.write(p2c_w, b"ping\n")
    os.close(p2c_w)

    reply = os.read(c2p_r, 256)
    print(f"[父] 收到：{reply.decode().strip()}")
    os.close(c2p_r)

    os.waitpid(pid, 0)
