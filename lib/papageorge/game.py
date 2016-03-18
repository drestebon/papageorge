# game - Game class

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
from papageorge.general import *
from papageorge.model import GameHistory, GameState, Style12, postopos, pos2sq, rewind
from papageorge.pgn import Pgn

from time import time, localtime, strftime
import re

class Game:
    MOVES_TO_PGN = re.compile('\(\d+?:\d+?\)')
    PLAYER_NAME = re.compile('\w+')

    def __init__(self,
                 initial_state=None,
                 game_info=None,
                 board=None):
        # world
        self.board = None
        self.waiting_for_board = False
        # game
        self._history = GameHistory()
        self.selected = []
        self.piece_flying = False
        self.piece_clicked = False
        self.move_sent = False
        # properties
        self.turn = True
        self.halfmove = -1
        # ONESHOT PROPS
        self.number = 0
        self.rating = ['','']
        self.rated = ''
        self.player = ['','']
        self.player_names = ['','']
        self.opponent = self.me = ''
        self._kind = 0
        self.kind = 0
        self.side = True
        self.itime = self.iinc = ''
        self.name = ''
        self.interruptus = False
        self.altline = False
        self.last_style12 = None
        self.result = None
        if game_info:
            self.set_gameinfo(game_info)
        if initial_state:
            self.set_state(initial_state)
        if board:
            board.set_game(self)
            self.board = board

    def set_board(self, board):
        self.board = board

    def set_interruptus(self, result=None):
        if not self.result:
            self.result = result
            if result:
                self.name = self.name + ' - ' + result
        self.interruptus = True
        if self.board:
            self.board.reset(True)

    def set_altline(self):
        self.altline = not isinstance(self._history[-1], Style12)

    def set_gameinfo(self, info):
        self.number = int(info.split()[1])
        self.rating = ['('+x+')' for x in
                 info.split()[9].split('=')[1].split(',')[::-1]]
        self.rated = ('rated' if info.split()[4].split('=')[1] == '1'
                                else 'unrated')

    def set_state(self, new_state):
        if isinstance(new_state, GameState):
            state = new_state
        else:
            state = Style12(new_state)
            self.interruptus = False
            self.last_style12 = state
        if not self._history.update(state) and self.opponent != '':
            self.fill_history(state)
        if state in self._history or self.kind & KIND_EXAMINING:
            r = self._history.set_mainline(state)
            if self.board and self.board.movetree:
                if r:
                    self.board.movetree.set_mainline(*r)
                else:
                    self.board.movetree.repopulate()
        elif self.board and self.board.movetree:
            self.board.movetree.update_node(state)
        self.move_sent = False
        if state is self._history[-1]:
            self.turn = state.turn
        #flush premove
        if (self.kind & KIND_PLAYING and len(self.selected) == 2 and
                self.side == self.turn and self.halfmove != state.halfmove):
            config.cli.send_cmd((postopos(self.selected[0])+
                        postopos(self.selected[1])), save_history=False)
        # move was ilegal? preserve selected piece
        elif (len(self.selected) == 2 and self.halfmove == state.halfmove):
            self.selected.pop()
        elif (self.kind & KIND_PLAYING and len(self.selected) == 1 and
                self.side == self.turn):
            pass
        elif state is not self._history[-1]:
            pass
        else:
            self.selected.clear()
        self.halfmove = state.halfmove
        if (not self.player_names == state.names or
                self._kind != state.relation):
            self.number = state.game_number
            self.player = [state.names[0]+self.rating[0],
                           state.names[1]+self.rating[1]]
            self.player_names = state.names
            self._kind = state.relation
            self.kind = (KIND_PLAYING if abs(self._kind) == 1 else
                         KIND_OBSERVING if self._kind == 0 else
                         KIND_EXAMINING if self._kind == 2 else
                         KIND_ISOLATED if self._kind == -3 else
                         KIND_OBSERVING | KIND_EXAMINING)
            self.side = ((self.turn and (self._kind == 1)) or
                         ((self._kind == -1) and not self.turn) or
                         (self.kind ^ KIND_PLAYING and
                             (self.player_names[0] != config.fics_user or
                                 self.player_names[1] == config.fics_user)))
            self.opponent = self.player_names[not self.side]
            self.me       = self.player_names[self.side]
            self.itime = state.itime
            self.iinc  = state.iinc
            self.name = ('Game {}: '.format(state.game_number) +
                         ('Observing ' if self.kind & KIND_OBSERVING else
                          'Examining ' if self.kind & KIND_EXAMINING else '')+
                          ' v/s '.join(self.player[::-1])+' - '+
                          '/'.join([self.itime, self.iinc])+
                          # (' - '+self.rated if self.rated else '' )+
                          (' - ' + self.result if self.result else '')
                          ).strip()
            if self.kind & KIND_OBSERVING:
                self.get_old_moves()
            if self.kind & (KIND_EXAMINING | KIND_PLAYING):
                config.gui.seek_graph_destroy()
            if self.board:
                self.board.reset(True)
            for hdl in self.player_names:
                config.update_handle(hdl)
        else:
            if self.board:
                self.board.reset(False)

    def get_moves(self):
        moves_txt = list()
        if config.cli.send_cmd('moves {}'.format(self.number),
                                wait_for=WAIT_FOR_MOVELIST, ans_buff=moves_txt,
                                save_history=False):
            moves_txt = ''.join(moves_txt)
            if ' 1. ' in moves_txt:
                moves_txt = moves_txt[moves_txt.index(' 1. ')::]
                moves_txt = self.MOVES_TO_PGN.sub('', moves_txt)
                return Pgn(txt=moves_txt).main_line
        return list()

    def fill_history(self, state):
        l = self.get_moves()
        m = next((x for x in self._history._directory.back_sorted() if x in l), None)
        if m:
            l = l[l.index(m)+1:l.index(state)]
            if l:
                l[0].prev = m
                m.next.append(l[0])
                l[-1].next.clear()
                if m in self._history:
                    self._history.extend(l)
                else:
                    for x in l:
                        self._history.update_reg(x)
                self._history.update(state)

    def get_old_moves(self):
        l = self.get_moves()
        n, i = next(((x,l.index(x)) for x in l
                if x == self._history[0]), (None, 0))
        if i:
            for x in l[i::]:
                l.remove(x)
                l._directory[x.halfmove].clear()
            for x in self._history:
                l.update_reg(x)
            l[-1].next = list([self._history[0]])
            self._history[0].prev = l[-1]
            l.extend(self._history)
            self._history = l

    def backward(self, n):
        for i in range(n):
            if len(self._history)>1:
                x = self._history.pop()
                if x and self.board and self.board.movetree:
                    self.board.movetree.recolor(x)
            else:
                break
        self.turn = self._history[-1].turn
        if not (self.kind & (KIND_OBSERVING | KIND_PLAYING)):
            config.cli.send_cmd('backward {}'.format(n), save_history=False)
        elif not len(self._history):
            config.cli.print("You're at the beginning of the game.")
        if isinstance(self._history[-1], Style12):
            self.altline = False

    def forward(self, n):
        if self.kind & (KIND_OBSERVING | KIND_PLAYING):
            for i in range(n):
                if len(self._history[-1].next):
                    x = self._history[-1].next[0]
                    self._history.append(x)
                    if x and self.board and self.board.movetree:
                        self.board.movetree.recolor(x)
                else:
                    break
            self.turn = self._history[-1].turn
        elif not (self.kind & (KIND_OBSERVING | KIND_PLAYING)):
            config.cli.send_cmd('forward {}'.format(n), save_history=False)
        if (self.kind & KIND_OBSERVING and 
                not isinstance(self._history[-1], Style12)):
            self.altline = True

    def piece_in(self, pos):
        return self._history[-1].piece_in(pos)

    def click(self, pos):
        x = self.piece_in(pos)
        # Another piece is selected
        if (x and
            (self.side if self.kind & KIND_PLAYING
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
            if self.kind & KIND_OBSERVING:
                ns = self._history[-1].make(self.selected)
                if ns:
                    self.set_state(ns)
                    self.altline = True
                else:
                    self.selected.pop()
            elif (self.kind ^ KIND_PLAYING) or (self.side == self.turn) :
                self.move_sent = True
                return (postopos(self.selected[0])
                            +postopos(self.selected[1]))
            return None

    def release(self, pos):
        if self.piece_flying:
            self.piece_flying = False
            x = self.piece_in(pos)
            if (x and
                    (self.side if self.kind & KIND_PLAYING
                     else self.turn) == x.isupper()):
                self.piece_clicked = x
                self.selected.clear()
                self.selected.append(pos)
                return None
            # MOVE
            if len(self.selected):
                if len(self.selected) > 1:
                    self.selected.pop()
                self.selected.append(pos)
                if self.kind & KIND_OBSERVING:
                    ns = self._history[-1].make(self.selected)
                    if ns:
                        self.set_state(ns)
                        self.altline = True
                    else:
                        self.selected.pop()
                elif (self.kind ^ KIND_PLAYING) or (self.side == self.turn) :
                    self.move_sent = True
                    return (postopos(self.selected[0])
                             +postopos(self.selected[1]))
                return None

    def figures(self):
        if len(self._history):
            fl = [ x for x in self._history[-1].figures
                      if x[0] not in self.selected ]
            if not self.piece_flying and len(self.selected) > 1:
                if self.piece_in(self.selected[-2]):
                    fl.append((self.selected[-1],
                        self.piece_in(self.selected[-2])))
                return fl
            elif not self.piece_flying and len(self.selected):
                if self.piece_in(self.selected[-1]):
                    fl.append((self.selected[-1],
                        self.piece_in(self.selected[-1])))
                return fl
            else:
                return fl
        else:
            return []

    def is_being_played(self):
        return ((not (self.kind & (KIND_EXAMINING | KIND_ISOLATED))) and
                    not self.interruptus)

    def pgn(self, fd, save_timestamps=False):
        root = rewind(self._history[0])
        if root.next:
            start_time = root.next[0].time
        else:
            start_time = time()
        date = strftime('%Y.%m.%d', localtime(start_time))
        print('[Date "{}"]'.format(date), file=fd)
        if self.result:
            print('[Result "{}"]'.format(self.result), file=fd)
        print('[White "{}"]'.format(self.player_names[1]), file=fd)
        print('[Black "{}"]'.format(self.player_names[0]), file=fd)
        print('[FEN "{}"]\n'.format(root.fen()), file=fd)
        L = list()
        l = list()
        x = root
        Lpoped = False
        split = False
        while x:
            if x and x.halfmove>=0 and not Lpoped:
                if x.halfmove%2:
                    print(x.move, end=' ', file=fd)
                else:
                    print(str(x.halfmove//2+1)+'. '+x.move, end=' ', file=fd)
                if save_timestamps:
                    times = (x.btime if x.halfmove%2 else x.wtime)
                    print('{{ ({}:{}) }}'.format(times//60, times%60), end=' ', file=fd)
                if x.comment:
                    print('{{ {} }}'.format(x.comment), end=' ', file=fd)
            if not x.next and L and not split:
                print(')', end=' ', file=fd)
            Lpoped = False
            if x.next and not split:
                if len(x.next) > 1:
                    L.append(x.next[0])
                    l.append(x.next[1::][::-1])
                    x = x.next[0]
                    split = True
                else:
                    x = x.next[0]
            else:
                if l:
                    if l[-1]:
                        x = l[-1].pop()
                        print('(', end=' ', file=fd)
                        if x.halfmove%2:
                            print(str(x.halfmove//2+1)+'. ... ', end=' ', file=fd)
                    else:
                        l.pop()
                        if L:
                            x = L.pop()
                            Lpoped = True
                        else:
                            x = None
                else:
                    if L:
                        x = L.pop()
                        Lpoped = True
                        print(')', end=' ', file=fd)
                    else:
                        x = None
                split = False
        print('\n', file=fd)

    def setup_from_pgn(self, pgn):
        self._history = pgn.main_line
        for x in self._history[1::]:
            self._history.remove(x)
        root = self._history[-1]
        x = next((x[1] for x in pgn.header if x[0].lower() == 'fen'), None)
        if x:
            fen = x.split()
            config.cli.send_cmd('bsetup fen '+fen[0], save_history=False)
            config.cli.send_cmd('tomove '+('white' if fen[1]=='w' else 'black'), save_history=False)
            config.cli.send_cmd('bsetup done', save_history=False)
        x = next((x[1] for x in pgn.header if x[0].lower() == 'result'), None)
        if x:
            self.result = x
        for c, n in zip(['black', 'white'], ['bname ', 'wname ']):
            x = next((x[1] for x in pgn.header if x[0].lower() == c), None)
            if x:
                m = self.PLAYER_NAME.match(x)
                if m:
                    x = m.group()
                    config.cli.send_cmd(n+x, save_history=False)
        if self.board:
            self.board.reset(True)
            if self.board.movetree:
                self.board.movetree.repopulate()

    @property
    def marked(self):
        return [ pos2sq(x) for x in self._history.marked() ]

    @property
    def material(self):
        if len(self._history):
            d = (self._history[-1].strength[1]-self._history[-1].strength[0])*(
                    1 if self.side else -1)
            return '=' if not d else '{:+d}'.format(d)
        else:
            return '='

    @property
    def time(self):
        if len(self._history):
            if (self.is_being_played() and
                    self.halfmove > 2 and
                    (not self.interruptus) and
                    self.last_style12 is self._history[-1]):
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

