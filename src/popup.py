import textwrap
import curses
import time

# View menu_fly() function in main.py for a simple usage example

def split_text(text, max_length):
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(
            textwrap.wrap(line, width=max_length, break_long_words=False, replace_whitespace=False) or [''])
    return wrapped_lines

class Popup:
    def __init__(self, game):
        self.game = game
        self.w = 40
        self.h = 10
        self.txt = []
        self.cmd = []
        self.ret = []
        self.offscreen = False

        # In case caller needs to execute custom render code, these functions
        # can be set and will be called appropriately.
        # Prepass render code can only contain ascii map art render commands
        self.prepass = None
        # Postpass render code can only do direct-to-terminal text splatting
        self.postpass = None

    def add_text(self, text):
        self.txt.extend( split_text(text, self.w - 4) )
        return

    # The payload is returned instead of the label if set, if player selects
    # this option
    def add_option(self, label, payload=None):
        self.cmd.append(label)
        self.ret.append(payload)
        return

    def run(self):
        game = self.game
        gfx  = game.gfx

        sel = 0
        w = self.w
        h = 3 + len(self.txt) + len(self.cmd)
        while True:
            gfx.fb.update()
            if h >= gfx.fb.h or w >= gfx.fb.w:
                gfx.win.clear()
                gfx.win.addstr(0,0, "Your terminal is too small.")
                gfx.win.refresh()
                time.sleep(0.1)
                continue
            gfx.draw_map(game.cam)
            if self.prepass != None:
                self.prepass(game)
            gfx.fb.scanout()
            if self.postpass != None:
                self.postpass(game)

            x = gfx.fb.w // 2 - w // 2
            y = gfx.fb.h // 2 - h // 2

            str_edge = "+" + ("-")*(w-2) + "+"
            str_panel = f"| {" "*(w-4)} |"

            if self.offscreen:
                x = gfx.fb.w - w

            gfx.win.addstr(y, x, str_edge)
            y+=1
            for line in self.txt:
                gfx.win.addstr(y, x, str_panel)
                gfx.win.addstr(y, x+2, line)
                y+=1

            gfx.win.addstr(y, x, str_panel)
            y+=1

            for i in range(len(self.cmd)):
                line = self.cmd[i]
                gfx.win.addstr(y, x, str_panel)
                gfx.win.addstr(y, x+2, ("> " if i==sel else "  ") + line)
                y+=1

            gfx.win.addstr(y, x, str_panel)
            y+=1
            gfx.win.addstr(y, x, str_edge)

            gfx.win.refresh()

            # Input handling
            ch = gfx.win.getch()
            if ch == curses.KEY_ENTER or ch == 10 or ch == 13:
                ret = self.ret[sel]
                if ret != None:
                    return ret
                return self.cmd[sel]
            elif ch == ord("w") or ch == curses.KEY_UP:
                sel -= 1
            elif ch == ord("s") or ch == curses.KEY_DOWN:
                sel += 1

            elif ch == ord("x"):
                game.cam.zoom *= 2.0
            elif ch == ord("z"):
                game.cam.zoom /= 2.0

            sel = max(0, min(sel, len(self.cmd)-1))


# Immediate popup, convenience function for simple things
# Yes we procedualice OOP code, deal with it
def impopup(game, text, options):
    popup = Popup(game)

    for line in text:
        popup.add_text(line)

    for line in options:
        popup.add_option(line)

    return popup.run()
