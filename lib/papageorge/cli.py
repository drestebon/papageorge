# cli - command-line interface

# Copyright (C) 2016 DrEstebon

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

import telnetlib, urwid, threading, os, re, time
from subprocess import Popen, PIPE
from socket import gethostbyname
from urwid.escape import process_keyqueue
from gi.repository import Gtk, Gdk

if __name__ == '__main__':
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config
from papageorge.general import *
from papageorge.pgn import Pgn

class ChallengeDialog(Gtk.Window):
    def __init__(self, txt):
        Gtk.Window.__init__(self, title='Challenge')
        self.set_default_size(1,1)
        self.set_border_width(5)
        self.set_modal(True)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        Box = Gtk.VBox().new(False, 1)
        txt = ('\n'+txt+
          '\nYou can "accept" or "decline", or propose different parameters\n')
        Box.pack_start(Gtk.Label().new(txt), False, False, 0)
        hbox = Gtk.HBox().new(False, 1)
        Box.pack_start(hbox, False, False, 0)
        button = Gtk.Button.new_with_mnemonic("_Cancel")
        button.connect("clicked", self.on_cancel)
        hbox.pack_end(button, False, False, 0)
        for label, command in [
                ('_Decline', lambda x: 'decline'),
                ('_Accept', lambda x: 'accept')
                ]:
            button = Gtk.Button.new_with_mnemonic(label)
            button.command = command
            button.connect("clicked", self.on_button_clicked)
            hbox.pack_end(button, False, False, 0)
        self.add(Box)
        self.realize()
        self.get_window().set_transient_for(
                Gdk.Screen.get_default().get_active_window())
        self.show_all()

    def on_button_clicked(self, button):
        config.cli.send_cmd(button.command(self),echo=True,save_history=False)
        config.cli.set_focus('footer')
        config.cli.redraw()
        self.destroy()

    def key_cmd(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def on_cancel(self, widget):
        self.destroy()


class HandleCommands(Gtk.Window):
    def __init__(self, handle):
        config.update_handle(handle)
        self.handle = handle
        Gtk.Window.__init__(self, title=handle)
        self.set_default_size(1,1)
        self.set_border_width(5)
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
        self.get_window().set_transient_for(
                Gdk.Screen.get_default().get_active_window())
        self.show_all()

    def on_button_clicked(self, button):
        if button.command_send:
            config.cli.send_cmd(button.command(self), echo=True, save_history=False)
        else:
            config.cli.cmd_line.set_edit_text(button.command(self))
            config.cli.cmd_line.set_edit_pos(999)
        config.cli.set_focus('footer')
        config.cli.redraw()
        self.destroy()

    def key_cmd(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def on_cancel(self, widget):
        self.destroy()

class CompleteMenu:
    def __new__(cls, cmd_line):
        cltxt = cmd_line.edit_text
        cmd = cltxt.split()
        if not cltxt:
            option = config.FICS_COMMANDS
        elif len(cmd) == 1 and cltxt and cltxt[-1] != ' ':
            option = [x for x in config.FICS_COMMANDS
                                        if not x.find(cmd[0])]
        elif len(cmd) > 1 and cltxt[-1] != ' ':
            option = [x for x in config.FICS_HANDLES
                                        if not x.lower().find(cmd[-1].lower())]
        else:
            option = config.FICS_HANDLES
        if not option:
            return None
        else:
            self = object.__new__(cls)
            self.option = option
            self.cltxt = cltxt
            self.cmd = cmd
            self.cmd_line = cmd_line
            return self

    def __init__(self, cmd_line):
        self.idx = -1
        self.next()
        cmd_line.menu_placeholder.original_widget = self.get_menu()

    def get_menu(self):
        l = list(self.option)
        l[self.idx] = (urwid.AttrSpec('#000, bold', '#888'), l[self.idx])
        for i in range(len(l)-1, 0, -1):
            l.insert(i, ' ')
        return urwid.Text((urwid.AttrSpec('#ddd', '#111'), l))

    def next(self):
        self.idx = (self.idx + 1) % len(self.option)
        self.complete()

    def prev(self):
        self.idx = (self.idx - 1 + len(self.option)) % len(self.option)
        self.complete()

    def complete(self):
        if self.cltxt and self.cltxt[-1] != ' ':
            if len(self.cmd)>1:
                self.cmd_line.set_edit_text(' '.join(self.cmd[:-1])+' '
                        +self.option[self.idx])
            else:
                self.cmd_line.set_edit_text(self.option[self.idx])
        else:
            self.cmd_line.set_edit_text(self.cltxt+self.option[self.idx])
        self.cmd_line.set_edit_pos(999)
        self.cmd_line.menu_placeholder.original_widget = self.get_menu()

    def finish(self, complete):
        if not complete:
            self.cmd_line.set_edit_text(self.cltxt)
        self.cmd_line.complete_menu = None
        self.cmd_line.menu_placeholder.original_widget = urwid.Pile([])

class CmdLine(urwid.Edit):
    def __init__(self, prompt):
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
               ('tab'        , self.cmd_complete_menu),
               ('shift tab'  , self.cmd_complete_menu),
        ]
        for accel, txt in config.console.command:
            self.key_commands.append((accel,
                lambda size, key, txt=txt: config.cli.send_cmd(eval(txt),
                                                                echo=True)))
        self.cmd_history = list()
        self.cmd_history_idx = 0
        self.complete_menu = None
        return super(CmdLine, self).__init__(prompt, wrap='clip')

    def cmd_debug(self, size, key):
        self.set_edit_text('')
        config.cli.print(' '.join([y.move for y in config.gui.games[0]._history]))
        return None
        
    def cmd_quit(self, size, key):
        config.cli.exit()

    def cmd_board(self, size, key):
        config.gui.new_board()
        self.set_edit_text('')
        return None

    def cmd_seek_graph(self, size, key):
        if not config.gui.seek_graph:
            config.gui.new_seek_graph()
        return None

    def cmd_connect(self, size, key):
        self.set_edit_text('')
        self.insert_text('Connecting ')
        config.cli.main_loop.draw_screen()
        config.cli.connect_fics()
        self.set_edit_text('')
        return None

    def cmd_clear_cmdline(self, size, key):
        if self.complete_menu:
            self.complete_menu.finish(False)
        else:
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

    def cmd_complete_menu(self, size, key):
        if self.complete_menu:
            if key.find('shift'):
                self.complete_menu.next()
            else:
                self.complete_menu.prev()
        else:
            self.complete_menu = CompleteMenu(self)
        return True

    def keypress(self, size, key):
        cmd_f = next((c[1] for c in self.key_commands if key == c[0] ), False )
        if cmd_f:
            if cmd_f(size, key):
                return None
        if key != 'enter':
            if self.complete_menu:
                self.complete_menu.finish(True)
            return super(CmdLine, self).keypress((size[0] if size else 0,), key)
        if self.complete_menu:
            self.complete_menu.finish(True)
            return None
        cmd = self.edit_text
        if len(cmd) < 1:
            return None
        elif cmd[0] == '?':
            config.cli.print('{}'.format(self.cli_commands.keys()))
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
                config.cli.print(cmd+' verstehe ich nicht ... ')
                return None
        elif hasattr(config.cli, 'fics'):
            config.cli.send_cmd(cmd, echo=True)
            self.set_edit_text('')
            return None
        if not cmd:
            return None
        config.cli.print('{} - Not connected!!'.format(cmd))

class ConsoleText(urwid.Text):
    def __init__(self, body):
        return super(ConsoleText, self).__init__(body)

    def mouse_event(self, size, event, button, col, row, focus):
        txt_row = self.render(size).text[row].decode('UTF-8').strip()
        word = None
        if txt_row and len(txt_row) > 0:
            word = next((m.group() for m in
                             config.cli.word_rule.finditer(txt_row)
                                 if m.start() <= col and col <= m.end()), None)
        return (self, txt_row, word, self.get_text()[0])

class FicsTimesealConnection:
    def __init__(self):
        self._proc = Popen([config.general.timeseal,
                        gethostbyname('freechess.org'), '5000'],
                        stdin=PIPE, stdout=PIPE)

    def write(self, data):
        self._proc.stdin.write(data)
        self._proc.stdin.flush()

    def read_until(self, data, timeout=None):
        idata = b''
        if timeout:
            st = time.time()
        while True:
            idata = idata+self._proc.stdout.read1(262144)
            if data in idata:
                return idata
            if timeout and (time.time()-st) > timeout:
                return False
            time.sleep(0.1)

    def close(self):
        self._proc.terminate()

def fics_filter(txt):
    if not isinstance(txt, bytes):
        return txt
    for x in [b'\r', b'fics% ', b'fics%', b'\x07']:
        txt = txt.replace(x,b'')
    txt = txt.replace(b'\x01', b'   ')
    txt = txt.replace(b'\xff', b' ')
    txt = txt.replace(b'\xfb', b'\u00b9')
    return txt.rstrip().lstrip(b'\n')

class CLI(urwid.Frame):
    def __init__(self, fics_pass):
        self.fics_pass = fics_pass
        self.TEXT_RE = [
            ( # forward backward - DROP
              re.compile('^Game \w+: \w+ (goes forward|backs up)'),
                lambda regexp, txt: False),
            ( re.compile('^<s[cr]*>'),
                self.update_seek_graph),
            ( re.compile('^<12>'),
                self.style12),
            ( re.compile('^<g1>'),
                self.game_info),
            ( re.compile('^{Game (\d+) .+}( [012/-]+)?'),
                self.interruptus),
            ( re.compile('^Challenge:'),
                self.challenge),
            ( re.compile('^(?P<opponent>\w{3,}) (offers|would|requests)'),
                self.offer),
            ( re.compile('^You are no longer examining game (\d+)'),
                self.unexamine),
            ( re.compile('^Removing game (\d+) from observation list.'),
                self.unexamine),
            ( re.compile('^\\\\\s+(.+)'),
                self.continuation),
            ( re.compile('^fics% ((\s|.|\n)+)'),
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
                                                    [ConsoleText('')]))
        self.cmd_line = CmdLine('> ')
        self.cmd_line.menu_placeholder = urwid.WidgetPlaceholder(urwid.Pile([]))
        bottom = urwid.WidgetDisable(self.cmd_line.menu_placeholder)
        bottom = urwid.Pile([col, self.cmd_line])
        self._wait_for_sem = threading.Semaphore(0)
        self._wait_for_txt = None
        self._wait_for_buf = list()
        self.ML_recording = False
        self._last_AB = None
        self.handle_commands = None
        self.temp_buff = None
        # return super(CLI, self).__init__(self.txt_list,
                        # footer=self.cmd_line, focus_part='footer')
        return super(CLI, self).__init__(self.txt_list,
                        footer=bottom, focus_part='footer')

    def re_rules(self):
        check     = '[+#]'
        rank      = '[1-8]'
        file      = '[a-h]'
        piece     = '[KNBQR]'
        promotion = '{}?x?{}[18]=(?!K){}'.format(file, file, piece)
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
        if key == 65506:
            return
        elif key == 65056:
            key = 'shift tab'
        else:
            key = (10 if key == 65293 else
                    9 if key == 65289 else
                    8 if key == 65288 else
                    key)
            key = process_keyqueue([key], False)[0][0]
        self.cmd_line.keypress(self.body_size, key)

    def continuation(self, regexp, txt):
        txt_ = self.txt_list.body.pop().get_text()
        self.txt_list.body.append(ConsoleText((txt_[1][0][0], 
                                         txt_[0]+' '+regexp.groups()[0])))
        pos = len(self.txt_list.body)-1
        self.txt_list.set_focus(pos)
        return False

    def send_AB_moves(self, moves):
        self.print('> Stopping Analysisbot to avoid jamming',
                urwid.AttrSpec(config.console.echo_color, 'default'))
        self.send_cmd('tell Analysisbot stop')
        self.send_moves(moves)
        self.print('> Restarting Analysisbot in 2 secs ...',
                urwid.AttrSpec(config.console.echo_color, 'default'))
        self.redraw()
        time.sleep(2)
        self.send_cmd('tell Analysisbot obsme', echo=True)

    def may_I_move(self):
        return next((g for g in config.gui.games
                      if g.kind & (KIND_PLAYING | KIND_EXAMINING)), False )

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
                                gn = int(self.AB_gn_rule.match(txt_line).group(1))
                                g = self.game_with_number(gn)
                                p = Pgn(txt=' '.join(moves), ic=g._history[-1])
                                threading.Thread(target=self.send_AB_moves,
                                        args=(p.main_line[1::],)).start()
                            else:
                                self.send_cmd(word, echo=True)
                        else:
                            m = self.handle_rule.match(word)
                            if m:
                                if self.handle_commands:
                                    self.handle_commands.destroy()
                                self.handle_commands = \
                                        HandleCommands(m.group())
        return True

    def update_seek_graph(self, regexp, txt):
        if config.gui.seek_graph:
            config.gui.seek_graph.update(txt[regexp.pos::])
        else:
            pass
        return False

    def game_with_number(self, n):
        return next((g for g in config.gui.games
                      if g.number == n), False )

    def game_with_opponent(self, txt):
        return next((g for g in config.gui.games
                      if g.opponent == txt), False )

    def style12(self, regexp, txt):
        config.gui.style12(txt)
        return False

    def game_info(self, regexp, txt):
        g = self.game_with_number(int(txt.split()[1]))
        if g:
            g.set_gameinfo(txt)
        else:
            config.gui.new_game(game_info=txt)
        return False

    def interruptus(self, regexp, txt):
        g = self.game_with_number(int(regexp.group(1)))
        if g:
            g.set_interruptus(regexp.group(2))
        return (urwid.AttrSpec(config.console.game_end_color, 'default'), txt)

    def challenge(self, regexp, txt):
        ChallengeDialog(txt)
        return (urwid.AttrSpec(config.console.game_end_color, 'default'), txt)

    def offer(self, regexp, txt):
        g = self.game_with_opponent(regexp.group('opponent'))
        if g and g.board:
            g.board.offer(txt)
        return (urwid.AttrSpec(config.console.game_end_color, 'default'), txt)

    def unexamine(self, regexp, txt):
        self.palette_remove(regexp.group(1))
        g = self.game_with_number(int(regexp.group(1)))
        if g:
            if g.kind & KIND_EXAMINING and not g.kind & KIND_OBSERVING:
                config.gui.game_destroy(g)
            else:
                g.set_interruptus()
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
                    if 'handle' in regxp.groupdict():
                        config.update_handle(regxp.group('handle'))
                    txt = rule[1](regxp, text)
                    break
            else:
                txt = (urwid.AttrSpec(config.console.default_color, 'default'),
                        text)
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
                self._last_AB = ctxt = ConsoleText(txt)
            else:
                ctxt = ConsoleText(txt)
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
        if config.general.timeseal:
            self.fics = FicsTimesealConnection()
        else:
            self.fics = telnetlib.Telnet('freechess.org', port=5000)
        # login:
        data = fics_filter(self.fics.read_until(b'login: '))
        config.log(data)
        self.read_pipe(data+b'<_>')
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        # > login
        data = config.fics_user.encode('ascii') + b'\n'
        config.log(data, True)
        self.fics.write(data)
        # pass:
        data = fics_filter(self.fics.read_until(b':'))
        if config.fics_user == 'guest':
            config.fics_user = data.split()[-1].strip(b'":').decode('ascii',
                                                                    'ignore')
        else:
            config.fics_user = data.split()[0].strip(b'"').decode('ascii',
                                                                    'ignore')
        config.FICS_HANDLES.append(config.fics_user)
        self.re_rules()
        config.log(data)
        self.read_pipe(data+b'<_>')
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        # > pass
        data = self.fics_pass.encode('ascii') + b'\n'
        config.log(data, True)
        self.fics.write(data)
        # prompt
        data = fics_filter(self.fics.read_until(b'fics% '))
        config.log(data)
        self.read_pipe(data+b'<_>')
        self.cmd_line.insert_text('.')
        self.main_loop.draw_screen()
        # > startup commands
        for cmd in config.general.startup_command:
            self.send_cmd(cmd, save_history=False, record_handle=False)
            self.cmd_line.insert_text('.')
            self.main_loop.draw_screen()
        self.pipe = self.main_loop.watch_pipe(self.read_pipe)
        self.fics_thread = threading.Thread(target=self.fics_read)
        self.fics_thread.start()

    def read_pipe(self, txt):
        txt = txt.decode('ascii','ignore')
        if txt and txt[-3::] != '<_>':
            txt = txt.split('<_>')
            if len(txt) == 1 and self.temp_buff:
                temp_buff = self.temp_buff + txt.pop()
            else:
                temp_buff = txt.pop()
        else:
            txt = txt.split('<_>')
            if len(txt) and not txt[-1]:
                txt.pop()
            temp_buff = None
        if txt and self.temp_buff:
            txt[0] = self.temp_buff + txt[0]
        for foo in txt:
            for line in foo.split('\n'):
                self.print(line)
        self.temp_buff = temp_buff

    def fics_read(self):
        try:
            while not self.die:
                data = self.fics.read_until(b'fics% ',
                # data = self.fics.read_until(b'\n\r',
                           timeout=(None
                            if config.general.connection_test_timeout == 0 else
                               config.general.connection_test_timeout))
                if not data:
                    threading.Thread(target=self.test_connection).start()
                elif data != b'fics% \n\r':
                    data = fics_filter(data)
                    config.log(data)
                    if self._wait_for_txt == WAIT_FOR_MOVELIST:
                        odata = None
                        if (not self.ML_recording and
                                b'Movelist for game' in data):
                            self.ML_recording = True
                            idx = data.index(b'Movelist for game')
                            odata = data[:idx]
                            data  = data[idx::]
                        if self.ML_recording:
                            txt = data.decode('ascii','ignore')
                            self._wait_for_buf.append(txt)
                            if b'      {' in data:
                                idx = data.index(b'      {')
                                odata = data[idx+6::]
                                self._wait_for_buf.pop()
                                data = data[:idx]
                                txt = data.decode('ascii','ignore')
                                self._wait_for_buf.append(txt)
                                self.ML_recording = False
                                self._wait_for_sem.release()
                        data = odata if odata else b''
                    elif self._wait_for_txt:
                        txt = data.decode('ascii','ignore')
                        self._wait_for_buf.append(txt)
                        if self._wait_for_txt in txt:
                            self._wait_for_sem.release()
                    data = data+b'<_>'
                    os.write(self.pipe, data)
            self.fics.close()
        except:
            del self.fics
            self.print('=== We got DISCONNECTED! try %c ===',
                    urwid.AttrSpec(config.console.echo_color, 'default'))

    def test_connection(self):
        self.send_cmd(' '.join(['xtell', config.fics_user,
                                'papageorge connection test']),
                      wait_for='tells you: papageorge connection test')

    def send_cmd(self, cmd, echo=False,
            wait_for=None, ans_buff=None, save_history=True,
            record_handle=True):
        if hasattr(self, 'fics'):
            if save_history:
                self.cmd_line.cmd_history_idx = 0
                if (len(self.cmd_line.cmd_history) and
                        self.cmd_line.cmd_history[-1] != cmd or
                            not len(self.cmd_line.cmd_history)):
                    self.cmd_line.cmd_history.append(cmd)
            if record_handle:
                if ' ' in cmd:
                    m = self.handle_rule.match(cmd.split()[1])
                    if m:
                        config.update_handle(m.group())
            data = cmd.translate(config.TRANS_TABLE) \
                    .encode("ascii", "ignore")+b'\n'
            config.log(data, sent=True)
            if wait_for:
                self._wait_for_buf.clear()
                self._wait_for_txt = wait_for
                config.log('Waiting for: '+str(wait_for))
            self.fics.write(data)
            if wait_for:
                if not self._wait_for_sem.acquire(timeout=5):
                    self._wait_for_txt = None
                    self.ML_recording = False
                    config.log('Waiting for failed')
                    return False
                config.log('Waiting for succeed')
                self._wait_for_txt = None
                if isinstance(ans_buff, list):
                    ans_buff.append(''.join(self._wait_for_buf))
            if echo:
                self.print('> '+cmd,
                        urwid.AttrSpec(config.console.echo_color, 'default'))
            return True

    def send_moves(self, moves):
        for move in moves:
            self.send_cmd(move.cmove[2::] if '/' in move.cmove else move.cmove,
                            save_history=False)

