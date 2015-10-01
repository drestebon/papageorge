# gui - Board and Seekgraph definitions

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

# ♔ ♕ ♖ ♗ ♘ ♙ ♚ ♛ ♜ ♝ ♞ ♟ 

import os
from time import time
from glob import glob
from math import floor, ceil, pi, sqrt
import gi
from gi.repository import Gtk, GLib, GObject, GdkPixbuf, Gdk, Pango, PangoCairo
import cairo

if __name__ == '__main__':
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config

here = os.path.dirname(os.path.abspath(__file__))
figPath = os.path.abspath(os.path.join(here, 'JinSmart'))
fsets = [int(os.path.basename(x)) for x in glob(figPath+'/[0-9]*')]
fsets.sort()

class Style12(str):
    def __new__(cls, value):
        return str.__new__(cls, ''.join(value.split()[8:0:-1]))

    def __init__(self, value):
        self.style12 = value
        svalue = value.split()
        self.game_number = int(svalue[16])
        self.turn = svalue[9] == 'W'
        self.wname, self.bname = svalue[17:19]
        self.relation = int(svalue[19])
        self.itime = svalue[20]
        self.iinc  = svalue[21]
        self.wstrength = int(svalue[22])
        self.bstrength = int(svalue[23])
        self.wtime = int(svalue[24])
        self.btime = int(svalue[25])
        self.halfmove  = (int(svalue[26])-1)*2 + (not self.turn) + 1
        self.time = time()

    def __sub__(self, y):
        return [ (i%8, i//8) for i in range(64) if self[i] != y[i] ]

    def piece_in(self, pos):
        square = self[pos[1]*8+pos[0]]
        return square if square != '-' else False

    def duplicate(self, s):
        n = self.style12.split()
        f = self.piece_in(s[0])
        t = self.piece_in(s[1])
        n[8-s[0][1]] = '-'.join([n[8-s[0][1]][0:s[0][0]],
                                 n[8-s[0][1]][s[0][0]+1::]])
        n[8-s[1][1]] = f.join([n[8-s[1][1]][0:s[1][0]],
                               n[8-s[1][1]][s[1][0]+1::]])
        if n[9] == 'W':
            n[23] = str(int(n[23])-(1 if t == 'p' else 
                                    3 if t in ['n', 'b'] else
                                    5 if t == 'r' else
                                    9 if t == 'q' else 0))
        else:
            n[22] = str(int(n[22])-(1 if t == 'P' else 
                                    3 if t in ['N', 'B'] else
                                    5 if t == 'R' else
                                    9 if t == 'Q' else 0))
        n[26] = str(int(n[26]) + (1 if n[9] == 'B' else 0))
        n[9] = 'W' if n[9] == 'B' else 'B'
        n[27] = n[29] = '-'
        return ' '.join(n)

class BoardState:
    def __init__(self, initial_state=None):
        self._history = []
        self._showing = -1
        self.marked = []
        self.selected = []
        self.piece_flying = False
        self.piece_clicked = False
        self.move_sent = False
        # properties
        self.strength = [0,0]
        self.turn = True
        self.halfmove = -1
        # ONESHOT PROPS
        self.rating = ['','']
        self.player = ['','']
        self.wplayer = ''
        self.bplayer = ''
        self.opponent = self.bplayer
        self.me = self.wplayer
        self._kind = 0
        self.side = True
        self.itime = self.iinc = ''
        self.name = ''
        self.interruptus = False
        if initial_state:
            self.set(initial_state)

    def set_gameinfo(self, info):
        self.rating = [' ('+x+')' for x in 
                 info.split()[9].split('=')[1].split(',')[::-1]]

    def update_marked(self):
        self.marked.clear()
        if len(self._history) > 1 and len(self._history)+self._showing > 0:
            pds = next( (x for x in self._history[self._showing-1::-1] 
                            if x != self._history[self._showing]),
                        None)
            if pds:
                self.marked = self._history[self._showing]-pds
                if len(self.marked) > 4:
                    self.marked.clear()

    def pos2pos(self, pos):
        return chr(97 + pos[0]) + str(pos[1]+1)

    def set(self, new_state):
        state = Style12(new_state)
        i = next((self._history.index(x) for x in self._history
                            if x.halfmove >= state.halfmove), None)
        if i != None:
            self._history = self._history[:i]
        self._history.append(state)
        self._showing = -1
        self.move_sent = False
        self.update_marked()
        self.strength = [state.bstrength,
                         state.wstrength]
        self.turn = state.turn
        #flush premove
        ret = None
        if (self.kind == 'playing' and len(self.selected) == 2 and
                self.side == self.turn and self.halfmove != state.halfmove):
            ret = (self.pos2pos(self.selected[0])+
                               self.pos2pos(self.selected[1]))
        elif (self.kind == 'playing' and len(self.selected) == 1 and
                self.side == self.turn): 
            pass
        else:
            self.selected.clear()
        self.halfmove = state.halfmove
        if len(self._history) == 1:
            self.player = [state.bname+self.rating[0],
                           state.wname+self.rating[1]]
            self.wplayer = state.wname
            self.bplayer = state.bname
            self._kind = state.relation
            self.side = ((self.turn and (self._kind == 1)) or
                         ((self._kind == -1) and not self.turn) or
                         (self.kind != 'playing' and
                             self.wplayer == config.fics_user))
            self.opponent = self.bplayer if self.side else self.wplayer
            self.me       = self.wplayer if self.side else self.bplayer
            self.itime = state.itime
            self.iinc  = state.iinc
            self.name = ('Game {}: '.format(state.game_number) +
                         ('Examining ' if self.kind == 'examining' else
                          'Observing ' if self.kind == 'observing' else '')+ 
                          ' v/s '.join(self.player[::-1])+' -  Clock:'+
                          '/'.join([self.itime, self.iinc])).strip()
        return ret

    def backward(self):
        if len(self._history)+self._showing > 0:
            self._showing = next((self._history.index(x)-len(self._history)
                                   for x in self._history[self._showing-1::-1]
                                      if x != self._history[self._showing]),
                                 self._showing)
        self.update_marked()

    def forward(self):
        if self._showing < -1:
            self._showing = next((self._history.index(x)-len(self._history)
                                    for x in self._history[self._showing+1::] 
                                       if x != self._history[self._showing]),
                                 self._showing)
        self.update_marked()

    def piece_in(self, pos):
        return self._history[self._showing].piece_in(pos)

    def click(self, pos):
        self._showing = -1
        x = self.piece_in(pos)
        # Another piece is selected
        if (x and 
            (self.side if self.kind == 'playing'
                else self.turn) == x.isupper()):
            self.piece_clicked = x
            self.selected.clear()
            self.selected.append(pos)
            return None
        else:
            self.piece_clicked = False
        # MOVE
        if len(self.selected):
            if len(self.selected) > 1 :
                self.selected.pop()
            self.selected.append(pos)
            if self.kind == 'observing':
                self.set(self._history[-1].duplicate(self.selected))
                self.interruptus = True
            elif (self.kind != 'playing') or (self.side == self.turn) :
                self.move_sent = True
                return (self.pos2pos(self.selected[0])
                            +self.pos2pos(self.selected[1]))
            return None
    
    def release(self, pos):
        if self.piece_flying:
            self.piece_flying = False
            x = self.piece_in(pos)
            if (x and
                    (self.side if self.kind == 'playing'
                     else self.turn) == x.isupper()):
                self.piece_clicked = x
                self.selected.clear()
                self.selected.append(pos)
                return None
            # MOVE
            if len(self.selected):
                if len(self.selected) > 1 :
                    self.selected.pop()
                self.selected.append(pos)
                if self.kind == 'observing':
                    self.set(self._history[-1].duplicate(self.selected))
                    self.interruptus = True
                elif (self.kind != 'playing') or (self.side == self.turn) :
                    self.move_sent = True
                    return (self.pos2pos(self.selected[0])
                             +self.pos2pos(self.selected[1]))
                return None

    def figures(self):
        if len(self._history):
            fl = [((i%8,i//8), self._history[self._showing][i])
                  for i in range(64) if (self._history[self._showing][i] != '-'
                         and  (i%8,i//8) not in self.selected) ]
            if not self.piece_flying and len(self.selected) > 1:
                return fl+([(self.selected[-1],
                                self.piece_in(self.selected[-2]))]
                        if self.piece_in(self.selected[-2]) else [])
            elif not self.piece_flying and len(self.selected):
                return fl+([(self.selected[-1],
                                self.piece_in(self.selected[-1]))]
                        if self.piece_in(self.selected[-1]) else [])
            else:
                return fl
        else:
            return []

    def is_being_played(self):
        return (abs(self._kind) < 2) and not self.interruptus

    @property
    def kind(self):
        if len(self._history):
            return ('playing' if abs(self._kind) == 1 else
                    'observing' if self._kind in [0, -2] else
                    'examining' if self._kind == 2 else
                    'isolated')
        else:
            return None

    @property
    def time(self):
        if len(self._history):
            if (self.is_being_played() and
                    self.halfmove > 2 and
                    not self.interruptus):
                Dt = time()-self._history[-1].time
            else:
                Dt = 0
            if self._history[-1].turn:
                return [int(self._history[-1].btime),
                        int(self._history[-1].wtime-Dt)]
            else:
                return [int(self._history[-1].btime-Dt),
                        int(self._history[-1].wtime)]
        else:
            return [0, 0]

class BoardExitDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "uh?", parent.win)
        self.set_modal(True)
        self.add_button('_Abort', 0)
        self.add_button('_Draw', 1)
        self.add_button('Ad_journ', 2)
        self.add_button('_Resign', 3)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        b = self.set_default_response(Gtk.ResponseType.CANCEL)
        self.show_all()

class BoardCommandsPopover(Gtk.Popover):
    def __init__(self, parent):
        self.parent = parent
        Gtk.Popover.__init__(self)
        self.connect('closed', self.on_delete)
        self.set_border_width(0)
        self.set_relative_to(parent)
        self.set_modal(True)
        self.set_position(Gtk.PositionType.RIGHT)
        if gi.version_info >= (3,16,0):
            self.set_transitions_enabled(False)
        vbox = Gtk.VBox().new(True, 1)
        self.add(vbox)
        if parent.state.kind == 'playing':
            if not parent.state.interruptus:
                for label, command in [
                        ('_Draw',      lambda x : 'draw'),
                        ('_Resign',    lambda x : 'resign'),
                        ('_Abort',     lambda x : 'abort'),
                        ('Ad_journ',   lambda x : 'adjourn'),
                        ('_More Time', lambda x :
                          'moretime {}'.format(x.more_time.get_value_as_int())),
                        ('R_efresh',   lambda x : 'refresh'),
                        ]:
                    button = Gtk.Button.new_with_mnemonic(label)
                    button.command = command
                    button.connect("clicked", self.on_button_clicked)
                    vbox.pack_start(button, True, True, 0)
                # Moretime
                self.more_time = Gtk.SpinButton()
                self.more_time.set_adjustment(
                        Gtk.Adjustment(60, 0, 1000, 10, 60, 0))
                self.more_time.get_adjustment().configure(
                        60, 0, 1000, 10, 60, 0) 
                vbox.pack_start(self.more_time, True, True, 0)
            else:
                button = Gtk.Button.new_with_mnemonic('_Examine Last')
                button.command = lambda x : 'exl'
                button.connect("clicked", self.on_button_clicked)
                vbox.pack_start(button, True, True, 0)
        if parent.state.kind == 'examining':
            for label, command in [
                    ('_AnalysisBot obsme', lambda x : 'tell Analysisbot obsme'),
                    ('AnalysisBot _stop', lambda x : 'tell Analysisbot stop'),
                    ('_Refresh',   lambda x : 'refresh'),
                    ('_Unexamine', lambda x : 'unexamine'),
                    ]:
                button = Gtk.Button.new_with_mnemonic(label)
                button.command = command
                button.connect("clicked", self.on_button_clicked)
                vbox.pack_start(button, True, True, 0)
        if parent.state.kind == 'observing':
            for label, command in [
                    ('_Copy Game',
                       lambda x : 'copygame {}'.format(x.parent.board_number)),
                    ('_Refresh',   lambda x : 'refresh'),
                    ('_Unobserve', lambda x : 'unobserve'),
                    ]:
                button = Gtk.Button.new_with_mnemonic(label)
                button.command = command
                button.connect("clicked", self.on_button_clicked)
                vbox.pack_start(button, True, True, 0)
        button = Gtk.Button.new_with_mnemonic('_Cancel')
        button.connect("clicked", self.on_cancel_clicked)
        vbox.pack_start(button, True, True, 0)

    def on_button_clicked(self, button):
        self.parent.cli.send_cmd(button.command(self), True)
        self.hide()

    def on_cancel_clicked(self, button):
        self.hide()

    def on_delete(self, widget):
        pass

class DimensionsSet(object):
    PARAM_SET = [
            'turnbox_y', 'turn_x', 'turn_y',
            'turn_width', 'turn_height', 'turn_off',
            'tp_xoff', 'tp_yoff', 'tc_xoff', 'tc_yoff',
            'bp_xoff', 'bp_yoff', 'bc_xoff', 'bc_yoff',
            'xoff', 'yoff', 'side', 'sside', 'bside', 'bxoff', 'byoff', 'G',
            'lw', 'fig_size', 'wwidth', 'wheight',
            'promote_height', 'promote_width',
            'promote_yoff', 'promote_xoff',
            'promote_txoff', 'promote_tyoff', 'promote_fyoff'
        ]

    def __setattr__(self, name, value):
        if name in self.PARAM_SET:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError

    def __getattr__(self, name):
        if name in self.PARAM_SET:
            if name in dir(self):
                return getattr(self, name)
            else:
                return 1
        else:
            raise AttributeError

class Board (Gtk.DrawingArea):
    def __init__(self,
                 gui,
                 cli,
                 initial_state = None,
                 game_info = None):
        # Window cfg
        da = Gtk.DrawingArea.__init__(self)
        bg = Gdk.RGBA.from_color(Gdk.color_parse('#101010'))
        self.override_background_color(Gtk.StateType.NORMAL, bg)
        self.connect('draw', self.on_draw)
        self.connect('size_allocate', self.on_resize)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button_press_event', self.mouse_cmd)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect('scroll_event', self.scroll_cmd)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect('button_release_event', self.mouse_release)
        self.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        self.connect('motion-notify-event', self.mouse_move)
        self.set_can_focus(True)
        self.grab_focus()
        # 
        self.png_figures = {x : None for x in 'KQRBNPkqrbnp'}
        self.ico_figures = {x : None for x in 'KQRBNPkqrbnp'}
        self.cli = cli
        self.gui = gui
        self.key_commands = [
          (config.board.accel_fforward       , self.cmd_fforward),
          (config.board.accel_frewind        , self.cmd_frewind),
          (config.board.accel_forward        , self.cmd_forward),
          (config.board.accel_rewind         , self.cmd_rewind),
          (config.board.accel_prev_move      , self.cmd_prev_move),
          (config.board.accel_next_move      , self.cmd_next_move),
          (config.board.accel_flip           , self.cmd_flip),
          (config.board.accel_promote        , self.cmd_promote),
          (config.board.accel_promote        , self.cmd_promote),
          (config.board.accel_border         , self.cmd_border),
          (config.board.accel_board_commands , self.cmd_board_commands),
          (config.board.accel_seek_graph     , self.gui.new_seek_graph),
        ]
        for accel, txt in config.board.command:
            self.key_commands.append((accel,
                lambda event, txt=txt: self.cli.send_cmd(eval(txt), echo=True)))
        self.state = BoardState(initial_state)
        self.flip = not self.state.side
        if game_info:
            self.state.set_gameinfo(game_info)
            self.board_number = int(game_info.split()[1])
            self.flip = 2
        elif initial_state:
            self.board_number = int(initial_state.split()[16])
            self.pop = BoardCommandsPopover(self)
        else:
            self.board_number = 9999
        #
        self.geom = DimensionsSet()
        self.promote_to = 0
        self.promote_show = False
        self.promote_timeout = None
        if self.state.kind in ['examining', 'playing']:
            self.gui.seek_graph_destroy()
        if config.board.border:
            self.cmd_border(True)
        else:
            self.BORDER = 0

        GObject.timeout_add(99, self.redraw_turn)

    def set_gameinfo(self, info):
        self.state.set_gameinfo(info)

    def set_state(self, new_state):
        self.state.interruptus = False
        cmd = self.state.set(new_state)
        if self.flip == 2:
            self.pop = BoardCommandsPopover(self)
            self.flip = not self.state.side
            if self.state.kind == 'playing':
                self.BORDER = 0
        try:
            self.win.set_title(self.state.name)
        except:
            pass
        if self.state.kind in ['examining', 'playing']:
            self.gui.seek_graph_destroy()
        if(cmd):
            self.cli.send_cmd(cmd)
        self.redraw()

    def set_interruptus(self):
        self.state.interruptus = True
        self.pop = BoardCommandsPopover(self)
        self.redraw()

    def cmd_border(self, event, value=False):
        if value or (not value and not self.BORDER):
            pc = self.get_pango_context()
            pc.set_font_description(
                   Pango.FontDescription.from_string(config.board.font+' '
                       +str(config.board.font_coords_size))
                   )
            m = pc.get_metrics(None)
            self.BORDER = 1.5*(m.get_descent()+m.get_ascent())/Pango.SCALE
        else:
            self.BORDER = 0
        self.on_resize(self, 0)
        self.redraw()

    def cmd_board_commands(self, event, mevent=None):
        if self.promote_show:
            self.promote_hide()
            return
        ri = self.get_allocation().copy()
        ri.width=ri.height=0
        if mevent:
            ri.x = mevent.x
            ri.y = mevent.y
        self.pop.set_pointing_to(ri)
        self.pop.show_all()

    def cmd_fforward(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward 999")
            return True
        else:
            return False

    def cmd_frewind(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward 999")
            return True
        else:
            return False

    def cmd_forward(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward 6")
            return True
        else:
            return False

    def cmd_rewind(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward 6")
            return True
        else:
            return False

    def cmd_prev_move(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward")
            return True
        else:
            self.state.backward()
            self.redraw()
            return True

    def cmd_next_move(self, event):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward")
            return True
        else:
            self.state.forward()
            self.redraw()
            return True

    def cmd_flip(self, event):
        self.flip = not self.flip
        self.on_resize(self, 0)
        self.redraw()
        return True

    def cmd_promote(self, event):
        if self.state.kind in ['playing', 'examining']:
            self.promote_show = True
            if self.promote_timeout:
                if event.state == Gdk.ModifierType.SHIFT_MASK:
                    self.promote_to = (self.promote_to - 1)% 4
                else:
                    self.promote_to = (self.promote_to + 1)% 4
                GLib.source_remove(self.promote_timeout)
            self.cli.send_cmd('promote {}'.format('qrbn'[self.promote_to]))
            self.promote_timeout = GObject.timeout_add_seconds(2, self.promote_hide)
            GObject.idle_add(self.queue_draw_area,
                self.geom.promote_xoff, self.geom.promote_yoff,
                self.geom.promote_width, self.geom.promote_height)
            return True

    def promote_hide(self):
        self.promote_show = False
        if self.promote_timeout:
            GLib.source_remove(self.promote_timeout)
        self.promote_timeout = None
        GObject.idle_add(self.queue_draw_area,
            self.geom.promote_xoff-5, self.geom.promote_yoff-5,
            self.geom.promote_width+10, self.geom.promote_height+10)

    def key_cmd(self, widget, event):
        state = event.state & ~Gdk.ModifierType.BUTTON1_MASK
        cmd = next((c[1] for c in self.key_commands 
                if ( Gtk.accelerator_parse(c[0]) ==
                     ( (Gdk.keyval_to_lower(event.keyval) if
                         event.keyval not in [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
                         else Gdk.KEY_Tab), state)
                   )),
                None)
        if cmd:
            if cmd not in [self.cmd_promote, self.cmd_board_commands]:
                self.promote_hide()
            cmd(event)
        else:
            if event.keyval not in [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R]:
                self.promote_hide()
            self.cli.key_from_gui(event.keyval)
        self.cli.redraw()

    def mouse_cmd(self, widget, event):
        self.promote_hide()
        if event.button == 1:
            x = floor((event.x - self.geom.bxoff)/self.geom.sside)
            y = floor((event.y - self.geom.byoff)/self.geom.sside)
            if x < 0 or x > 7 or y < 0 or y > 7:
                return False
            s = (7-x, y) if self.flip else (x, 7-y)
            cmd = self.state.click(s)
            if(cmd):
                self.cli.send_cmd(cmd)
            self.redraw()
        elif event.button == 3:
            self.cmd_board_commands(None, mevent=event)

    def scroll_cmd(self, widget, event):
        self.promote_hide()
        if event.direction == Gdk.ScrollDirection.UP:
            self.cmd_next_move(None)
        if event.direction == Gdk.ScrollDirection.DOWN:
            self.cmd_prev_move(None)

    def mouse_move(self, widget, event):
        if self.state.piece_clicked and not self.state.piece_flying:
            self.win.get_window().set_cursor(
                    self.ico_figures[self.state.piece_clicked])
            self.state.piece_flying = True
            self.redraw()

    def mouse_release(self, widget, event):
        self.promote_hide()
        self.win.get_window().set_cursor(None)
        x = floor((event.x - self.geom.bxoff)/self.geom.sside)
        y = floor((event.y - self.geom.byoff)/self.geom.sside)
        if x < 0 or x > 7 or y < 0 or y > 7:
            return False
        s = (7-x, y) if self.flip else (x, 7-y)
        cmd = self.state.release(s)
        if(cmd):
            self.cli.send_cmd(cmd)
        self.redraw()

    def on_resize(self, widget, cr):
        pc = self.get_pango_context()
        pc.set_font_description(
               Pango.FontDescription.from_string(config.board.font+' Bold '
                   +str(config.board.font_size))
               )
        m = pc.get_metrics(None)
        P_clk_height = (m.get_descent()+m.get_ascent())/Pango.SCALE

        lay = Pango.Layout(pc)
        txt = max((t for t in ["00  00:00"]+ self.state.player),
                key=lambda t: len(t))
        lay.set_text(txt, -1)
        L_clk_width, height = lay.get_pixel_size()

        self.geom.wwidth = self.get_allocated_width()
        self.geom.wheight = self.get_allocated_height()

        Lside = min(self.geom.wwidth-L_clk_width, self.geom.wheight)
        Pside = min(self.geom.wheight-2*P_clk_height, self.geom.wwidth)

        if Lside > Pside:
            self.geom.side = Lside
            self.geom.xoff = 0
            self.geom.yoff = (self.geom.wheight-self.geom.side)*0.5

            self.geom.tp_xoff = self.geom.side
            self.geom.tp_yoff = self.geom.yoff
            self.geom.tc_xoff = self.geom.side
            self.geom.tc_yoff = self.geom.yoff+P_clk_height
            self.geom.bp_xoff = self.geom.side
            self.geom.bp_yoff = self.geom.yoff+self.geom.side-2*P_clk_height
            self.geom.bc_xoff = self.geom.side
            self.geom.bc_yoff = self.geom.yoff+self.geom.side-P_clk_height
            self.geom.turn_width  = L_clk_width
            self.geom.turn_height = 2*P_clk_height
            self.geom.turn_x      = self.geom.side
            self.geom.turn_y      = self.geom.yoff
            self.geom.turn_off    = self.geom.side-self.geom.turn_height
        else:
            self.geom.side = Pside
            self.geom.xoff = (self.geom.wwidth-self.geom.side)*0.5
            if self.geom.xoff:
                self.geom.yoff = P_clk_height
            else:
                self.geom.yoff = (self.geom.wheight-self.geom.side)*0.5

            lay.set_text("00  00:00", -1)
            P_clk_width, height = lay.get_pixel_size()

            self.geom.tp_xoff = self.geom.xoff
            self.geom.tp_yoff = self.geom.yoff-P_clk_height
            self.geom.tc_xoff = self.geom.xoff+self.geom.side-P_clk_width
            self.geom.tc_yoff = self.geom.yoff-P_clk_height
            self.geom.bp_xoff = self.geom.xoff
            self.geom.bp_yoff = self.geom.yoff+self.geom.side
            self.geom.bc_xoff = self.geom.xoff+self.geom.side-P_clk_width
            self.geom.bc_yoff = self.geom.yoff+self.geom.side
            self.geom.turn_width  = self.geom.side
            self.geom.turn_height = P_clk_height
            self.geom.turn_x      = self.geom.xoff
            self.geom.turn_y      = self.geom.yoff-P_clk_height
            self.geom.turn_off    = self.geom.side+self.geom.turn_height

        self.geom.bside = self.geom.side-2*self.BORDER
        self.geom.sside = self.geom.bside*0.125
        self.geom.lw = self.geom.sside*0.04

        self.geom.bxoff = self.geom.xoff + self.BORDER
        self.geom.byoff = self.geom.yoff + self.BORDER

        # Promote
        pc.set_font_description(
                Pango.FontDescription.from_string(config.board.font+' Bold '
                    +str(int(0.8*config.board.font_size)))
                )
        lay = Pango.Layout(pc)
        lay.set_text('Promote to:', -1)
        width, height = lay.get_pixel_size()
        self.geom.promote_height = height*2.2+self.geom.sside
        self.geom.promote_width  = height+max(width, 4*self.geom.sside)
        self.geom.promote_yoff   = self.geom.byoff+0.5*(self.geom.bside-self.geom.promote_height)
        self.geom.promote_xoff   = self.geom.bxoff+0.5*(self.geom.bside-self.geom.promote_width)
        self.geom.promote_txoff  = self.geom.promote_xoff+0.5*height
        self.geom.promote_tyoff  = self.geom.promote_yoff+0.5*height
        self.geom.promote_fyoff  = 7-(self.geom.promote_yoff-self.geom.byoff+1.7*height)/self.geom.sside 

        if self.BORDER:
            pc.set_font_description(
                    Pango.FontDescription.from_string(config.board.font+' '
                        +str(config.board.font_coords_size))
                    )
            m = pc.get_metrics(None)
            fheight = (m.get_descent()+m.get_ascent())/Pango.SCALE
            lay = Pango.Layout(pc)
            self.file_coords = []
            for x, l in enumerate('abcdefgh'):
                lay.set_text(l, -1)
                width, height = lay.get_pixel_size()
                xx = 7-x if self.flip else x
                self.file_coords.append(
                   (l,
                   self.geom.xoff+self.BORDER+self.geom.sside*(0.5+xx)-width*0.5,
                   self.geom.yoff+self.BORDER*0.5-fheight*0.5)
                   )
                self.file_coords.append(
                   (l,
                   self.geom.xoff+self.BORDER+self.geom.sside*(0.5+xx)-width*0.5,
                   self.geom.yoff+self.BORDER*1.5-fheight*0.5+self.geom.bside)
                   )
                txt = str(8-x)
                lay.set_text(txt, -1)
                width, height = lay.get_pixel_size()
                self.file_coords.append(
                        (txt,
                        self.geom.xoff+self.BORDER*0.5-width*0.5,
                        self.geom.yoff+self.BORDER+self.geom.sside*(0.5+xx)-fheight*0.5)
                    )
                self.file_coords.append(
                        (txt,
                        self.geom.xoff+self.BORDER*1.5-width*0.5+self.geom.bside,
                        self.geom.yoff+self.BORDER+self.geom.sside*(0.5+xx)-fheight*0.5)
                    )

        self.reload_figures()
        return True

    def reload_figures(self):
        fig_scale = 1.17
        mono_res = next(x for x in fsets if x >= self.geom.sside/fig_scale)
        self.geom.G = fig_scale*mono_res/self.geom.sside
        self.mono_res = mono_res
        self.geom.fig_size = self.geom.sside/fig_scale

        for mono in 'KQRBNPkqrbnp':
            fn = figPath+'/'+str(mono_res)+"/"+mono+".png"
            fd = cairo.ImageSurface.create_from_png(fn)
            self.png_figures[mono] = cairo.SurfacePattern(fd)
            if self.geom.sside > 0:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(fn,
                        int(ceil(mono_res)), int(ceil(mono_res)))
                self.ico_figures[mono] = Gdk.Cursor.new_from_pixbuf(
                    Gdk.Display.get_default(),pb,int(mono_res/2),
                    int(mono_res/2))

    def on_draw(self, widget, cr):
        # background
        cr.rectangle(0, 0, self.geom.wwidth, self.geom.wheight)
        cr.set_source_rgb(*config.board.bg)
        cr.fill()
        pc = self.get_pango_context()
        pc.set_font_description(
               Pango.FontDescription.from_string(config.board.font+' Bold '
                   +str(config.board.font_size))
               )
        lay = Pango.Layout(pc)
        # Turn Square
        turn_y = self.geom.turn_y + (0 if not (self.state.turn^self.flip)
                else (self.geom.turn_off))
        cr.rectangle(self.geom.turn_x, turn_y, self.geom.turn_width, self.geom.turn_height)
        self.geom.turnbox_y  = int(turn_y)
        ma_time = self.state.time[self.state.turn]
        if ma_time < 20 and ma_time % 2 and self.state.is_being_played():
            cr.set_source_rgb(*config.board.turn_box_excl)
        else:
            cr.set_source_rgb(*config.board.turn_box)
        cr.fill()
        # Player TOP
        if not (self.state.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(self.geom.tp_xoff, self.geom.tp_yoff)
        lay.set_text(self.state.player[self.flip], -1)
        PangoCairo.show_layout(cr, lay)
        cr.move_to(self.geom.tc_xoff, self.geom.tc_yoff)
        ma_time = self.state.time[self.flip]
        lay.set_text("{:>2} ".format(self.state.strength[self.flip]) +
                     (" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60),-1)
        PangoCairo.show_layout(cr, lay)
        # Player BOTTOM
        if (self.state.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(self.geom.bp_xoff, self.geom.bp_yoff)
        lay.set_text(self.state.player[not self.flip],-1)
        PangoCairo.show_layout(cr, lay)
        cr.move_to(self.geom.bc_xoff, self.geom.bc_yoff)
        ma_time = self.state.time[not self.flip]
        lay.set_text("{:>2} ".format(self.state.strength[not self.flip]) +
                     (" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60), -1)
        PangoCairo.show_layout(cr, lay)
        # Mesa
        cr.set_source_rgb(*config.board.border_color)
        cr.rectangle(self.geom.xoff, self.geom.yoff, self.geom.side, self.geom.side)
        cr.fill()
        # Tablero
        cr.set_source_rgb(*config.board.dark_square)
        cr.rectangle(self.geom.xoff+self.BORDER, self.geom.yoff+self.BORDER,
                     self.geom.bside, self.geom.bside)
        cr.fill()
        for i in range(0, 8):
            for j in range(0, 8):
                if (i+j)%2:
                    (x, y) = (7-i, j) if self.flip else (i, 7-j)
                    cr.set_source_rgb(*config.board.light_square)
                    cr.rectangle((self.geom.xoff + self.BORDER + x*self.geom.sside),
                                 (self.geom.yoff + self.BORDER + y*self.geom.sside),
                                 (self.geom.sside), (self.geom.sside))
                    cr.fill()
        for s in self.state.selected:
            i, j = s
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.set_source_rgb(
                   *(config.board.square_move_sent if self.state.move_sent else
                        (config.board.light_square_selected if (i+j)%2 else 
                            config.board.dark_square_selected))
                        )
            cr.rectangle((self.geom.xoff + self.BORDER + x*self.geom.sside),
                         (self.geom.yoff + self.BORDER + y*self.geom.sside),
                         (self.geom.sside), (self.geom.sside))
            cr.fill()
        for s in self.state.marked:
            i, j = s
            cr.set_source_rgb(*config.board.square_marked)
            cr.set_line_width(self.geom.lw)
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.rectangle((self.geom.xoff + self.BORDER +
                          x*self.geom.sside+self.geom.lw*0.5),
                         (self.geom.yoff + self.BORDER +
                             y*self.geom.sside+self.geom.lw*0.5),
                         (self.geom.sside-self.geom.lw),
                         (self.geom.sside-self.geom.lw))
            cr.stroke()
        # Figuras
        for s, f in self.state.figures():
            self.draw_piece(s,f,cr)
        # TAPON
        if self.state.interruptus:
            cr.rectangle(self.geom.xoff, self.geom.yoff, self.geom.side, self.geom.side)
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
            cr.fill()
        # Coordenadas
        pc.set_font_description(
                   Pango.FontDescription.from_string(config.board.font+' '
                       +str(config.board.font_coords_size))
                   )
        lay = Pango.Layout(pc)
        cr.set_source_rgba(*config.board.text_active)
        if self.BORDER:
            for l, x, y in self.file_coords:
                cr.move_to(x, y)
                lay.set_text(l, -1)
                PangoCairo.show_layout(cr, lay)
        # promote to:
        if self.promote_show:
            cr.rectangle(self.geom.promote_xoff, self.geom.promote_yoff,
                         self.geom.promote_width, self.geom.promote_height)
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.6)
            cr.fill()
            pc.set_font_description(
                    Pango.FontDescription.from_string(config.board.font+' Bold '
                        +str(int(0.8*config.board.font_size)))
                    )
            lay = Pango.Layout(pc)
            lay.set_text('Promote to:', -1)
            cr.set_source_rgba(*config.board.text_active)
            cr.move_to(self.geom.promote_txoff, self.geom.promote_tyoff)
            PangoCairo.show_layout(cr, lay)
            for i, f in enumerate('QRBN' if self.state.side else 'qrbn'):
                s = (2+i,self.geom.promote_fyoff)
                self.draw_piece(s,f,cr, coords=s)
                if 'qrbn'[self.promote_to] == f.lower():
                    cr.set_source_rgb(*config.board.square_marked)
                    cr.set_line_width(self.geom.lw)
                    x, y = s
                    cr.rectangle((self.geom.xoff + self.BORDER +
                        x*self.geom.sside+self.geom.lw*0.5),
                                 (self.geom.yoff + self.BORDER +
                                     (7-y)*self.geom.sside+self.geom.lw*0.5),
                                 (self.geom.sside-self.geom.lw),
                                 (self.geom.sside-self.geom.lw))
                    cr.stroke()

    # figura
    def draw_piece(self, pos, fig, cr, coords=None):
        cr.save()
        if coords:
            x, y = coords
        else:
            x, y = (7-pos[0], 7-pos[1]) if self.flip else (pos[0], pos[1])
        matrix = cairo.Matrix(
           xx = self.geom.G, yy = self.geom.G,
           x0 = self.geom.G*(-self.geom.bxoff-
                            (x*self.geom.sside+0.5*(self.geom.sside-self.geom.fig_size))),
           y0 = self.geom.G*(-self.geom.byoff-
                            ((7-y)*self.geom.sside+0.5*(self.geom.sside-self.geom.fig_size)))
           )
        pattern = self.png_figures[fig]
        pattern.set_matrix(matrix)
        cr.rectangle(
                self.geom.bxoff+x*self.geom.sside + 0.5*(self.geom.sside-self.geom.fig_size)+1,
                self.geom.byoff+(7-y)*self.geom.sside + 0.5*(self.geom.sside-self.geom.fig_size)+1,
                self.geom.fig_size-2, self.geom.fig_size-2
                )
        cr.clip()
        cr.set_source(pattern)
        cr.paint()
        cr.restore()

    def redraw(self):
        GObject.idle_add(self.queue_draw)

    def redraw_turn(self):
        GObject.idle_add(
            self.queue_draw_area,
            self.geom.turn_x, self.geom.turnbox_y,
            self.geom.turn_width, self.geom.turn_height)
        return True

class Seek ():
    def __init__(self, idx, x, y, text, computer, rated):
        self.idx = idx
        self.x = x
        self.y = y
        self.text = text
        self.computer = computer
        self.rated = rated
        self.xx = 0
        self.yy = 0

    def dist(self, x, y):
        return sqrt((x-self.xx)**2+(y-self.yy)**2)

class SeekGraph (Gtk.DrawingArea):
    def __init__(self,
                 cli,
                 initial_state = None):
        Gtk.DrawingArea.__init__(self)

        bg = Gdk.RGBA.from_color(Gdk.color_parse('#242424'))
        self.override_background_color(Gtk.StateType.NORMAL, bg)

        self.connect('draw', self.on_draw)
        self.connect('size_allocate', self.on_resize)

        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key_press_event', self.key_cmd)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button_press_event', self.mouse_cmd)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion-notify-event', self.hover)

        self.cli = cli
        
        self.active_seek = None

        self.seeks = []

        if initial_state:
            self.update(initial_state)

    def update(self, txt):
        cmd = txt.split()
        if cmd[0] == '<sc>':
            self.seeks.clear()
        elif cmd[0] == '<sr>':
            for idx in cmd[1::]:
                try:
                    s = next(s for s in self.seeks if s.idx==int(idx))
                    if self.active_seek == s:
                        self.active_seek = None
                    self.seeks.remove(s)
                except:
                    pass
        elif cmd[0] == '<s>':
            player = cmd[2].split('=')[1]
            flags = bool(int(cmd[3].split('=')[1], 16) & 0x2)
            rating = cmd[4].split('=')[1]
            clock = int(cmd[5].split('=')[1])
            incr = int(cmd[6].split('=')[1])
            rated = cmd[7].split('=')[1] == 'r'
            kind = cmd[8].split('=')[1]
            rrange = cmd[10].split('=')[1] 
            automatic = cmd[11].split('=')[1] == 't'
            formula = cmd[12].split('=')[1] == 't'
            color = cmd[9].split('=')[1] 
            color = 'white' if color=='W' else 'black' if color=='B' else ''

            stxt = [ "{}{} {}".format(player, '(C)' if flags else '', rating),
                     "{} {} {} {} ({})".format(clock,incr,
                                              'rated' if rated else 'unrated',
                                              kind, rrange),
                     "{}/{} {}".format('-' if automatic else 'm',
                                       'f' if formula else '-', color)]

            idx = int(cmd[1])
            y = 1.0 - ((int(rating.strip('E').strip('P')) - 500.0)/2000.0)
            x = sqrt(clock + 2.0*incr/3.0)/6.0
            self.seeks.append(self.position_seek(Seek(idx,x,y,stxt,
                                                       flags,rated)))

        GObject.idle_add(self.queue_draw)

    def position_seek(self, seek):
        ww = self.get_allocated_width()
        wh = self.get_allocated_height()
        xx = seek.x*ww
        yy = seek.y*wh
        xx = 5 if xx < 5 else ww-5 if xx > ww-5 else xx
        yy = 5 if yy < 5 else wh-5 if yy > wh-5 else yy
        seek.xx = xx
        seek.yy = yy
        return seek

    def reposition_seeks(self):
        ww = self.get_allocated_width()
        wh = self.get_allocated_height()
        for s in self.seeks:
            s.xx = s.x*ww
            s.yy = s.y*wh
        for s in self.seeks:
            self.position_seek(s)

    def hover(self, widget, event):
        if len(self.seeks):
            s = min(self.seeks, key=lambda s: s.dist(event.x, event.y))
            self.active_seek = s if s.dist(event.x, event.y) < 15 else None
            self.redraw()
        return

    def key_cmd(self, widget, event):
        return

    def mouse_cmd(self, widget, event):
        if self.active_seek in self.seeks:
            self.cli.send_cmd("play {}".format(self.active_seek.idx))
        return

    def on_resize(self, widget, cr):
        self.reposition_seeks()
        return True

    def on_draw(self, widget, cr):
        cr.select_font_face(config.board.font, cairo.FONT_SLANT_NORMAL)

        ww = self.get_allocated_width()
        wh = self.get_allocated_height()

        xx=[0.0, 0.23570226039551587, 0.6454972243679028, 1.0]
        yy=[0.0, 0.25, 0.75, 1.0]

        fheight = cr.font_extents()[2]

        for i in range(3):
            for j in range(3):
                cr.rectangle(xx[i]*ww,yy[j]*wh,
                             (xx[i+1]-xx[i])*ww,(yy[j+1]-yy[j])*wh)
                color = 0.1+0.02*i+0.02*(j%2)
                cr.set_source_rgb(color, color, color)
                cr.fill()

        cr.set_font_size(12)
        cr.set_source_rgb(0.3, 0.3, 0.3)
        x_off=1
        cr.move_to(x_off, yy[1]*wh)
        cr.show_text("2000")
        cr.move_to(x_off, yy[2]*wh)
        cr.show_text("1000")

        y_off=1.0*wh-0.1*fheight
        cr.move_to(xx[1]*ww, y_off)
        color = 0.3+0.02
        cr.set_source_rgb(color, color, color)
        cr.show_text("2m")
        cr.move_to(xx[2]*ww, y_off)
        color = 0.3+0.04
        cr.set_source_rgb(color, color, color)
        cr.show_text("15m")

        cr.set_source_rgba(0.4, 0.4, 0.4, 0.4)
        cr.set_line_width(0.5)
        for xx in range(1,21):
            cr.move_to(0, (0.05*xx-0.05)*wh)
            cr.rel_line_to(ww, 0)
            cr.stroke()

        cr.set_font_size(11)
        if len(self.seeks):
            for s in self.seeks:
                if s.computer:
                    cr.rectangle(s.xx-3, s.yy-3, 6, 6)
                else:
                    cr.arc(s.xx, s.yy, 3, 0, 2*pi)
                if s.rated:
                    cr.set_source_rgb(0.6, 0.6, 0.6)
                else:
                    cr.set_source_rgb(0.4, 0.4, 0.4)
                cr.fill()

            if self.active_seek in self.seeks:
                s = self.active_seek
                if s.computer:
                    cr.rectangle(s.xx-4, s.yy-4, 8, 8)
                else:
                    cr.arc(s.xx, s.yy, 4, 0, 2*pi)
                if s.rated:
                    cr.set_source_rgb(0.6, 0.6, 0.6)
                else:
                    cr.set_source_rgb(0.4, 0.4, 0.4)
                cr.fill()

                x_off = 15
                y_off = 0
                t = max(s.text, key=lambda t: len(t))
                width, height = (cr.text_extents(t))[2:4]
                if s.xx+x_off+width > ww:
                    x_off = x_off - (s.xx+x_off+width-ww)

                if s.yy-2*fheight < 0:
                    y_off = -(s.yy-2*fheight)
                elif s.yy+fheight+5 > wh:
                    y_off = wh - (s.yy+fheight+5)

                cr.rectangle(s.xx+x_off-4,s.yy-2*fheight+y_off,
                             width+8,3*fheight+5)
                cr.set_source_rgba(0.0, 0.0, 0.0, 0.4)
                cr.fill()

                cr.set_source_rgb(0.85, 0.85, 0.85)
                for i, txt in enumerate(s.text):
                    cr.move_to(s.xx+x_off, s.yy+fheight*(i-1)+y_off)
                    cr.show_text(txt)

        return

    def redraw(self):
        GObject.idle_add(self.queue_draw)

class GUI:
    def __init__(self, cli):
        self.cli = cli
        self.boards = []
        self.seek_graph = None

    def on_board_delete(self, widget, event):
        b = widget.get_children()[0]
        if b.state.kind == 'examining':
            self.cli.send_cmd("unexamine")
            self.boards.remove(b)
            return False
        elif b.state.kind == 'observing':
            self.cli.send_cmd("unobserve {}".format(b.board_number))
            self.boards.remove(b)
            return False
        elif b.state.kind == 'playing':
            if b.state.interruptus:
                self.boards.remove(b)
                return False
            else:
                dialog = BoardExitDialog(b)
                response = dialog.run()
                if response < 0:
                    dialog.destroy()
                    return True
                self.cli.send_cmd(['abort', 'draw',
                                    'adjourn', 'resign'][response])
                if response > 2 or (response == 0 and b.state.halfmove < 2):
                    self.boards.remove(b)
                    dialog.destroy()
                    return False
                else:
                    dialog.destroy()
                    return True
                dialog.destroy()
        self.boards.remove(b)
        return False

    def on_board_focus(self, widget, direction):
        b = widget.get_children()[0]
        if (b.state.kind == 'observing' and 
             len([b for b in self.boards if b.state.kind == 'observing'])>1):
            self.cli.send_cmd('primary {}'.format(b.board_number))

    def new_board(self, initial_state=None, game_info=None):
        b = Board(self,self.cli,
                  initial_state=initial_state,game_info=game_info)
        self.boards.append(b)
        b.win = Gtk.Window(title=b.state.name)
        b.win.add(b)
        b.win.set_default_size(480,532)
        b.win.connect('delete-event', self.on_board_delete)
        b.win.add_events(Gdk.EventMask.FOCUS_CHANGE_MASK)
        b.win.connect('focus-in-event', self.on_board_focus)
        b.win.show_all()
        self.cli.connect_board(b)

    def on_seek_graph_delete(self, widget, event):
        self.cli.send_cmd("iset seekremove 0")
        self.cli.send_cmd("iset seekinfo 0")
        self.seek_graph = None
        return False

    def seek_graph_destroy(self):
        if self.seek_graph:
            self.cli.send_cmd("iset seekremove 0")
            self.cli.send_cmd("iset seekinfo 0")
            self.seek_graph.win.destroy()
            self.seek_graph = None

    def new_seek_graph(self, initial_state=None):
        if len([x for x in self.boards
                  if (x.state.kind == 'examining'
                      or (x.state.kind == 'playing'
                          and not x.state.interruptus))]) == 0:
            b = SeekGraph(self.cli, initial_state=initial_state)
            self.seek_graph = b
            b.win = Gtk.Window(title="Seeks")
            b.win.add(b)
            b.win.set_default_size(400,400)
            b.win.connect('delete-event', self.on_seek_graph_delete)
            self.cli.send_cmd("iset seekremove 1")
            self.cli.send_cmd("iset seekinfo 1")
            b.win.show_all()

def test_seek_graph():
    b = SeekGraph(0)
    b.win = Gtk.Window(title="Seek Graph")
    b.win.add(b)
    b.win.set_default_size(400,400)
    b.win.connect('delete-event', Gtk.main_quit)
    b.win.show_all()
    Gtk.main()

class TestCli:
    def __init__(self):
        foo = 'caca'
    def key_from_gui(self, keyval):
        print("cli.key_from_gui(): {}".format(keyval))
    def send_cmd(self, txt, echo=False):
        print("cli.send_cmd(): " + txt)
    def print(self, texto, attr=None):
        print("cli.print(): " + txt)
    def redraw(self):
        print('cli.redraw()')

class TestGui:
    def __init__(self):
        foo = 'caca'
    def new_seek_graph(self, initial_state=None):
        return True
    def seek_graph_destroy(self):
        return True

def test_board():
    game_info = '<g1> 1 p=0 t=blitz r=1 u=1,1 it=5,5 i=8,8 pt=0 rt=1586E,2100  ts=1,0'
    initial_state = '<12> rnbqkbnr pppppppp -------- -------- -------- -------- PPPPPPPP RNBQKBNR W  1 1 1 1 1 0 14 GuestXYQM estebon 2 5 5 19 39 10 30 1 none (0:00) none 0 0 0'
    b = Board(TestGui(), TestCli(), game_info=game_info)
    #b = Board(0, 0, initial_state=initial_state)
    b.set_state(initial_state)
    #b.interruptus = True
    b.win = Gtk.Window(title=b.state.name)
    b.win.add(b)
    b.win.set_default_size(480,532)
    b.win.connect('delete-event', Gtk.main_quit)
    b.win.show_all()
    Gtk.main()
    return b

if __name__ == '__main__':
    #test_seek_graph()
    b = test_board()
    pass

