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

    def new_board(self, initial_state=None, game_info=None):
        b = Board(self,self.cli,
                  initial_state=initial_state,
                  game_info=game_info)
        self.boards.append(b)
        self.cli.connect_board(b)

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
            self.seek_graph = SeekGraph(self,
                                        self.cli,
                                        initial_state=initial_state)
            self.cli.send_cmd("iset seekremove 1", save_history=False)
            self.cli.send_cmd("iset seekinfo 1", save_history=False)

