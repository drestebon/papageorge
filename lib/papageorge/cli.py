# cli - command-line interface

# Copyright (C) 2015 DrEstebon

# This file is part of Papageorge.
#
# Papageorge is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Papageorge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Papageorge If not, see <http://www.gnu.org/licenses/>.

import telnetlib, urwid, threading, os, re, datetime
from gi.repository import Gtk, Gdk

class HandleCommandsDialog(Gtk.Dialog):
    def set_transient_for(self, win):
        self.get_window().set_transient_for(win)

    def __init__(self, title):
        active_window = Gtk.Window()
        Gtk.Dialog.__init__(self, title, active_window)

        vbox = Gtk.VBox().new(True, 1)
        frame = Gtk.Frame().new('Match Parameters')
        frame.add(vbox)

        hbox = Gtk.HBox().new(True, 1)
        hbox.pack_start(Gtk.Label().new('Time (min)'), False, False, 0)
        adjustment = Gtk.Adjustment(5, 0, 100, 1, 10, 0)
        self.time = Gtk.SpinButton()
        self.time.set_adjustment(adjustment)
        hbox.pack_start(self.time, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        hbox = Gtk.HBox().new(True, 1)
        hbox.pack_start(Gtk.Label().new('Incr (sec)'), False, False, 0)
        adjustment = Gtk.Adjustment(10, 0, 100, 1, 10, 0)
        self.incr = Gtk.SpinButton()
        self.incr.set_adjustment(adjustment)
        hbox.pack_start(self.incr, False, False, 0)

        vbox.pack_start(hbox, False, False, 0)

        Box = self.get_content_area()
        Box.pack_start(frame, False, False, 0)

        self.add_button('_Match', 1)
        self.add_button('_Tell', 2)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        b = self.set_default_response(Gtk.ResponseType.CANCEL)
        self.show_all()

class CmdLine(urwid.Edit):
    def __init__(self, prompt, cli):
        self.cli = cli
        self.WORD_RE = re.compile('\w+')
        self.cli_commands = {
                'q': self.cmd_quit,
                'n': self.cmd_next,
                'p': self.cmd_prev,
                'b': self.cmd_board,
                'c': self.cmd_connect,
                's': self.cmd_seek_graph,
                'd': self.cmd_debug,
        }
        self.input_commands = {
                'f5'         : self.cmd_seek_graph,
                'ctrl d'     : self.cmd_quit,
                'ctrl v'     : self.cmd_clear_cmdline,
                'esc'        : self.cmd_clear_cmdline,
                'ctrl left'  : self.cmd_prev_word,
                'ctrl right' : self.cmd_next_word,
                'up'         : self.cmd_prev_cmd,
                'down'       : self.cmd_next_cmd,
        }
        self.cmd_history = list()
        self.cmd_history_idx = 0
        return super(CmdLine, self).__init__(prompt)

    def cmd_debug(self, size, key):
        return None
        
    def cmd_quit(self, size, key):
        self.cli.exit()

    def cmd_next(self, size, key):
        if len(cmd) > 1:
            if cmd[1].isdecimal():
                self.board.next_move(int(cmd[1]))
        else:
            self.board.next_move()
        self.set_edit_text(u"")
        return None

    def cmd_prev(self, size, key):
        self.board.prev_move()
        self.set_edit_text(u"")
        return None

    def cmd_board(self, size, key):
        self.gui.new_board()
        self.set_edit_text(u"")
        return None

    def cmd_seek_graph(self, size, key):
        if not self.gui.seek_graph:
            self.gui.new_seek_graph()
        self.set_edit_text(u"")
        return None

    def cmd_connect(self, size, key):
        self.set_edit_text(u"")
        self.insert_text(u"Connecting ")
        self.cli.main_loop.draw_screen()
        self.cli.connect_fics()
        self.set_edit_text(u"")
        return None

    def cmd_clear_cmdline(self, size, key):
        self.set_edit_text(u"")
        return None

    def cmd_prev_word(self, size, key):
        if self.edit_pos > 0:
            self.set_edit_pos([x.start()
                                for x in self.WORD_RE.finditer(self.edit_text)
                                  if x.start() < self.edit_pos][-1])
        return None

    def cmd_next_word(self, size, key):
        newpos = [x.start() for x in self.WORD_RE.finditer(self.edit_text) 
                      if x.start() > self.edit_pos]
        if len(newpos):
            self.set_edit_pos(newpos[0])
        return None

    def cmd_prev_cmd(self, size, key):
        self.cmd_history_idx = self.cmd_history_idx - 1
        if len(self.cmd_history)+self.cmd_history_idx < 0:
            self.cmd_history_idx = -len(self.cmd_history)
        if self.cmd_history_idx < 0:
            self.set_edit_text(u"{}".format(
                self.cmd_history[self.cmd_history_idx]))
            self.set_edit_pos(999)
        else:
            self.set_edit_text(u"")
        return None

    def cmd_next_cmd(self, size, key):
        self.cmd_history_idx = self.cmd_history_idx + 1
        if self.cmd_history_idx > -1:
            self.cmd_history_idx = 0
        if self.cmd_history_idx < 0:
            self.set_edit_text(u"{}".format(
                self.cmd_history[self.cmd_history_idx]))
            self.set_edit_pos(999)
        else:
            self.set_edit_text(u"")
        return None

    def keypress(self, size, key):
        cmd_f = next((self.input_commands[c]
                          for c in self.input_commands.keys()
                                if key == c ), False )
        if cmd_f:
            cmd_f(size, key)
        else:
            pass
        if key != 'enter':
            return super(CmdLine, self).keypress((size[0],), key)
        cmd = self.edit_text
        if len(cmd) < 1:
            return None
        elif cmd[0] == '?':
            self.cli.print("{}".format(self.cli_commands.keys()))
            self.cmd_history_idx = 0
            self.cmd_history.append(cmd)
            self.set_edit_text(u"")
            return None
        elif cmd[0] == '%':
            if cmd[1::] in self.cli_commands.keys():
                self.cmd_history_idx = 0
                self.cmd_history.append(cmd)
                return self.cli_commands[cmd[1::]](size, cmd[1::])
            else:
                self.cli.print(cmd+" verstehe ich nicht ... ")
                return None
        elif hasattr(self.cli, 'fics'):
            self.cli.print("> "+cmd, urwid.AttrSpec('#dd0', '#000'))
            self.cli.fics.write(cmd.encode()+b'\n')
            self.cmd_history_idx = 0
            self.cmd_history.append(cmd)
            self.set_edit_text(u"")
            return None
        if not cmd:
            return None
        self.cli.print("{} - Not connected!!".format(cmd))

class SCBoard_cli(urwid.Frame):
    def __init__(self, fics_user, fics_pass, log):
        self.fics_user = fics_user
        self.fics_pass = fics_pass
        self.log = log
        self.TEXT_RE = [
            ( # CHAT 50
              re.compile('^\w+(\([\w\*]+\))*\(50\): '),
                lambda regexp, txt: (urwid.AttrSpec('#95b', '#000'), txt)),
            ( # CHAT
              re.compile('^\w+(\([\w\*]+\))*\(\d+\): '),
                lambda regexp, txt: (urwid.AttrSpec('#4dd', '#000'), txt)),
            ( # SHOUT
              re.compile('^\w+(\(\w+\))* (c-)*shouts: '),
                lambda regexp, txt: (urwid.AttrSpec('#8f8', '#000'), txt)),
            ( # TELL
              re.compile('^\w+(\(\w+\))* tells you: '),
                lambda regexp, txt: (urwid.AttrSpec('#ff0', '#000'), txt)),
            ( # SELFR
              re.compile('^--> \w+(\(\w+\))*'),
                lambda regexp, txt: (urwid.AttrSpec('#8f8', '#000'), txt)),
            ( # forward backward
              re.compile("^fics% Game \w+: \w+ (goes forward|backs up)"),
                lambda regexp, txt: False),
            ( re.compile('^\s+\*\*ANNOUNCEMENT\*\*'),
                lambda regexp, txt: (urwid.AttrSpec('#9f9', '#000'), txt)),
            ( re.compile('^<s[cr]*>'),
                self.update_seek_graph),
            ( re.compile('^<12>'),
                self.style12),
            ( re.compile('^<g1>'),
                self.game_info),
            ( re.compile('^{Game (\d+)'),
                self.interruptus),
            ( re.compile('^You are no longer examining game (\d+)'),
                self.unexamine),
            ( re.compile('^Removing game (\d+) from observation list.'),
                self.unexamine),
            ( re.compile('^\\\\\s+(.+)'),
                self.continuation),
            ( re.compile('^fics% ((.|\n)+)'),
                self.strip_prompt),
        ]
        check     = '[+#]'
        rank      = '[1-8]'
        file      = '[a-h]'
        piece     = '[KNBQR]'
        promotion = "x?{}[18]=(?!K){}".format(file, piece)
        pawnmove  = "(?:{}?x)?{}(?![18]){}".format(file, file, rank)
        stdmove   = "{}{}?{}?x?{}{}".format(piece, file, rank, file, rank)
        castling  = "O-O(?:-O)?"
        handle    = '[a-z]{3,}'
        san = "((?:(?:{}|{}|{}|{}){}?))".format(
                    promotion,castling,pawnmove,stdmove,check,handle)
        highlight = "((?:(?:{}|{}|{}|{}){}?)|(?:{}))".format(
                    promotion,castling,pawnmove,stdmove,check,handle)
        handle = "({})".format(handle)
        self.san_rule = re.compile(san, re.IGNORECASE)
        self.hl_rule = re.compile(highlight, re.IGNORECASE)
        self.handle_rule = re.compile(handle, re.IGNORECASE)
        self.body_size = None
        self.die = 0
        self.txt_list = urwid.ListBox(
                            urwid.SimpleFocusListWalker([urwid.Text(u"")]))
        self.cmd_line = CmdLine(u"> ", self)
        return super(SCBoard_cli, self).__init__(self.txt_list,
                        footer=self.cmd_line, focus_part='footer')

    def continuation(self, regexp, txt):
        txt_ = self.txt_list.body.pop().get_text()
        self.txt_list.body.append(urwid.Text((txt_[1][0][0], 
                                             txt_[0]+' '+regexp.groups()[0])))
        pos = len(self.txt_list.body)-1
        self.txt_list.set_focus(pos)
        return False

    def mouse_event(self, size, event, button, col, row, focus):
        # No sirve con vtwheel
        self.size = size
        if event == 'mouse press':
            if button == 5.0:
                self.keypress(size, 'page down')
            elif button == 4.0:
                self.keypress(size, 'page up')
            elif button == 1.0:
                max_rows = size[1]-self.cmd_line.pack((size[0],))[1]
                if row < max_rows:
                    txt_row = self.txt_list.render(
                            (size[0], max_rows)).text[row].rstrip().decode()
                    m = next((m for m in self.san_rule.finditer(txt_row) 
                        if m.start() <= col and col <= m.end()), None)
                    if m:
                        self.send_cmd(m.group(), echo=True)
                    m = next((m for m in self.handle_rule.finditer(txt_row) 
                        if m.start() <= col and col <= m.end()), None)
                    if m:
                        dialog = HandleCommandsDialog(m.group())
                        response = dialog.run()
                        dialog.destroy()
                        if response == 2:
                            txt = u'tell {} '.format(m.group())
                            self.cmd_line.set_edit_text(txt)
                            self.cmd_line.set_edit_pos(len(txt))
                        elif response == 1:
                            txt = u'match {} {} {}'.format(
                                        m.group(),
                                        dialog.time.get_value_as_int(),
                                        dialog.incr.get_value_as_int())
                            self.send_cmd(txt, echo=True)
        return True

    def update_seek_graph(self, regexp, txt):
        if self.cmd_line.gui.seek_graph:
            self.cmd_line.gui.seek_graph.update(txt[regexp.pos::])
        else:
            pass
        return False

    def board_with_number(self, n):
        return next((b for b in self.cmd_line.gui.boards
                      if b.board_number == n), False )

    def style12(self, regexp, txt):
        b = self.board_with_number(int(txt.split()[16]))
        if b:
            b.set_state(txt)
        else:
            self.cmd_line.gui.new_board(initial_state=txt)
        return False

    def game_info(self, regexp, txt):
        b = self.board_with_number(int(txt.split()[1]))
        if b:
            b.set_gameinfo(txt)
        else:
            self.cmd_line.gui.new_board(game_info=txt)
        return False

    def interruptus(self, regexp, txt):
        b = self.board_with_number(int(regexp.group(1)))
        if b:
            b.state.interruptus = True
            b.redraw()
        return (urwid.AttrSpec('#eee', '#000'), txt)

    def unexamine(self, regexp, txt):
        b = self.board_with_number(int(regexp.group(1)))
        if b:
            b.win.destroy()
            self.cmd_line.gui.boards.remove(b)
        return (urwid.AttrSpec('#eee', '#000'), txt)

    def strip_prompt(self, regexp, txt):
        self.print(regexp.group(1)) 
        return False

    def keypress(self, size, key):
        self.body_size = (size[0], size[1]-self.cmd_line.pack((size[0],))[1])
        if key == 'page down':
            for x in range(5):
                self.txt_list.keypress(self.body_size, 'down')
            return self.txt_list.keypress(self.body_size, 'down')
        elif key == 'page up':
            for x in range(5):
                self.txt_list.keypress(self.body_size, 'up')
            return self.txt_list.keypress(self.body_size, 'up')
        else:
            size = self.cmd_line.pack((size[0],))
            return self.cmd_line.keypress(size, key)

    def exit(self, *args):
        if hasattr(self, 'fics_thread') and hasattr(self, 'fics'):
            self.die = 1
            self.fics.write("fi\n".encode())
            self.fics_thread.join()
        if len(args) < 1:
            raise urwid.ExitMainLoop()

    def connect_board(self, board):
        self.cmd_line.board = board

    def connect_gui(self, gui):
        self.cmd_line.gui = gui

    def print(self, text, attr=None):
        if (len(self.txt_list.body) and
                (text.find('\n') == 0 or len(text) == 0)):
            txt_ = self.txt_list.body[-1].get_text()[0]
            if txt_.find('\n') == 0 or len(txt_) == 0:
                return
        if attr:
            txt = (attr, text)
        else:
            for rule in self.TEXT_RE:
                regxp = rule[0].match(text)
                if regxp:
                    txt = rule[1](regxp, text)
                    break
            else:
                txt = (urwid.AttrSpec('#999', '#000'), text)
        if txt:
            text = txt[1]
            nc = [(int(x,16) if int(x,16)>=15 else int(x,16)+2)
                    for x in txt[0].foreground[1::]]
            nc = '#{:x}{:x}{:x}'.format(*nc)
            htxt = []
            ii = 0
            for m in self.hl_rule.finditer(text):
                if m.start()-ii > 0:
                    htxt.append(text[ii:m.start()])
                htxt.append((urwid.AttrSpec(nc 
                            +(',bold' if m.group() == self.fics_user else ''),
                                txt[0].background), m.group()))
                ii = m.end()
            if ii < len(text):
                htxt.append(text[ii::])
            if len(htxt):
                txt = (txt[0], htxt)
            if self.body_size:
                if (len(self.txt_list.body)-1 ==
                       self.txt_list.calculate_visible(self.body_size)[0][2]):
                    self.txt_list.body.append(urwid.Text(txt))
                    self.txt_list.set_focus(len(self.txt_list.body)-1)
                else:
                    self.txt_list.body.append(urwid.Text(txt))
            else:
                self.txt_list.body.append(urwid.Text(txt))
                self.txt_list.set_focus(len(self.txt_list.body)-1)

    def read_pipe(self, txt):
        text = txt.rstrip().decode()
        for line in text.split('\n'):
            self.print(line)

    def redraw(self):
        self.main_loop.draw_screen()

    def connect_mainloop(self):
        self.glel = urwid.GLibEventLoop()
        #self.connect_at_start_idle_hdl = self.glel.enter_idle(
                                                #self.connect_at_start)
        ml = urwid.MainLoop(self, handle_mouse=True, event_loop=self.glel)
        self.main_loop = ml
        ml.run()

    def connect_at_start(self):
        self.glel.remove_enter_idle(self.connect_at_start_idle_hdl)
        self.cmd_line.cmd_connect((0,), '')
        return None

    # FICS
    def connect_fics(self):
        fics = telnetlib.Telnet("freechess.org", port=5000)
        self.read_pipe(fics.read_until(b"login: ").replace(b'\r',b''))
        self.cmd_line.insert_text(u".")
        self.main_loop.draw_screen()
        fics.write(self.fics_user.encode('utf-8') + b"\n")
        self.read_pipe(fics.read_until(b":").replace(b'\r',b''))
        self.cmd_line.insert_text(u".")
        self.main_loop.draw_screen()
        fics.write(self.fics_pass.encode('utf-8') + b"\n")
        self.read_pipe(fics.read_until(b"fics% ").replace(b'\r',b''))
        self.cmd_line.insert_text(u".")
        self.main_loop.draw_screen()
        fics.write(b"iset gameinfo" + b"\n")
        self.read_pipe(fics.read_until(b"fics% ").replace(b'\r',b''))
        self.cmd_line.insert_text(u".")
        self.main_loop.draw_screen()
        fics.write(b"style 12" + b"\n")
        self.fics = fics
        self.pipe = self.main_loop.watch_pipe(self.read_pipe)
        self.fics_thread = threading.Thread(target=self.fics_read)
        self.fics_thread.start()

    def fics_read(self):
        try:
            while not self.die:
                data = self.fics.read_until(b"\n\r").strip(b'\r')
                dstr = datetime.datetime.strftime(datetime.datetime.now(),
                                                  '%Y-%m-%d %H:%M:%S ')
                if self.log:
                    self.log.write(dstr+str(data)+'\n')
                    self.log.flush()
                if data != b'fics% \n':
                    os.write(self.pipe, data)
            self.fics.close()
        except EOFError:
            del self.fics

    # localhost
    #def connect_fics(self):
        #fics = telnetlib.Telnet("localhost", port=5000)
        #self.fics = fics
        #self.pipe = self.main_loop.watch_pipe(self.read_pipe)
        #self.fics_thread = threading.Thread(target=self.fics_read)
        #self.fics_thread.start()

    #def fics_read(self):
        #try:
            #while not self.die:
                #data = self.fics.read_until(b"\n")
                #if data != b'fics% \n':
                    #os.write(self.pipe, data)
            #self.fics.close()
        #except EOFError:
            #del self.fics

    def send_cmd(self, cmd, echo=False):
        if hasattr(self, 'fics'):
            if echo:
                self.print("> "+cmd, urwid.AttrSpec('#dd0', '#000'))
            self.fics.write(cmd.encode()+b'\n')

