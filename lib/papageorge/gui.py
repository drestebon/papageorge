# gui - GUI class

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

# ♔ ♕ ♖ ♗ ♘ ♙ ♚ ♛ ♜ ♝ ♞ ♟ 

if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config
from papageorge.game import Game
from papageorge.board import Board
from papageorge.seekgraph import SeekGraph
from papageorge.general import *

from gi.repository import Gtk, Gdk 

class GUI:
    def __init__(self):
        self.games = []
        self.seek_graph = None

    def game_with_number(self, n):
        return next((g for g in self.games
                      if g.number == n), False )

    def assign_board(self, game):
        if config.board.auto_replace == 'off':
            game.set_board(Board(game))
        else:
            b = next((g.board for g in self.games if
                    (len([p for p in game.player_names if p in g.player_names]) and
                       g.interruptus and (game.kind ^ KIND_EXAMINING and g.kind == game.kind
                           or g.kind & KIND_PLAYING and game.kind & KIND_EXAMINING ))), False)
            if b:
                game.waiting_for_board = True
                b.change_game(game)
            else:
                game.set_board(Board(game))

    def style12(self, txt):
        gn = int(txt.split()[16])
        if gn in config.block12:
            config.block12.clear()
            return
        else:
            config.block12.clear()
        game = self.game_with_number(gn)
        if game:
            game.set_state(txt)
            if not game.board and not game.waiting_for_board:
                self.assign_board(game)
        else:
            self.new_game(initial_state=txt)

    def new_game(self, initial_state=None, game_info=None):
        game = Game(initial_state=initial_state, game_info=game_info)
        if initial_state:
            self.assign_board(game)
        self.games.append(game)

    def game_destroy(self, game):
        self.games.remove(game)
        if game.board:
            game.board.win.destroy()

    def seek_graph_destroy(self):
        if self.seek_graph:
            config.cli.send_cmd("iset seekremove 0",
                              wait_for='seekremove unset',
                              save_history=False, record_handle=False)
            config.cli.send_cmd("iset seekinfo 0",
                              wait_for='seekinfo unset',
                              save_history=False, record_handle=False)
            self.seek_graph.win.destroy()
            self.seek_graph = None

    def new_seek_graph(self, initial_state=None):
        if len([x for x in self.games
                  if (x.kind & KIND_EXAMINING
                      or (x.kind & KIND_PLAYING
                          and not x.interruptus))]) == 0:
            self.seek_graph = SeekGraph(initial_state=initial_state)
            config.cli.send_cmd("iset seekremove 1",
                              wait_for='seekremove set',
                              save_history=False)
            config.cli.send_cmd("iset seekinfo 1",
                              wait_for='seekinfo set',
                              save_history=False)

