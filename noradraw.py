import curses, time, pickle, os, random

def init_colors():
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_MAGENTA)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_GREEN)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_CYAN)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # curses.init_pair(8, curses.COLOR_BLACK, 208) # orange-ish 
    # curses.init_pair(9, curses.COLOR_YELLOW, 53) # darker purple-ish 

PEN_TIPS = " ~`!@#$%^&*()-_+=vVxXoO|\/[]{}'.:<>\""

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

    def erase_last(self):
        if self.points: # we can only erase existing points
            y, x, _, _ = self.points.pop(-1)
            self.window.addstr(y, x, " ", curses.color_pair(0))
        if self.points: # restore to previous point before erased point, if any
            prev_point = self.points[-1]
            self.window.move(prev_point[0], prev_point[1])
        self.window.refresh()
        
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

    def owl_win(self):
        max_y, max_x = self.parent.getmaxyx()
        owl_win = curses.newwin(7, max_x, 0, 0)
        owl_win.bkgdset(" ", curses.color_pair(0))
        owl_win.addstr(1, 1, r" /\___/\ ", curses.A_BOLD)
        owl_win.addstr(2, 1, r"; ^   ^ :", curses.A_BOLD)
        owl_win.addstr(3, 1, r"|(o)^(o)|", curses.A_BOLD) 
        owl_win.addstr(4, 1, r" \  V   /", curses.A_BOLD)
        owl_win.addstr(5, 1, r"  \    / ", curses.A_BOLD)
        owl_win.border()
        owl_win.refresh()

        msg_win = owl_win.subwin(1,13)
        return msg_win


    def message(self, msg, timeout=None):
        msg_win = self.owl_win()
        for i, line in enumerate(msg.splitlines()):
            msg_win.addstr(i, 0, line)
            if i > 5:
                break

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

    def erase(self):
        if 'erase' not in self.played:
            self.message("E is for ERASE\nIt deletes your mistakes\nat a moderate pace")
        self.played.add('erase')

    def pen(self):
        if 'pen' not in self.played:
            self.message("P is for PEN which draws on the PAGE\nPress P to PICK up the pen\nAnd to PUT it back down")
        self.played.add('pen')

    def help(self):
        if len(self.played) < 2:
            self.message("Play around a little more.\nYou'll soon figure everything out!\nYou can ask me for more help later.")
            return

        msg_win = self.owl_win()
        for i in range(8):
            msg_win.addstr(" %d " % i, curses.color_pair(i) | curses.A_BOLD)
        msg_win.addstr(": COLORS ")
        msg_win.addstr("/*|!", curses.A_BOLD)
        msg_win.addstr(" etc. are PEN TIPS")

        y, x = msg_win.getyx()
        msg_win.move(y+1, 1)
        msg_win.addstr("C", curses.A_BOLD)
        msg_win.addstr(": CHANGE COLOR ")
        msg_win.addstr("P", curses.A_BOLD)
        msg_win.addstr(": PEN UP/DOWN ")
        msg_win.addstr("E", curses.A_BOLD)
        msg_win.addstr(": ERASE ")


        y, x = msg_win.getyx()
        msg_win.move(y+1, 1)
        msg_win.addstr("N", curses.A_BOLD)
        msg_win.addstr(": NEW DRAWING ")
        msg_win.addstr("S", curses.A_BOLD)
        msg_win.addstr(": SAVE DRAWING ")
        msg_win.addstr("L", curses.A_BOLD)
        msg_win.addstr(": LOAD DRAWING ")
        msg_win.addstr("R", curses.A_BOLD)
        msg_win.addstr(": RICHARD REPLAYS ")

        y, x = msg_win.getyx()
        msg_win.move(y+1, 0)
        msg_win.addstr("Q", curses.A_BOLD)
        msg_win.addstr(": QUIT")

        msg_win.refresh()

        #"0-7: COLORS C: CHANGE COLOR ...: PEN TIPS N: NEW DRAWING R: RICHARD REPLAY S: SAVE L: LOAD Q: QUIT"



def move_by(window, dy, dx):
    y, x = window.getyx()
    maxy, maxx = window.getmaxyx()
    newy = (y + dy) % maxy
    newx = (x + dx) % maxx
    window.move(newy, newx)
    return window.getyx()

def reset(scr):
    scr.clear()
    scr.refresh()
    max_y, max_x = scr.getmaxyx()
    scr.move(max_y//2, max_x//2)


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
    inhibit_next_draw = False
    
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
           drawing.color_pair = (drawing.color_pair + 1) % 8
           tutor.change_color()
        elif c == ord("n"): # NEW DRAWING
            drawing = Drawing(scr)
            reset(scr)
            tutor.new()
        elif c == ord("p"): # PEN UP/DOWN
            drawing.pen_down = not drawing.pen_down
            tutor.pen()
        elif c == ord("e"): # ERASE
            drawing.erase_last()
            tutor.erase()
            inhibit_next_draw = True
        elif c in map(ord, PEN_TIPS): # PEN TIP
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
        elif c == ord("?") or c == ord("h"): # HELP
            tutor.help()

        if inhibit_next_draw:
            inhibit_next_draw = False
        else:
            drawing.draw()

curses.wrapper(main)    
