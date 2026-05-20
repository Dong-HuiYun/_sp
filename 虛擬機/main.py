from vm import VirtualMachine
from os_kernel import SimpleOS
from shell import Shell

def main():
    # 1. 建立硬體層
    vm = VirtualMachine()

    # 2. 建立 OS 核心層（持有 VM）
    os_kernel = SimpleOS(vm)

    # 3. 建立 Shell 層（持有 OS，完全不知道 VM）
    shell = Shell(os_kernel)

    # 4. 啟動互動介面
    shell.run()

if __name__ == "__main__":
    main()