import curses, time, pickle, os, random

def init_colors():
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_MAGENTA)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_GREEN)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_CYAN)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)

class Drawing:
    def __init__(self, window, bgcolor=curses.COLOR_BLACK):
        self.bgcolor = bgcolor
        self.window = window #curses.newwin()
        self.points = []
        self.pen_down = True
        self.pen_tip = " "
        self.color_pair = 1
        self.fname = None
 
    def draw(self):
        if self.pen_down:
            y, x = self.window.getyx()
            point = y, x, self.pen_tip, curses.color_pair(self.color_pair)
            self.points.append(point)
            self.window.addstr(*point)
            move_by(self.window,0,-1) # addstr moves the cursor to the right; move back

    def replay(self):
        self.window.clear()
        self.window.refresh()
        time.sleep(1)
        for point in self.points:
            self.window.addstr(*point)
            self.window.refresh()
            time.sleep(0.2)
            # TODO: allow quit?/jump to end?
            
    def save(self, drawingsdir):
        if not self.fname:
            fname = "%d.pickle" % (len(os.listdir(drawingsdir)) + 1)
            self.fname = os.path.join(drawingsdir, fname)

        with open(self.fname, "wb") as save_file:
            pickle.dump(self.points, save_file)

    def load_random(self, drawingsdir):
        files = os.listdir(drawingsdir)
        if len(files) > 0:
            fname = os.path.join(drawingsdir, random.choice(files))
            with open(fname, "rb") as load_file:
                self.points = pickle.load(load_file)
                self.fname = fname
                self.replay()
        
class Tutor:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.played = set()

    def message(self, msg, timeout=None):
        msg_win = curses.newwin(7, curses.COLS, 0, 0)
        msg_win.bkgdset(" ", curses.color_pair(0))
        msg_win.addstr(1, 1, r" /\___/\ ", curses.A_BOLD)
        msg_win.addstr(2, 1, r"; ^   ^ :", curses.A_BOLD)
        msg_win.addstr(3, 1, r"|(o)^(o)|", curses.A_BOLD) 
        msg_win.addstr(4, 1, r" \  V   /", curses.A_BOLD)
        msg_win.addstr(5, 1, r"  \    / ", curses.A_BOLD)

        for i, line in enumerate(msg.splitlines()):
            msg_win.addstr(i+1, 12, line)
            if i > 5:
                break

        msg_win.border()
        msg_win.refresh()
        time.sleep(timeout or 3)
        del msg_win
        self.parent.touchwin()
        self.parent.refresh()

    def new(self):
        if 'new' not in self.played:
            self.message("N is for NORA and also for NEW!\nLooks like you've got some drawing to do.")
        self.played.add('new')

    def change_color(self):
        if 'change' not in self.played:
            self.message("C is for CHANGE\nand also for COLOR\nPress C again when you want another")
        self.played.add('change')

    def pen(self):
        if 'pen' not in self.played:
            self.message("""P is for PEN which draws on the PAGE\nPress P to PICK up the pen\nAnd to PUT it back down""")
        self.played.add('pen')





def move_by(window, dy, dx):
    y, x = window.getyx()
    newy = (y + dy) % curses.LINES
    newx = (x + dx) % curses.COLS
    window.move(newy, newx)
    return window.getyx()

def reset(scr):
    scr.clear()
    scr.move(curses.LINES//2, curses.COLS//2)

def directory_setup():
    drawingsdir = os.path.expanduser("~/drawings")
    if not os.path.exists(drawingsdir):
        os.mkdir(drawingsdir)

    return drawingsdir
def main(scr):
    reset(scr)
    init_colors()
    drawing = Drawing(scr)
    tutor = Tutor(scr)
    save_dir = directory_setup()
    
    while True:
        c = scr.getch()
        if c == ord("q"):
            break
        elif c == curses.KEY_UP:
            y, x = move_by(scr,-1,0)
        elif c == curses.KEY_DOWN:
            y, x = move_by(scr,1,0)
        elif c == curses.KEY_RIGHT:
            y, x = move_by(scr,0,1)
        elif c == curses.KEY_LEFT:
            y, x = move_by(scr,0,-1)
        elif c == ord("c"): # CHANGE COLORS
           drawing.color_pair = (drawing.color_pair + 1) % 10
           tutor.change_color()
        elif c == ord("n"): # NEW DRAWING
            reset(scr)
            drawing = Drawing(scr)
            tutor.new()
        elif c == ord("p"): # PEN UP/DOWN
            drawing.pen_down = not drawing.pen_down
            tutor.pen()
        elif c in map(ord, " ~`!@#$%^&*()-_+=vVxXoO|\/[]{}'.:<>\""): # PEN TIP
            drawing.pen_tip = chr(c)
        elif c in map(ord, "01234567"): # COLOR SELECTION
            drawing.color_pair = int(chr(c))
        elif c == ord("r"): # REPLAY CURRENT DRAWING
            tutor.message("OK, now it's my turn!")
            drawing.replay()
        elif c == ord("s"): # SAVE CURRENT DRAWING
            drawing.save(save_dir)
            tutor.message("I saved your drawing!")
        elif c == ord("l"): # LOAD SAVED DRAWING
            drawing = Drawing(scr)
            drawing.load_random(save_dir)
            #TODO: message("No pictures to load!")

        drawing.draw()

curses.wrapper(main)    
