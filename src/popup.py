import textwrap
import curses

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

    def add_text(self, text):
        self.txt.extend( split_text(text, self.w - 4) )
        return

    def add_option(self, label, payload=None):
        self.cmd.append(label)
        self.ret.append(payload)
        return

    def run(self):
        game = self.game
        gfx  = game.gfx

        sel = 0
        w = self.w
        h = self.h
        while True:
            gfx.draw_map(game.cam)
            gfx.fb.scanout()

            x = gfx.fb.w // 2 - w // 2
            y = gfx.fb.h // 2 - h // 2

            gfx.win.addstr(y, x, "+" + ("-")*(w-2) + "+")
            y+=1
            for line in self.txt:
                gfx.win.addstr(y, x, f"| {" "*(w-4)} |")
                gfx.win.addstr(y, x+2, line)
                y+=1

            gfx.win.addstr(y, x, f"| {" "*(w-4)} |")
            y+=1

            for i in range(len(self.cmd)):
                line = self.cmd[i]
                gfx.win.addstr(y, x, f"| {" "*(w-4)} |")
                gfx.win.addstr(y, x+2, ("> " if i==sel else "  ") + line)
                y+=1

            gfx.win.addstr(y, x, "|" + (" ")*(w-2) + "|")
            y+=1
            gfx.win.addstr(y, x, "+" + ("-")*(w-2) + "+")

            gfx.win.refresh()

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

            sel = max(0, min(sel, len(self.cmd)-1))
