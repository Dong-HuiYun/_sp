import curses, time, threading

REFRESH_INTERVAL=0.5

def _safe_addstr(win,y,x,text,attr=0):
    try:
        h,w=win.getmaxyx()
        if y<0 or y>=h or x<0: return
        win.addstr(y,x,text[:w-x-1],attr)
    except curses.error: pass

def _box_title(win,title):
    try: win.box(); _safe_addstr(win,0,2,f" {title} ",curses.A_BOLD)
    except curses.error: pass

def launch_tui(os_kernel):
    curses.wrapper(_tui_main,os_kernel)

def _tui_main(stdscr,os_kernel):
    curses.curs_set(0); stdscr.nodelay(True); stdscr.timeout(int(REFRESH_INTERVAL*1000))
    curses.start_color(); curses.use_default_colors()
    curses.init_pair(1,curses.COLOR_CYAN,-1)
    curses.init_pair(2,curses.COLOR_GREEN,-1)
    curses.init_pair(3,curses.COLOR_YELLOW,-1)
    curses.init_pair(4,curses.COLOR_RED,-1)
    curses.init_pair(5,curses.COLOR_MAGENTA,-1)
    STATE_COLOR={"RUNNING":curses.color_pair(2)|curses.A_BOLD,"READY":curses.color_pair(3),
                 "WAITING":curses.color_pair(4),"TERMINATED":curses.color_pair(4)|curses.A_DIM,"NEW":0}
    while True:
        key=stdscr.getch()
        if key in (ord('q'),ord('Q'),27): break
        stdscr.erase(); H,W=stdscr.getmaxyx()
        if H<20 or W<60:
            _safe_addstr(stdscr,0,0,"Terminal too small (need 60x20+)"); stdscr.refresh(); continue
        algo=os_kernel.scheduler.algorithm
        aging="aging:ON" if os_kernel.aging_enabled else "aging:OFF"
        hdr=f" MINI-OS DASHBOARD  [{algo}] [{aging}]  q=exit "
        _safe_addstr(stdscr,0,0,hdr.center(W),curses.color_pair(1)|curses.A_REVERSE)
        mid_x=W//2; mid_y=H//2
        try:
            pw=stdscr.derwin(mid_y-1,mid_x,1,0); mw=stdscr.derwin(mid_y-1,W-mid_x,1,mid_x)
            sw=stdscr.derwin(H-mid_y,mid_x,mid_y,0); iw=stdscr.derwin(H-mid_y,W-mid_x,mid_y,mid_x)
        except curses.error: stdscr.refresh(); continue
        _draw_procs(pw,os_kernel,STATE_COLOR); _draw_mem(mw,os_kernel)
        _draw_sems(sw,os_kernel); _draw_ipc(iw,os_kernel)
        stdscr.refresh()

def _draw_procs(win,os,SC):
    _box_title(win,"PROCESSES"); h,w=win.getmaxyx()
    with os.lock: ready=list(os.ready_queue)
    cur=os.current_process; all_ps=os.get_all_processes(); row=1
    _safe_addstr(win,row,2,f"{'PID':<5}{'STATE':<12}{'PRI':<8}{'INSTR':<7}{'WAIT':>6}s",curses.A_UNDERLINE); row+=1
    for p in all_ps:
        if row>=h-1: break
        aged=f"+{p.priority-p.original_priority}" if p.priority!=p.original_priority else ""
        line=f"{p.pid:<5}{p.state.name:<12}{str(p.priority)+aged:<8}{p.stats.cpu_instructions:<7}{p.stats.waiting_time:>6.1f}"
        _safe_addstr(win,row,2,line,SC.get(p.state.name,0)); row+=1

def _draw_mem(win,os):
    _box_title(win,"MEMORY"); h,w=win.getmaxyx(); mm=os.memory_mgr
    used=sum(1 for o in mm._frame_owner if o is not None); free=mm.total_frames-used; row=1
    _safe_addstr(win,row,2,f"Frames:{mm.total_frames} Used:{used} Free:{free}",curses.color_pair(5)); row+=1
    _safe_addstr(win,row,2,f"Page faults: {mm.page_fault_count}",curses.color_pair(4) if mm.page_fault_count>0 else 0); row+=2
    _safe_addstr(win,row,2,f"{'PID':<5}{'Loaded':>8}{'OnDisk':>8}",curses.A_UNDERLINE); row+=1
    for pid in sorted(mm._page_tables.keys()):
        if row>=h-1: break
        loaded=list(mm._page_tables[pid].keys()); on_disk=list(mm._on_disk.get(pid,{}).keys())
        _safe_addstr(win,row,2,f"{pid:<5}{str(loaded):>8}{str(on_disk):>8}"); row+=1

def _draw_sems(win,os):
    _box_title(win,"SEMAPHORES"); h,w=win.getmaxyx(); sm=os.sem_manager; row=1
    if not sm._sems: _safe_addstr(win,row,2,"(no semaphores)",curses.A_DIM); return
    _safe_addstr(win,row,2,f"{'ID':<4}{'NAME':<14}{'VAL':>5}{'WAITING'}",curses.A_UNDERLINE); row+=1
    for sid,sem in sm._sems.items():
        if row>=h-1: break
        with sem._lock: val=sem.value; waiting=[p.pid for p in sem._wait_queue]
        col=curses.color_pair(4) if val<=0 else curses.color_pair(2)
        _safe_addstr(win,row,2,f"{sid:<4}{sem.name:<14}{val:>5}  {waiting}",col); row+=1

def _draw_ipc(win,os):
    _box_title(win,"IPC INBOXES"); h,w=win.getmaxyx(); ipc=os.ipc; row=1
    with ipc._lock: inboxes={pid:list(q) for pid,q in ipc._inboxes.items()}
    if not inboxes: _safe_addstr(win,row,2,"(no mailboxes)",curses.A_DIM); return
    _safe_addstr(win,row,2,f"{'PID':<5}{'MSGS':>5}  CONTENT",curses.A_UNDERLINE); row+=1
    for pid,msgs in sorted(inboxes.items()):
        if row>=h-1: break
        col=curses.color_pair(3) if msgs else 0
        _safe_addstr(win,row,2,f"{pid:<5}{len(msgs):>5}  {msgs[:3]}",col); row+=1
