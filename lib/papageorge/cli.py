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

import telnetlib, urwid, threading, os, re, datetime, time
from urwid.escape import process_keyqueue
from gi.repository import Gtk, Gdk

if __name__ == '__main__':
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config

class HandleCommands(Gtk.Window):
    def __init__(self, cli, handle):
        self.cli = cli
        self.handle = handle
        Gtk.Window.__init__(self, title=handle)
        self.set_default_size(1,1)
        self.set_border_width(10)
        self.set_modal(True)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        Box = Gtk.VBox().new(False, 1)

        frame = Gtk.Frame()
        Box.pack_start(frame, False, False, 0)
        vbox = Gtk.VBox().new(True, 1)
        frame.add(vbox)
        button = Gtk.Button.new_with_mnemonic("_Match")
        button.command = lambda x: 'match {} {} {}'.format(x.handle, 
                                            x.match_time.get_value_as_int(),
                                            x.match_incr.get_value_as_int())
        button.command_send = True
        button.connect("clicked", self.on_button_clicked)
        vbox.pack_start(button, False, False, 0)

        hbox = Gtk.HBox().new(True, 1)
        hbox.pack_start(Gtk.Label().new('Time (min)'), False, False, 0)
        self.match_time = Gtk.SpinButton()
        self.match_time.set_adjustment(Gtk.Adjustment(5, 0, 100, 1, 10, 0))
        self.match_time.get_adjustment().configure(5, 0, 100, 1, 10, 0)
        self.match_time.set_activates_default(True)
        hbox.pack_start(self.match_time, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        hbox = Gtk.HBox().new(True, 1)
        hbox.pack_start(Gtk.Label().new('Incr (sec)'), False, False, 0)
        self.match_incr = Gtk.SpinButton()
        self.match_incr.set_adjustment(Gtk.Adjustment(10, 0, 100, 1, 10, 0))
        self.match_incr.get_adjustment().configure(10, 0, 100, 1, 10, 0)
        self.match_incr.set_activates_default(True)
        hbox.pack_start(self.match_incr, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        for label, command, command_send in [
                ('_Tell', lambda x: 'tell {} '.format(x.handle), False),
                ('_Finger', lambda x: 'finger {}'.format(x.handle), True)
                ]:
            button = Gtk.Button.new_with_mnemonic(label)
            button.command = command
            button.command_send = command_send
            button.connect("clicked", self.on_button_clicked)
            Box.pack_start(button, False, False, 0)

        button = Gtk.Button.new_with_mnemonic("_Cancel")
        button.connect("clicked", self.on_cancel)
        Box.pack_start(button, False, False, 0)
        self.add(Box)
        self.realize()
        self.get_window().set_transient_for(Gdk.Screen.get_default().get_active_window())
        self.show_all()

    def on_button_clicked(self, button):
        #self.parent.cli.send_cmd(button.command(self), True)
        if button.command_send:
            self.cli.send_cmd(button.command(self), echo=True)
        else:
            self.cli.cmd_line.set_edit_text(button.command(self))
            self.cli.cmd_line.set_edit_pos(999)
        self.cli.set_focus('footer')
        self.cli.redraw()
        self.destroy()

    def key_cmd(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def on_cancel(self, widget):
        self.destroy()

class CmdLine(urwid.Edit):
    def __init__(self, prompt, cli):
        self.cli = cli
        self.WORD_RE = re.compile('\w+')
        self.cli_commands = {
                'q': self.cmd_quit,
                'b': self.cmd_board,
                'c': self.cmd_connect,
                's': self.cmd_seek_graph,
                'd': self.cmd_debug,
        }
        self.key_commands = [
               ('f5'         , self.cmd_seek_graph),
               ('ctrl d'     , self.cmd_quit),
               ('ctrl v'     , self.cmd_clear_cmdline),
               ('esc'        , self.cmd_clear_cmdline),
               ('ctrl left'  , self.cmd_prev_word),
               ('ctrl right' , self.cmd_next_word),
               ('up'         , self.cmd_prev_cmd),
               ('down'       , self.cmd_next_cmd),
        ]
        for accel, txt in config.console.command:
            self.key_commands.append((accel,
                lambda size, key, txt=txt: self.cli.send_cmd(eval(txt),
                                                                echo=True)))
        self.cmd_history = list()
        self.cmd_history_idx = 0
        return super(CmdLine, self).__init__(prompt, wrap='clip')

    def cmd_debug(self, size, key):
        self.cli.print('boards = {}'.format(self.gui.boards))
        return None
        
    def cmd_quit(self, size, key):
        self.cli.exit()

    def cmd_board(self, size, key):
        self.gui.new_board()
        self.set_edit_text('')
        return None

    def cmd_seek_graph(self, size, key):
        if not self.gui.seek_graph:
            self.gui.new_seek_graph()
        return None

    def cmd_connect(self, size, key):
        self.set_edit_text('')
        self.insert_text('Connecting ')
        self.cli.main_loop.draw_screen()
        self.cli.connect_fics()
        self.set_edit_text('')
        return None

    def cmd_clear_cmdline(self, size, key):
        self.set_edit_text('')
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
            self.set_edit_text('{}'.format(
                self.cmd_history[self.cmd_history_idx]))
            self.set_edit_pos(999)
        else:
            self.set_edit_text('')
        return None

    def cmd_next_cmd(self, size, key):
        self.cmd_history_idx = self.cmd_history_idx + 1
        if self.cmd_history_idx > -1:
            self.cmd_history_idx = 0
        if self.cmd_history_idx < 0:
            self.set_edit_text('{}'.format(
                self.cmd_history[self.cmd_history_idx]))
            self.set_edit_pos(999)
        else:
            self.set_edit_text('')
        return None

    def keypress(self, size, key):
        cmd_f = next((c[1] for c in self.key_commands if key == c[0] ), False )
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
            self.cli.print('{}'.format(self.cli_commands.keys()))
            self.cmd_history_idx = 0
            self.cmd_history.append(cmd)
            self.set_edit_text('')
            return None
        elif cmd[0] == '%':
            if cmd[1::] in self.cli_commands.keys():
                self.cmd_history_idx = 0
                self.cmd_history.append(cmd)
                return self.cli_commands[cmd[1::]](size, cmd[1::])
            else:
                self.cli.print(cmd+' verstehe ich nicht ... ')
                return None
        elif hasattr(self.cli, 'fics'):
            self.cli.print('> '+cmd,
                             urwid.AttrSpec(config.console.echo_color, 'default'))
            self.cli.fics.write(cmd.encode()+b'\n')
            self.cmd_history_idx = 0
            self.cmd_history.append(cmd)
            self.set_edit_text('')
            return None
        if not cmd:
            return None
        self.cli.print('{} - Not connected!!'.format(cmd))

class ConsoleText(urwid.Text):
    def __init__(self, body, cli):
        self.cli = cli
        return super(ConsoleText, self).__init__(body)

    def mouse_event(self, size, event, button, col, row, focus):
        txt_row = self.render(size).text[row].decode('UTF-8').strip()
        word = None
        if txt_row and len(txt_row) > 0:
            word = next((m.group() for m in
                             self.cli.word_rule.finditer(txt_row)
                                 if m.start() <= col and col <= m.end()), None)
        return (self, txt_row, word, self.get_text()[0])

class CLI(urwid.Frame):

    def __init__(self, fics_pass, logfd):
        self.fics_pass = fics_pass
        self.logfd = logfd
        self.TEXT_RE = [
            ( # forward backward - DROP
              re.compile('^fics% Game \w+: \w+ (goes forward|backs up)'),
                lambda regexp, txt: False),
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
        for restring, hcolor in config.console.highlight:
            if hcolor == 'palette':
                self.TEXT_RE.insert(0, (re.compile(restring),
                    lambda regexp, txt, hcolor=hcolor: (
                        urwid.AttrSpec(self.palette(regexp.group('id')),
                            'default'), txt)))
            else:
                self.TEXT_RE.insert(0, (re.compile(restring),
                    lambda regexp, txt, hcolor=hcolor: (urwid.AttrSpec(hcolor,
                                                            'default'), txt)))
        self.re_rules()
        self._palette = list()
        for hcolor in config.console.palette:
            self._palette.append( (hcolor, list()) )
        self.body_size = None
        self.die = 0
        self.txt_list = urwid.ListBox(urwid.SimpleFocusListWalker(
                                                    [ConsoleText('', self)]))
        self.cmd_line = CmdLine('> ', self)
        self._wait_for_sem = threading.Semaphore(0)
        self._wait_for_txt = None
        self._last_AB = None
        return super(CLI, self).__init__(self.txt_list,
                        footer=self.cmd_line, focus_part='footer')

    def re_rules(self):
        check     = '[+#]'
        rank      = '[1-8]'
        file      = '[a-h]'
        piece     = '[KNBQR]'
        promotion = 'x?{}[18]=(?!K){}'.format(file, piece)
        pawnmove  = '(?:{}?x)?{}(?![18]){}'.format(file, file, rank)
        stdmove   = '{}{}?{}?x?{}{}'.format(piece, file, rank, file, rank)
        castling  = 'O-O(?:-O)?'
        handle    = '[a-z]{3,}'
        san = '((?:{}|{}|{}|{}){}?)'.format(
                    promotion,castling,pawnmove,stdmove,check)
        highlight = '((?:{}|(?:{}))'.format(san[1::],config.fics_user)
        handle = '({})'.format(handle)
        self.san_rule = re.compile(san)
        self.hl_rule = re.compile(highlight)
        self.handle_rule = re.compile(handle, re.IGNORECASE)
        self.word_rule = re.compile('[+#=\w-]+')
        self.AB_gn_rule = re.compile('^:\[Game (\d+)\]')

    def palette(self, id):
        if len(self._palette) == 0:
            return '#999'
        c = next(( c for c in self._palette if id in c[1] ), None)
        if not c:
            c = min(self._palette, key = lambda c: len(c[1]))
            c[1].append(id)
        return c[0]

    def palette_remove(self, id):
        c = next(( c for c in self._palette if id in c[1] ), None)
        if c:
            c[1].remove(id)

    def key_from_gui(self, key):
        self.set_focus('footer')
        # ugly hack! why?!
        key = (10 if key == 65293 else 
                8 if key == 65288 else
                key)
        key = process_keyqueue([key], False)[0][0]
        self.cmd_line.keypress(self.body_size, key)

    def continuation(self, regexp, txt):
        txt_ = self.txt_list.body.pop().get_text()
        self.txt_list.body.append(ConsoleText((txt_[1][0][0], 
                                             txt_[0]+' '+regexp.groups()[0]),
                                             self))
        pos = len(self.txt_list.body)-1
        self.txt_list.set_focus(pos)
        return False

    def send_AB_moves(self, game_number, moves):
        self.print('> Stopping Analysisbot to avoid jamming',
                urwid.AttrSpec(config.console.echo_color, 'default'))
        self.send_cmd('tell Analysisbot stop')
        for move in moves:
            if not self.send_cmd(move,wait_for='Game {}: {} moves: {}'.format(
                                game_number,config.fics_user,move)):
                self.print('> An error occured sending',
                    urwid.AttrSpec(config.console.echo_color, 'default'))
                break
        self.print('> '+' '.join(moves),
                urwid.AttrSpec(config.console.echo_color, 'default'))
        self.print('> Restarting Analysisbot in 2 secs ...',
                urwid.AttrSpec(config.console.echo_color, 'default'))
        self.redraw()
        time.sleep(2)
        self.send_cmd('tell Analysisbot obsme', echo=True)

    def may_I_move(self):
        return next((b for b in self.cmd_line.gui.boards
                      if b.state.kind in ['playing', 'examining']), False )

    def mouse_event(self, size, event, button, col, row, focus):
        # No sirve con vtwheel
        self.body_size = size
        if event == 'mouse press':
            if button == 5.0:
                self.keypress(size, 'page down')
            elif button == 4.0:
                self.keypress(size, 'page up')
            elif button == 1.0:
                eggs = super(CLI, self).mouse_event(size, event, button,
                                                     col, row, focus)
                if isinstance(eggs, tuple):
                    widget, txt_row, word, txt_line = eggs
                    if txt_row and len(txt_row) and word:
                        m = self.san_rule.match(word) 
                        if m and self.may_I_move():
                            moves = self.san_rule.findall(txt_line)
                            moves = moves[:moves.index(word)+1]
                            if (':[Game ' in txt_line and
                                    'Book' not in txt_line and
                                    len(moves) > 1 and
                                   widget == self._last_AB):
                                gn = self.AB_gn_rule.match(txt_line).group(1)
                                threading.Thread(target=self.send_AB_moves,
                                        args=(gn,moves)).start()
                            else:
                                self.send_cmd(word, echo=True)
                        else:
                            m = self.handle_rule.match(word)
                            if m:
                                HandleCommands(self, m.group())
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
            b.set_interruptus()
        return (urwid.AttrSpec(config.console.game_end_color, 'default'), txt)

    def unexamine(self, regexp, txt):
        self.palette_remove(regexp.group(1))
        b = self.board_with_number(int(regexp.group(1)))
        if b:
            b.set_interruptus()
        return (urwid.AttrSpec(config.console.game_end_color, 'default'), txt)

    def strip_prompt(self, regexp, txt):
        self.print(regexp.group(1)) 
        return False

    def keypress(self, size, key):
        self.set_focus('footer')
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
            self.fics.write('fi\n'.encode())
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
                txt = (urwid.AttrSpec(config.console.default_color, 'default'), text)
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
                htxt.append((urwid.AttrSpec(nc +',bold',
                                txt[0].background), m.group()))
                ii = m.end()
            if ii < len(text):
                htxt.append(text[ii::])
            if len(htxt):
                txt = (txt[0], htxt)
            if ':[Game ' in text:
                self._last_AB = ctxt = ConsoleText(txt, self)
            else:
                ctxt = ConsoleText(txt, self)
            if self.body_size:
                if (len(self.txt_list.body)-1 ==
                       self.txt_list.calculate_visible(self.body_size)[0][2]):
                    self.txt_list.body.append(ctxt)
                    self.txt_list.set_focus(len(self.txt_list.body)-1)
                else:
                    self.txt_list.body.append(ctxt)
            else:
                self.txt_list.body.append(ctxt)
                self.txt_list.set_focus(len(self.txt_list.body)-1)

    def read_pipe(self, txt):
        text = txt.rstrip().decode()
        for line in text.split('\n'):
            if self._wait_for_txt and (self._wait_for_txt in line):
                self._wait_for_sem.release()
            self.print(line)

    def redraw(self):
        self.main_loop.draw_screen()

    def connect_mainloop(self):
        self.glel = urwid.GLibEventLoop()
        self.connect_at_start_idle_hdl = self.glel.enter_idle(
                                                self.connect_at_start)
        self.main_loop = urwid.MainLoop(self,
                handle_mouse=config.console.handle_mouse, event_loop=self.glel)
        self.main_loop.run()

    def connect_at_start(self):
        self.glel.remove_enter_idle(self.connect_at_start_idle_hdl)
        self.cmd_line.cmd_connect((0,), '')
        return None

    # FICS
    def connect_fics(self):
        fics = telnetlib.Telnet('freechess.org', port=5000)
        # login:
        data = fics.read_until(b'login: ').replace(b'\r',b'')
        self.log(data)
        self.read_pipe(data)
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        # > login
        data = config.fics_user.encode('utf-8') + b'\n'
        self.log(data, True)
        fics.write(data)
        # pass:
        data = fics.read_until(b':').replace(b'\r',b'')
        if config.fics_user == 'guest':
            config.fics_user = data.split()[-1].strip(b'":').decode('utf-8')
            self.re_rules()
        self.log(data)
        self.read_pipe(data)
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        # > pass
        data = self.fics_pass.encode('utf-8') + b'\n'
        self.log(data, True)
        fics.write(data)
        # prompt
        data = fics.read_until(b'fics% ').replace(b'\r',b'')
        self.log(data)
        self.read_pipe(data)
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        for cmd in config.general.startup_command:
            # > startup commands
            data = cmd.encode('utf-8')+b'\n'
            self.log(data, True)
            fics.write(data)
            # prompt
            data = fics.read_until(b'fics% ').replace(b'\r',b'')
            self.log(data)
            self.read_pipe(data)
            self.cmd_line.insert_text('.')
            self.main_loop.draw_screen()
        self.fics = fics
        self.pipe = self.main_loop.watch_pipe(self.read_pipe)
        self.fics_thread = threading.Thread(target=self.fics_read)
        self.fics_thread.start()

    def fics_read(self):
        try:
            while not self.die:
                data = self.fics.read_until(b'\n\r').strip(b'\r')
                self.log(data)
                if data not in [b'fics% \n', b'fics% \x07\n', b'\x07\n']:
                    os.write(self.pipe, data)
            self.fics.close()
        except EOFError:
            del self.fics

    def log(self, data, sent=False):
        if self.logfd:
            dstr = datetime.datetime.strftime(datetime.datetime.now(),
                                          '%Y-%m-%d %H:%M:%S ')
            direction = '> ' if sent else '< '
            self.logfd.write(dstr+direction+str(data)+'\n')
            self.logfd.flush()

    # localhost
    #def connect_fics(self):
        #fics = telnetlib.Telnet('localhost', port=5000)
        #self.fics = fics
        #self.pipe = self.main_loop.watch_pipe(self.read_pipe)
        #self.fics_thread = threading.Thread(target=self.fics_read)
        #self.fics_thread.start()

    #def fics_read(self):
        #try:
            #while not self.die:
                #data = self.fics.read_until(b'\n')
                #if data != b'fics% \n':
                    #os.write(self.pipe, data)
            #self.fics.close()
        #except EOFError:
            #del self.fics

    def send_cmd(self, cmd, echo=False, wait_for=None):
        if hasattr(self, 'fics'):
            if wait_for:
                self._wait_for_txt = wait_for
            data = cmd.encode()+b'\n'
            self.log(data, sent=True)
            self.fics.write(data)
            if wait_for:
                if not self._wait_for_sem.acquire(timeout=5):
                    self._wait_for_txt = None
                    return False
                self._wait_for_txt = None
            if echo:
                self.print('> '+cmd,
                        urwid.AttrSpec(config.console.echo_color, 'default'))
            return True

