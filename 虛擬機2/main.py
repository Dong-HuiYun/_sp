from vm        import VirtualMachine
from os_kernel import SimpleOS
from shell     import Shell

def main():
    vm=VirtualMachine(); os_kernel=SimpleOS(vm); Shell(os_kernel).run()

if __name__=="__main__": main()
