import curses, time, pickle

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
            

def move_by(window, dy, dx):
    y, x = window.getyx()
    newy = (y + dy) % curses.LINES
    newx = (x + dx) % curses.COLS
    window.move(newy, newx)
    return window.getyx()

def reset(scr):
    scr.clear()
    scr.move(curses.LINES//2, curses.COLS//2)

def main(scr):
    global current_color
    reset(scr)
    init_colors()
    drawing = Drawing(scr)
    
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
        elif c == ord("n"): # NEW DRAWING
            reset(scr)
            drawing = Drawing(scr)
        elif c == ord("p"): # PEN UP/DOWN
            drawing.pen_down = not drawing.pen_down
        elif c in map(ord, "+*^-xX#oO=_|\/~ "): # PEN TIP
            drawing.pen_tip = chr(c)
        elif c in map(ord, "01234567"): # COLOR SELECTION
            drawing.color_pair = int(chr(c))
        elif c == ord("R"): # REPLAY CURRENT DRAWING
            drawing.replay()
        elif c == ord("S"): # SAVE CURRENT DRAWING
            with open("drawing.pickle", "wb") as save_file:
                pickle.dump(drawing.points, save_file)
        elif c == ord("L"): # LOAD SAVED DRAWING
            with open("drawing.pickle", "rb") as load_file:
                drawing = Drawing(scr)
                drawing.points = pickle.load(load_file)
                drawing.replay()

        drawing.draw()

curses.wrapper(main)    
