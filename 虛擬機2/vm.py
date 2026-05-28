from io_utils import safe_print
from memory import PAGE_SIZE

class VirtualMachine:
    def __init__(self, memory_size=256):
        self.memory=[0]*memory_size
        self.registers={'R1':0,'R2':0,'R3':0,'R4':0,'PC':0,'IR':None}
        self.flags={'ZF':False,'SF':False}; self.halted=False
        self.ipc=None; self.sem_manager=None; self.current_pid=None
        self.ipc_recv_block=False; self.sem_block=False
        self.page_fault_vp=None; self._pending_sem_id=None; self._pending_awakened=None

    def load_program(self, program):
        for i,instr in enumerate(program):
            if i<len(self.memory): self.memory[i]=instr

    def step(self):
        if self.halted: return
        pc=self.registers['PC']
        vp=pc//PAGE_SIZE
        if pc<len(self.memory) and self.memory[pc]==0 and pc>0:
            self.page_fault_vp=vp; return
        if pc>=len(self.memory) or self.memory[pc]==0:
            self.halted=True; return
        self.registers['IR']=self.memory[pc]
        instr=self.registers['IR']; op,args=instr[0],instr[1:]
        self._execute(op,args)
        if not self.halted and not self.ipc_recv_block and not self.sem_block:
            self.registers['PC']+=1

    def _execute(self, op, args):
        r=self.registers
        if op=="SET":
            val=args[1]; r[args[0]]=r[val] if isinstance(val,str) else val
        elif op=="ADD": r[args[0]]+=r[args[1]]
        elif op=="SUB": r[args[0]]-=r[args[1]]
        elif op=="MUL": r[args[0]]*=r[args[1]]
        elif op=="PRINT": safe_print(f"[VM Output] {args[0]}: {r[args[0]]}")
        elif op=="HALT": self.halted=True
        elif op=="JUMP": r['PC']=args[0]-1
        elif op=="CMP":
            a,b=r[args[0]],r[args[1]]; self.flags['ZF']=(a==b); self.flags['SF']=(a<b)
        elif op=="JNZ":
            if not self.flags['ZF']: r['PC']=args[0]-1
        elif op=="JZ":
            if self.flags['ZF']: r['PC']=args[0]-1
        elif op=="JN":
            if self.flags['SF']: r['PC']=args[0]-1
        elif op=="LOAD":
            addr=args[1]
            if 0<=addr<len(self.memory): r[args[0]]=self.memory[addr]
            else: safe_print(f"[VM] LOAD: address {addr} out of range."); self.halted=True
        elif op=="STORE":
            addr=args[1]
            if 0<=addr<len(self.memory): self.memory[addr]=r[args[0]]
            else: safe_print(f"[VM] STORE: address {addr} out of range."); self.halted=True
        elif op=="SEND":
            if self.ipc is None: safe_print("[VM] SEND: IPC not available."); return
            self.ipc.send(self.current_pid,args[0],r[args[1]])
        elif op=="RECV":
            if self.ipc is None: safe_print("[VM] RECV: IPC not available."); return
            msg=self.ipc.recv(self.current_pid)
            if msg is not None:
                from_pid,value=msg; r[args[0]]=value
                safe_print(f"[VM] PID {self.current_pid} RECV: {args[0]}={value} (from PID {from_pid})")
            else:
                self.ipc_recv_block=True
                safe_print(f"[VM] PID {self.current_pid} RECV: inbox empty, entering WAITING.")
        elif op=="WAIT":
            if self.sem_manager is None: safe_print("[VM] WAIT: SemaphoreManager not available."); return
            self.sem_block=True; self._pending_sem_id=args[0]
            # PC 提前 +1，讓喚醒後從 WAIT 的下一條指令繼續執行
            self.registers['PC']+=1
            safe_print(f"[VM] PID {self.current_pid} WAIT sem={args[0]}")
        elif op=="SIGNAL":
            if self.sem_manager is None: safe_print("[VM] SIGNAL: SemaphoreManager not available."); return
            awakened=self.sem_manager.signal(args[0],from_pid=self.current_pid)
            if awakened: self._pending_awakened=awakened
            safe_print(f"[VM] PID {self.current_pid} SIGNAL sem={args[0]}")
        else:
            safe_print(f"[VM] Unknown opcode: {op}"); self.halted=True
