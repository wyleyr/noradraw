#!/usr/bin/python3
# noradraw, a curses-based drawing program
# Copyright (C) 2020 Richard Lawrence
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import curses, time, pickle, os, random

def init_colors():
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_MAGENTA)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_GREEN)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_CYAN)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)

def display_logo(scr):
    with open("logo.pickle", "rb") as logofile:
        logo = Drawing(scr)
        logo.points = pickle.load(logofile)
        logo.replay()
        logo.window.addstr(28,22,"Press N to start a new drawing")
        logo.refresh()
    

PEN_TIPS = " ~`!@#$%^&*()-_+=vVxXoO|\/[]{}'.:<>\""

class Drawing:
    def __init__(self, screen):
        self.window = curses.newpad(128, 368) # big enough for a fullscreen terminal on a large screen
        self.screen = screen
        self.points = []
        self.pen_down = True
        self.pen_tip = " "
        self.color_pair = 1
        self.fname = None

        # the pad coordinates which will be displayed at the upper
        # left corner of the screen:
        self.corner_y = 0
        self.corner_x = 0

        # place the cursor in the middle of the *screen* on init
        scrmax_y, scrmax_x = self.screen.getmaxyx()
        self.window.move(scrmax_y//2, scrmax_x//2)

    def move_by(self, dy, dx):
        y, x = self.window.getyx()
        maxy, maxx = self.window.getmaxyx()
        newy = (y + dy) % maxy
        newx = (x + dx) % maxx
        self.window.move(newy, newx)
        
        return self.window.getyx()

    def draw(self):
        if self.pen_down:
            y, x = self.window.getyx()
            point = y, x, self.pen_tip, curses.color_pair(self.color_pair)
            self.points.append(point)
            self.window.addstr(*point)
            self.move_by(0,-1*len(self.pen_tip)) # addstr moves the cursor to the right; move back
        self.refresh()

    def erase_last(self):
        if self.points: # we can only erase existing points
            y, x, _, _ = self.points.pop(-1)
            self.window.addstr(y, x, " ", curses.color_pair(0))
        if self.points: # restore to previous point before erased point, if any
            prev_point = self.points[-1]
            self.window.move(prev_point[0], prev_point[1])
        self.refresh()
        
    def replay(self):
        self.window.clear()
        self.refresh()
        time.sleep(1)
        wait = min(0.2, 60/(1+len(self.points))) # don't take longer than 1min 
        for point in self.points:
            self.window.addstr(*point)
            self.move_by(0,-1) # addstr moves the cursor to the right; move back
            self.refresh()
            time.sleep(wait)
            # TODO: allow quit?/jump to end?

    def find_corner(self):
        if not self.points:
            min_y, min_x = 0, 0
        else:
            scrmax_y, scrmax_x = min_y, min_x = self.screen.getmaxyx()
            max_y, max_x = 0, 0
            for y, x, _, _ in self.points:
                if y < min_y:
                    min_y = y
                if x < min_x:
                    min_x = x
                if y > max_y:
                    max_y = y
                if x > max_x:
                    max_x = x

            # set a new corner if the drawing is offscreen:
            if max_y > scrmax_y or max_x > scrmax_x:
                self.corner_y = max(min_y - 2, 0) 
                self.corner_x = max(min_x - 2, 0)

        return self.corner_y, self.corner_x

    def recenter(self):
        "Reorient and redisplay the current drawing onscreen after a resize or load"
        # Find the new upper left corner:
        p_y, p_x = self.find_corner()
        scrmax_y, scrmax_x = self.screen.getmaxyx()

        # without this, self.window doesn't refresh:
        self.screen.clear()
        self.screen.refresh() 

        # redisplay the drawing, placing the new upper left corner coordinates
        # of the drawing at 0,0 on the screen:
        self.window.touchwin()
        self.window.refresh(p_y, p_x, 0, 0, scrmax_y-1, scrmax_x-1)

        # make sure the cursor ends up onscreen:
        cur_y, cur_x = self.window.getyx()
        self.window.move(min(cur_y, scrmax_y + p_y - 1), min(cur_x, scrmax_x + p_x - 1))
        

    def refresh(self):
        scrmax_y, scrmax_x = self.screen.getmaxyx()
        self.window.refresh(self.corner_y, self.corner_x, 0, 0, scrmax_y-1, scrmax_x-1)
            
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
                self.recenter() 
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
        msg_win.addstr(": COLORS    ")
        msg_win.addstr("/*|!", curses.A_BOLD)
        msg_win.addstr(" etc. are PEN TIPS")

        y, x = msg_win.getyx()
        msg_win.move(y+1, 1)
        msg_win.addstr("C", curses.A_BOLD)
        msg_win.addstr(": CHANGE COLOR   ")
        msg_win.addstr("P", curses.A_BOLD)
        msg_win.addstr(": PEN UP/DOWN   ")
        msg_win.addstr("E", curses.A_BOLD)
        msg_win.addstr(": ERASE   ")


        y, x = msg_win.getyx()
        msg_win.move(y+1, 1)
        msg_win.addstr("N", curses.A_BOLD)
        msg_win.addstr(": NEW DRAWING    ")
        msg_win.addstr("S", curses.A_BOLD)
        msg_win.addstr(": SAVE DRAWING  ")
        msg_win.addstr("L", curses.A_BOLD)
        msg_win.addstr(": LOAD DRAWING  ")
        msg_win.addstr("R", curses.A_BOLD)
        msg_win.addstr(": OWL REPLAYS ")

        y, x = msg_win.getyx()
        msg_win.move(y+1, 1)
        msg_win.addstr("Q", curses.A_BOLD)
        msg_win.addstr(": QUIT")

        y, x = msg_win.getyx()
        msg_win.move(y+1, 19)
        msg_win.addstr("Press any key to go back to the drawing!")

        msg_win.refresh()

        # for some reason we need to call getch() on self.parent (the screen),
        # because calling it on msg_win apparently leaves control
        # characters in the buffer and ends up setting the pen tip as
        # a side effect.
        self.parent.getch() 

        del msg_win


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
    display_logo(scr)
    drawing = Drawing(scr)
    tutor = Tutor(scr)
    save_dir = directory_setup()
    
    while True:
        c = scr.getch()
        if c == ord("q"): # QUIT
            break
        elif c == curses.KEY_RESIZE:
            drawing.recenter()
            continue
        elif c == curses.KEY_UP:
            drawing.move_by(-1,0)
        elif c == curses.KEY_DOWN:
            drawing.move_by(1,0)
        elif c == curses.KEY_RIGHT:
            drawing.move_by(0,1)
        elif c == curses.KEY_LEFT:
            drawing.move_by(0,-1)
        elif c == ord("c"): # CHANGE COLORS
           drawing.color_pair = (drawing.color_pair + 1) % 8
           tutor.change_color()
        elif c == ord("n"): # NEW DRAWING
            reset(scr)
            drawing = Drawing(scr)
            tutor.new()
            continue 
        elif c == ord("p"): # PEN UP/DOWN
            drawing.pen_down = not drawing.pen_down
            tutor.pen()
        elif c == ord("e"): # ERASE
            tutor.erase()
            drawing.erase_last()
            continue # skip drawing, which would negate the erase
        elif c == ord("r"): # REPLAY CURRENT DRAWING
            tutor.message("OK, now it's my turn!")
            drawing.replay()
            continue
        elif c == ord("s"): # SAVE CURRENT DRAWING
            try:
                drawing.save(save_dir)
                tutor.message("I saved your drawing!")
            except IOError:
                tutor.message("Sorry, something went wrong.\nI couldn't save this drawing.")
        elif c == ord("l"): # LOAD SAVED DRAWING
            try:
                drawing = Drawing(scr)
                tutor.message("Here's a drawing you made!\n(Or someone made for you!)")
                drawing.load_random(save_dir)
            except IndexError:
                message("There are no drawings to load!\nYou should save one first.")
            continue
        elif c == ord("D"): # DELETE
            if drawing.fname:
                os.remove(drawing.fname)
                tutor.message("Deleted %s" % drawing.fname)
                reset(scr)
                drawing = Drawing(scr)

        elif c == ord("?") or c == ord("h"): # HELP
            tutor.help()
        elif c in map(ord, PEN_TIPS): # PEN TIP
            drawing.pen_tip = chr(c)
        elif c in map(ord, "01234567"): # COLOR SELECTION
            drawing.color_pair = int(chr(c))
        elif c == curses.KEY_F3: # DEBUG
            curses.savetty()
            scr.move(0,0)
            curses.reset_shell_mode()
            scr.refresh()
            import pdb
            pdb.set_trace()
            curses.resetty()
            reset(scr)
            drawing.recenter()

        drawing.draw()

curses.wrapper(main)    
