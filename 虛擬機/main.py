from vm import VirtualMachine
from os_kernel import SimpleOS
import threading
import time

DISK = {
    "calc_add": [
        ("SET", "R1", 10), ("SET", "R2", 20), ("ADD", "R1", "R2"),
        ("PRINT", "R1"), ("HALT",)
    ],
    "counter": [
        ("SET", "R1", 1), ("PRINT", "R1"), ("SET", "R2", 1),
        ("ADD", "R1", "R2"), ("PRINT", "R1"), ("HALT",)
    ],
    "hello": [
        ("SET", "R1", 999), ("PRINT", "R1"), ("HALT",)
    ],
    "loop": [
        ("SET", "R1", 0),
        ("SET", "R2", 1),
        ("ADD", "R1", "R2"),   # index 2
        ("PRINT", "R1"),       # index 3
        ("JUMP", 2)            # 跳回 index 2 (ADD) 形成死迴圈
    ]
}

def main():
    my_vm = VirtualMachine()
    my_os = SimpleOS(my_vm)
    
    print("Welcome to Python-Mini-OS v2.0 (Memory Isolation & Priority Enabled)")
    
    while True:
        try:
            line = input("\nmini-os@user:~$ ").strip().split()
            if not line: continue
            cmd, args = line[0].lower(), line[1:]
        except EOFError: break

        if cmd == "exit": break
        elif cmd == "ls":
            print("Available programs:", ", ".join(DISK.keys()))
        elif cmd == "run":
            if not args:
                print("Usage: run <prog> [priority]")
                continue
            prog_name = args[0]
            priority = int(args[1]) if len(args) > 1 else 1
            if prog_name in DISK:
                my_os.create_process(DISK[prog_name], priority)
            else:
                print("Error: Program not found.")
        elif cmd == "start":
                    # 建立一個背景執行緒跑 OS
                    # daemon=True 表示主程式關閉時，這個執行緒也會強制關閉
                    os_thread = threading.Thread(target=my_os.run, args=(2,), daemon=True)
                    os_thread.start()
                    print("OS is now running in the background. Use 'ps' or 'kill' at any time.")
        elif cmd == "ps":
            print(f"Ready Queue: {[f'PID:{p.pid}(Pri:{p.priority})' for p in my_os.ready_queue]}")
        elif cmd == "kill":
            if args: my_os.kill_process(int(args[0]))
        elif cmd == "reset":
            my_os.reset_system()
        elif cmd == "help":
            print("Commands: ls, run <prog> <pri>, ps, start, kill <pid>, reset, exit")
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()