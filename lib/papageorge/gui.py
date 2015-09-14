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
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk
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
        svalue = value.split()
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
            self.name = (('Examining ' if self.kind == 'examining' else
                          'Observing ' if self.kind == 'observing' else '')+ 
                          ' v/s '.join(self.player[::-1])+' '+
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
        if pos in self.selected:
            self.selected.remove(pos)
            return None
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
            if (self.kind != 'playing') or (self.side == self.turn) :
                self.move_sent = True
                return (self.pos2pos(self.selected[0])
                            +self.pos2pos(self.selected[1]))
            return None
    
    def release(self, pos):
        if self.piece_flying:
            self.piece_flying = False
            if pos in self.selected:
                self.selected.remove(pos)
                return None
            if len(self.selected):
                if len(self.selected) > 1 :
                    self.selected.pop()
                self.selected.append(pos)
                if (self.kind != 'playing') or (self.side == self.turn) :
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
            if (self.kind != 'examining' and
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

class BoardCommandsDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "uh?", parent.win)
        if parent.state.kind == 'playing':
            if not parent.state.interruptus:
                self.add_button('_Abort', 1)
                self.add_button('_Resign', 2)
                self.add_button('A_djourn', 3)
            else:
                self.add_button('_Examine last', 4)
        if parent.state.kind == 'examining':
            self.add_button('_Unexamine', 1)
        if parent.state.kind == 'observing':
            self.add_button('_Unobserve', 1)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        b = self.set_default_response(Gtk.ResponseType.CANCEL)
        self.show_all()

class Board (Gtk.DrawingArea):
    BORDER = 20
    def __init__(self,
                 gui,
                 cli,
                 initial_state = None,
                 game_info = None):
        # Window cfg
        Gtk.DrawingArea.__init__(self)
        bg = Gdk.RGBA.from_color(Gdk.color_parse('#101010'))
        self.override_background_color(Gtk.StateType.NORMAL, bg)
        self.connect('draw', self.on_draw)
        self.connect('size_allocate', self.on_resize)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button_press_event', self.mouse_cmd)
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
          ('<Shift>Up',     self.cmd_fforward),
          ('<Shift>Down',   self.cmd_frewind),
          ('Up',            self.cmd_forward),
          ('Down',          self.cmd_rewind),
          ('Left',          self.cmd_prev_move),
          ('Right',         self.cmd_next_move),
          ('f',             self.cmd_flip),
          ('b',             self.cmd_border),
          ('Escape',        self.cmd_board_commands),
          ('F5',            self.gui.new_seek_graph),
        ]
        for accel, txt in config.board.commands:
            self.key_commands.append((accel,
                      lambda txt=txt: self.cli.send_cmd(eval(txt), echo=True)))
        self.state = BoardState(initial_state)
        self.flip = not self.state.side
        if game_info:
            self.state.set_gameinfo(game_info)
            self.board_number = int(game_info.split()[1])
            self.flip = 2
        elif initial_state:
            self.board_number = int(initial_state.split()[16])
        else:
            self.board_number = 9999
        #
        if self.state.kind in ['examining', 'playing']:
            self.gui.seek_graph_destroy()
        if self.state.kind == 'playing':
            self.BORDER = 0
        GObject.timeout_add(99, self.redraw_turn)

    def set_gameinfo(self, info):
        self.state.set_gameinfo(info)

    def set_state(self, new_state):
        cmd = self.state.set(new_state)
        if self.flip == 2:
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

    def cmd_border(self):
        self.BORDER = 0 if self.BORDER else 20
        self.reload_figures()
        self.redraw()

    def cmd_board_commands(self):
        dialog = BoardCommandsDialog(self)
        response = dialog.run()
        if response < 0:
            pass
        elif self.state.kind == 'playing':
            if response == 1:
                self.cli.send_cmd("abort")
            elif response == 2:
                self.cli.send_cmd("resign")
            elif response == 3:
                self.cli.send_cmd("adjourn")
            elif response == 4:
                self.cli.send_cmd("exl")
        elif self.state.kind == 'examining' and response == 1:
                self.cli.send_cmd("unexamine")
        elif self.state.kind == 'observing' and response == 1:
                self.cli.send_cmd("unobserve")
        dialog.destroy()
        return True

    def cmd_fforward(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward 999")
            return True
        else:
            return False

    def cmd_frewind(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward 999")
            return True
        else:
            return False

    def cmd_forward(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward 6")
            return True
        else:
            return False

    def cmd_rewind(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward 6")
            return True
        else:
            return False

    def cmd_prev_move(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("backward")
            return True
        else:
            self.state.backward()
            self.redraw()
            return True

    def cmd_next_move(self):
        if self.state.kind == 'examining':
            self.cli.send_cmd("forward")
            return True
        else:
            self.state.forward()
            self.redraw()
            return True

    def cmd_flip(self):
        self.flip = not self.flip
        self.redraw()
        return True
            
    def key_cmd(self, widget, event):
        next((c[1] for c in self.key_commands 
                if ( Gtk.accelerator_parse(c[0]) ==
                     (Gdk.keyval_to_lower(event.keyval), event.state)
                   )),
                lambda : False)()
        self.cli.redraw()

    def mouse_cmd(self, widget, event):
        x = floor((event.x - self.bxoff)/self.sside)
        y = floor((event.y - self.byoff)/self.sside)
        if x < 0 or x > 7 or y < 0 or y > 7:
            return False
        s = (7-x, y) if self.flip else (x, 7-y)
        cmd = self.state.click(s)
        if(cmd):
            self.cli.send_cmd(cmd)
        self.redraw()

    def mouse_move(self, widget, event):
        if self.state.piece_clicked and not self.state.piece_flying:
            self.win.get_window().set_cursor(
                    self.ico_figures[self.state.piece_clicked])
            self.state.piece_flying = True
            self.redraw()

    def mouse_release(self, widget, event):
        self.win.get_window().set_cursor(None)
        x = floor((event.x - self.bxoff)/self.sside)
        y = floor((event.y - self.byoff)/self.sside)
        if x < 0 or x > 7 or y < 0 or y > 7:
            return False
        s = (7-x, y) if self.flip else (x, 7-y)
        cmd = self.state.release(s)
        if(cmd):
            self.cli.send_cmd(cmd)
        self.redraw()

    def on_resize(self, widget, cr):
        self.reload_figures()
        return True

    def reload_figures(self):
        wwidth  = self.get_allocated_width()
        wheight = self.get_allocated_height()
        side = min(wwidth,wheight)
        xoff = (wwidth-side)/2
        yoff = (wheight-side)/2
        bside = side-2*self.BORDER
        self.sside = bside/8

        self.bxoff = xoff + self.BORDER# + self.sside*0.5
        self.byoff = yoff + self.BORDER# + self.sside*0.5

        fig_scale = 1.17
        self.fig_scale = fig_scale
        mono_res = next(x for x in fsets if x >= self.sside/fig_scale)
        self.G = fig_scale*mono_res/self.sside
        self.mono_res = mono_res

        for mono in 'KQRBNPkqrbnp':
            fn = figPath+'/'+str(mono_res)+"/"+mono+".png"
            fd = cairo.ImageSurface.create_from_png(fn)
            self.png_figures[mono] = cairo.SurfacePattern(fd)
            if self.sside > 0:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(fn,
                        int(ceil(mono_res)), int(ceil(mono_res)))
                self.ico_figures[mono] = Gdk.Cursor.new_from_pixbuf(
                    Gdk.Display.get_default(),pb,int(mono_res/2),
                    int(mono_res/2))

    def on_draw(self, widget, cr):
        cr.select_font_face(config.board.font, cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_BOLD)
        wwidth  = self.get_allocated_width()
        wheight = self.get_allocated_height()
        side = min(wwidth,wheight)
        xoff = 0
        yoff = (wheight-side)/2
        bside = side-2*self.BORDER
        self.sside = bside/8

        self.bxoff = xoff + self.BORDER# + self.sside*0.5
        self.byoff = yoff + self.BORDER# + self.sside*0.5

        # Relojes
        cr.set_font_size(26)
        fascent, fdescent, fheight, fxadvance, fyadvance = cr.font_extents()
        xbearing, ybearing, width, height, xadvance, yadvance = (
                cr.text_extents("00  00:00"))

        if yoff > 0 :
            tp_xoff = xoff + 0.5
            tp_yoff = yoff + 0.5 - fdescent
            tc_xoff = side - xadvance + xoff
            tc_yoff = yoff + 0.5 - fdescent
            bp_xoff = xoff + 0.5
            bp_yoff = yoff + side + 0.5 + fascent
            bc_xoff = side - xadvance + xoff
            bc_yoff = yoff + side + 0.5 + fascent

            turn_width = wwidth
            turn_height = fheight*1.1 #yoff  #fheight+fdescent
            turn_x=0
            turn_y=yoff-fheight*1.1
            turn_yoff = fheight*1.1 #fheight+fdescent
        else:
            tp_xoff = side + xoff + 0.5
            tp_yoff = yoff + 0.5 + fascent
            tc_xoff = side + xoff + 0.5
            tc_yoff = yoff + 0.5 + fascent + fheight
            bp_xoff = side + xoff + 0.5
            bp_yoff = yoff + side + 0.5 - fdescent - fheight
            bc_xoff = side + xoff + 0.5
            bc_yoff = yoff + side + 0.5 - fdescent

            txt = max((t for t in ["00  00:00"]+ self.state.player),
                    key=lambda t: len(t))
            xbearing, ybearing, width, height, xadvance, yadvance = (
                    cr.text_extents(txt))
            turn_width = width*1.05
            turn_height = 2*fheight
            turn_x = side
            turn_y = 0
            turn_yoff = -2*fheight

        # Turn Square
        turn_y = turn_y + (0 if not (self.state.turn^self.flip)
                else (side+turn_yoff))
        cr.rectangle(turn_x, turn_y, turn_width, turn_height)
        self.turn_x      = int(turn_x)
        self.turn_y      = int(turn_y)
        self.turn_width  = int(ceil(turn_width))
        self.turn_height = int(ceil(turn_height))
        ma_time = self.state.time[self.state.turn]
        if (ma_time < 20 and ma_time % 2 and 
                (self.state.kind in ['playing', 'observing']) and
                not self.state.interruptus):
            cr.set_source_rgb(*config.board.turn_box_excl)
        else:
            cr.set_source_rgb(*config.board.turn_box)
        cr.fill()
        # Player TOP
        if not (self.state.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(tp_xoff, tp_yoff)
        cr.show_text(self.state.player[self.flip])
        cr.move_to(tc_xoff, tc_yoff)
        ma_time = self.state.time[self.flip]
        cr.show_text("{:>2} ".format(self.state.strength[self.flip]) +
                     (" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60))
        # Player BOTTOM
        if (self.state.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(bp_xoff, bp_yoff)
        cr.show_text(self.state.player[not self.flip])
        cr.move_to(bc_xoff, bc_yoff)
        ma_time = self.state.time[not self.flip]
        cr.show_text("{:>2} ".format(self.state.strength[not self.flip]) +
                     (" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60))
        # Mesa
        cr.set_source_rgb(*config.board.border)
        cr.rectangle(xoff, yoff, side, side)
        cr.fill()
        # Tablero
        cr.set_source_rgb(*config.board.dark_square)
        cr.rectangle(xoff+self.BORDER, yoff+self.BORDER, bside, bside)
        cr.fill()
        for i in range(0, 8):
            for j in range(0, 8):
                if (i+j)%2:
                    (x, y) = (7-i, j) if self.flip else (i, 7-j)
                    cr.set_source_rgb(*config.board.light_square)
                    cr.rectangle((xoff + self.BORDER + x*self.sside),
                                 (yoff + self.BORDER + y*self.sside),
                                 (self.sside), (self.sside))
                    cr.fill()
        for s in self.state.selected:
            i, j = s
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.set_source_rgb(
                   *(config.board.square_move_sent if self.state.move_sent else
                        (config.board.light_square_selected if (i+j)%2 else 
                            config.board.dark_square_selected))
                        )
            cr.rectangle((xoff + self.BORDER + x*self.sside),
                         (yoff + self.BORDER + y*self.sside),
                         (self.sside), (self.sside))
            cr.fill()
        for s in self.state.marked:
            i, j = s
            cr.set_source_rgb(*config.board.square_marked)
            lw = self.sside*0.04
            cr.set_line_width(lw)
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.rectangle((xoff + self.BORDER + x*self.sside+lw*0.5),
                         (yoff + self.BORDER + y*self.sside+lw*0.5),
                         (self.sside-lw), (self.sside-lw))
            cr.stroke()
        # Coordenadas
        if self.BORDER:
            cr.set_source_rgb(*config.board.text_active)
            cr.set_font_size(12)
            fascent, fdescent, fheight, fxadvance, fyadvance = cr.font_extents()
            for cx, letter in enumerate('abcdefgh'):
                coff = 7-cx if self.flip else cx
                xbearing, ybearing, width, height, xadvance, yadvance = (
                        cr.text_extents(letter))
                cxoff = (self.BORDER+self.sside/2+0.5+coff*self.sside
                            -xbearing-width/2)
                cyoff = 0.5 - fdescent + fheight / 2
                cr.move_to(xoff + cxoff,
                           self.BORDER*0.5 + yoff + cyoff)
                cr.show_text(letter)
                cr.rel_move_to(-width, bside + self.BORDER*1.3 -cyoff)
                cr.show_text(letter)
                number = str(coff+1) if self.flip else str(8-coff)
                xbearing, ybearing, width, height, xadvance, yadvance = (
                        cr.text_extents(number))
                cxoff = 0.5 - xbearing - width / 2
                cyoff = 0.5+0.5*self.sside+coff*self.sside-fdescent+fheight/2
                cr.move_to(self.BORDER*0.5 + xoff + cxoff,
                           self.BORDER     + yoff + cyoff)
                cr.show_text(number)
                cr.rel_move_to(bside + self.BORDER - width, 0)
                cr.show_text(number)
        # Figuras
        for s, f in self.state.figures():
            self.draw_piece(s,f,cr)
        # TAPON
        if self.state.interruptus:
            cr.rectangle(xoff, yoff, side, side)
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
            cr.fill()

    # figura
    def draw_piece(self, pos, fig, cr):
        cr.save()
        x, y = (7-pos[0], 7-pos[1]) if self.flip else (pos[0], pos[1])
        matrix = cairo.Matrix(
            xx = self.G, yy = self.G,
            x0 = self.G*(-self.bxoff-(x+0.5-0.5/self.fig_scale)*self.sside),
            y0 = self.G*(-self.byoff-(7-y+0.5-0.5/self.fig_scale)*self.sside))
        pattern = self.png_figures[fig]
        pattern.set_matrix(matrix)
        cr.rectangle(self.bxoff+x*self.sside,
                     self.byoff+(7-y)*self.sside,
                     self.sside, self.sside)
        cr.clip()
        cr.set_source(pattern)
        cr.paint()
        cr.restore()

    def redraw(self):
        GObject.idle_add(self.queue_draw)

    def redraw_turn(self):
        GObject.idle_add(
            self.queue_draw_area, self.turn_x, self.turn_y,
            self.turn_width, self.turn_height)
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
        print(event)
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
                dialog = BoardCommandsDialog(b)
                response = dialog.run()
                if response < 0:
                    return True
                elif response == 1:
                    self.cli.send_cmd("abort")
                    return True
                elif response == 2:
                    self.cli.send_cmd("resign")
                    self.boards.remove(b)
                    return False
                elif response == 3:
                    self.cli.send_cmd("adjourn")
                    return True
                dialog.destroy()
        self.boards.remove(b)
        return False

    def new_board(self, initial_state=None, game_info=None):
        b = Board(self,self.cli,
                  initial_state=initial_state,game_info=game_info)
        self.boards.append(b)
        b.win = Gtk.Window(title=b.state.name)
        b.win.add(b)
        b.win.connect('delete-event', self.on_board_delete)
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
            b.win.connect('delete-event', self.on_seek_graph_delete)
            self.cli.send_cmd("iset seekremove 1")
            self.cli.send_cmd("iset seekinfo 1")
            b.win.show_all()

def test_seek_graph():
    b = SeekGraph(0)
    b.win = Gtk.Window(title="Seek Graph")
    b.win.add(b)
    b.win.connect('delete-event', Gtk.main_quit)
    b.win.show_all()
    Gtk.main()

class TestCli:
    def __init__(self):
        foo = 'caca'
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
    initial_state = '<12> rnbqkbnr pppppppp -------- -------- -------- -------- PPPPPPPP RNBQKBNR W -1 1 1 1 1 0 14 GuestXYQM estebon 1 5 5 19 39 10 30 1 none (0:00) none 0 0 0'
    b = Board(TestGui(), TestCli(), game_info=game_info)
    #b = Board(0, 0, initial_state=initial_state)
    b.set_state(initial_state)
    b.set_state('<12> rnbqkbnr p-pppppp -------- -p------ -------- -------- PPPPPPPP RNBQKBNR B -1 1 1 1 1 0 14 GuestXYQM estebon -1 5 5 19 39 100 300 1 none (0:00) none 0 0 0')
    b.set_state('<12> rnbqkbnr p-pppppp -------- -p------ -------- -------- PPPPPPPP RNBQKBNR B -1 1 1 1 1 0 14 GuestXYQM estebon -1 5 5 19 39 1 1 1 none (0:00) none 0 0 0')
    #b.interruptus = True
    b.win = Gtk.Window(title=b.state.name)
    b.win.add(b)
    b.win.connect('delete-event', Gtk.main_quit)
    b.win.show_all()
    Gtk.main()
    return b

if __name__ == '__main__':
    #test_seek_graph()
    b = test_board()
    pass

