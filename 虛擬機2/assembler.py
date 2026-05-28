from io_utils import safe_print

REGISTERS={"R1","R2","R3","R4"}
JUMP_OPS={"JUMP","JNZ","JZ","JN"}

class AssemblerError(Exception): pass

def assemble(source, filename="<string>"):
    lines=source.splitlines(); raw=[]; labels={}
    for line_no,line in enumerate(lines,1):
        line=line.split(";")[0].strip()
        if not line: continue
        if line.endswith(":"):
            label=line[:-1].strip()
            if not label.isidentifier(): raise AssemblerError(f"Line {line_no}: invalid label '{label}'")
            if label in labels: raise AssemblerError(f"Line {line_no}: duplicate label '{label}'")
            labels[label]=len(raw)
        else:
            raw.append((line_no,line.split()))
    program=[]
    for idx,(line_no,tokens) in enumerate(raw):
        op=tokens[0].upper(); args=tokens[1:]
        try: program.append(_parse_instr(op,args,labels,line_no))
        except AssemblerError: raise
        except Exception as e: raise AssemblerError(f"Line {line_no}: {e}")
    if not program: raise AssemblerError("Empty program.")
    return program

def _parse_instr(op, args, labels, line_no):
    def req(n):
        if len(args)!=n: raise AssemblerError(f"Line {line_no}: {op} needs {n} arg(s), got {len(args)}")
    def resolve(token):
        if token in labels: return labels[token]
        try: return int(token)
        except: raise AssemblerError(f"Line {line_no}: '{token}' is not a label or int")
    def reg_or_int(token):
        u=token.upper()
        if u in REGISTERS: return u
        try: return int(token)
        except: raise AssemblerError(f"Line {line_no}: '{token}' not a register or int")
    if op=="HALT": req(0); return ("HALT",)
    if op in ("PRINT","RECV"): req(1); return (op,args[0].upper())
    if op in JUMP_OPS: req(1); return (op,resolve(args[0]))
    if op in ("WAIT","SIGNAL"): req(1); return (op,int(args[0]))
    if op=="SET": req(2); return (op,args[0].upper(),reg_or_int(args[1]))
    if op in ("ADD","SUB","MUL","CMP"): req(2); return (op,args[0].upper(),args[1].upper())
    if op=="SEND": req(2); return (op,int(args[0]),args[1].upper())
    if op in ("LOAD","STORE"): req(2); return (op,args[0].upper(),int(args[1]))
    raise AssemblerError(f"Line {line_no}: unknown opcode '{op}'")

def load_file(path):
    try:
        with open(path,"r",encoding="utf-8") as f: source=f.read()
    except FileNotFoundError: raise AssemblerError(f"File not found: '{path}'")
    except IOError as e: raise AssemblerError(f"Cannot read '{path}': {e}")
    program=assemble(source,filename=path)
    safe_print(f"[ASM] Loaded '{path}': {len(program)} instructions.")
    return program

def disassemble(program):
    return "\n".join(f"  {i:>4}: {instr[0]} {' '.join(str(a) for a in instr[1:])}".rstrip() for i,instr in enumerate(program))
