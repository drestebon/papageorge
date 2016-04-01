# seekgraph - Seekgraph class

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

if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config

from math import pi, sqrt
from gi.repository import GObject, Gtk, Gdk
import cairo

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
    def __init__(self, initial_state = None):
        Gtk.DrawingArea.__init__(self)
        bg = Gdk.RGBA.from_color(Gdk.color_parse('#242424'))
        self.override_background_color(Gtk.StateType.NORMAL, bg)
        self.connect('draw', self.on_draw)
        self.connect('size_allocate', self.on_resize)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button_press_event', self.mouse_cmd)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion-notify-event', self.hover)
        self.active_seek = None
        self.seeks = []
        if initial_state:
            self.update(initial_state)
        self.win = Gtk.Window(title="Seeks")
        self.win.add(self)
        self.win.set_default_size(400,400)
        self.win.connect('key_press_event', self.key_cmd)
        self.win.connect('delete-event', self.on_seek_graph_delete)
        self.win.show_all()

    def on_seek_graph_delete(self, widget, event):
        config.gui.seek_graph_destroy()
        return False

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
        if event.keyval == Gdk.KEY_Escape:
            config.gui.seek_graph_destroy()
        else:
            config.cli.key_from_gui(event.keyval)
            config.cli.redraw()

    def mouse_cmd(self, widget, event):
        if self.active_seek in self.seeks:
            config.cli.send_cmd("play {}".format(self.active_seek.idx),
                    save_history=False)
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

    def redraw(self):
        GObject.idle_add(self.queue_draw)

