# gui - GUI class

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

if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config
from papageorge.board import Board, BoardExit
from papageorge.seekgraph import SeekGraph

from gi.repository import Gtk, Gdk 

class GUI:
    def __init__(self, cli):
        self.cli = cli
        self.boards = []
        self.seek_graph = None

    def on_board_delete(self, widget, event):
        b = widget.get_children()[0]
        if b.state.kind == 'examining':
            self.cli.send_cmd("unexamine", save_history=False,
               wait_for='You are no longer examining game {}'.format(b.board_number))
            self.boards.remove(b)
            return False
        elif b.state.kind == 'observing':
            if not b.state.interruptus:
                self.cli.send_cmd("unobserve {}".format(b.board_number),
                        save_history=False,
                        wait_for='Removing game {}'.format(b.board_number))
            self.boards.remove(b)
            return False
        elif b.state.kind == 'playing':
            if b.state.interruptus:
                self.boards.remove(b)
                return False
            else:
                BoardExit(b)
                return True
        self.boards.remove(b)
        return False

    def on_board_focus(self, widget, direction):
        b = widget.get_children()[0]
        if (b.state.kind == 'observing' and 
             len([b for b in self.boards if b.state.kind == 'observing'])>1 and
             not b.state.interruptus):
            self.cli.send_cmd('primary {}'.format(b.board_number),
                                save_history=False)

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
        self.cli.send_cmd("iset seekremove 0", save_history=False)
        self.cli.send_cmd("iset seekinfo 0", save_history=False)
        self.seek_graph = None
        return False

    def seek_graph_destroy(self):
        if self.seek_graph:
            self.cli.send_cmd("iset seekremove 0", save_history=False)
            self.cli.send_cmd("iset seekinfo 0", save_history=False)
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
            self.cli.send_cmd("iset seekremove 1", save_history=False)
            self.cli.send_cmd("iset seekinfo 1", save_history=False)
            b.win.show_all()

