# game - Game class

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

if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config

from time import time

def postopos(pos):
    return chr(97 + pos[0]) + str(pos[1]+1)

def pos2pos(pos):
    return (ord(pos[0])-97,  int(pos[1])-1)

def rewind(state):
    if state.prev:
        return rewind(state.prev)
    else:
        return state

def contiguous(src, dst):
    if dst.halfmove-src.halfmove != 1:
        return False
    D = set(dst - src)
    if dst.cmove == 'o-o':
        x = 0 if src.turn else 7
        if (D == {(4,x), (5,x), (6,x), (7,x)} and
                src.piece_in((4,x)).lower() == 'k' and
                src.piece_in((7,x)).lower() == 'r'):
            return True
        else:
            return False
    if dst.cmove == 'o-o-o':
        x = 0 if src.turn else 7
        if (D == {(0,x), (2,x), (3,x), (4,x)} and
                src.piece_in((4,x)).lower() == 'k' and
                src.piece_in((0,x)).lower() == 'r'):
            return True
        else:
            return False
    p, m = dst.cmove.split('/')
    s, d = m.split('-')
    s = pos2pos(s)
    d = pos2pos(d)
    DD = {s,d}^D
    if len(DD) == 1: 
        dp = DD.pop()
        if (p.lower() == 'p' and 
                dp[1] == (4 if src.turn else 3) and
                src.piece_in(s).lower() == 'p' and
                src.piece_in(dp).lower() == 'p' and
                not src.piece_in(d)):
            return True
        else:
            return False
    if (len({s, d} ^ D) or (src.piece_in(s).lower() != p.lower())):
        return False
    else:
        return True

class GameHistory(list):
    _not_connected = []

    def append(self, state):
        i = next((self.index(x) for x in self
                      if x.halfmove >= state.halfmove), None)
        if i != None:
            if contiguous(state, self[i]):
                state.next.append(self[i])
            elif state == self[i]:
                for x in self[i].next:
                    x.prev = state
                    state.next.append(x)
                self[i].next.clear()
                if self[i].prev:
                    self[i].prev.next.remove(self[i])
            elif i==0:
                o = rewind(self[i])
                if o not in self._not_connected:
                    self._not_connected.append(o)
            for x in self[i::]:
                self.remove(x)
        if len(self):
            if contiguous(self[-1], state):
                state.prev = self[-1]
                self[-1].next.append(state)
            else:
                o = rewind(self[-1])
                if o not in self._not_connected:
                    self._not_connected.append(o)
                self.clear()
        super().append(state)

    def go_deeper(self, lines, state, line):
        if not len(state.next):
            lines.append(' '.join(line+[state.move]))
        else:
            for x in state.next:
                self.go_deeper(lines, x, line+[state.move])

    def get_lines(self):
        lines = []
        self.go_deeper(lines,rewind(self[0]),[])
        ncl = []
        for x in self._not_connected:
            self.go_deeper(ncl,x,[])
        return lines, ncl

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
        self.cmove = svalue[27]
        self.move = svalue[29]
        self.time = time()
        # history tree
        self.next = []
        self.prev = None

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

class Game:
    def __init__(self,
                 gui,
                 cli,
                 initial_state=None,
                 game_info=None,
                 board=None):
        # world
        self.gui = gui
        self.cli = cli
        self.board = None
        self.waiting_for_board = False
        # game
        self._history = GameHistory([])
        self._showing = -1
        self.marked = []
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
        self.side = True
        self.itime = self.iinc = ''
        self.name = ''
        self.interruptus = False
        if game_info:
            self.set_gameinfo(game_info)
        if initial_state:
            self.set_state(initial_state)
        if board:
            board.set_game(self)
            self.board = board

    def set_board(self, board):
        self.board = board

    def set_interruptus(self):
        self.interruptus = True
        if self.board:
            self.board.reset(True)

    def set_gameinfo(self, info):
        self.number = int(info.split()[1])
        self.rating = ['('+x+')' for x in
                 info.split()[9].split('=')[1].split(',')[::-1]]
        self.rated = ('rated' if info.split()[4].split('=')[1] == '1'
                                else 'unrated')

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

    def set_state(self, new_state):
        self.interruptus = False
        state = Style12(new_state)
        #i = next((self._history.index(x) for x in self._history
                            #if x.halfmove >= state.halfmove), None)
        #if i != None:
            #self._history = self._history[:i]
        self._history.append(state)
        self._showing = -1
        self.move_sent = False
        self.update_marked()
        self.turn = state.turn
        #flush premove
        if (self.kind == 'playing' and len(self.selected) == 2 and
                self.side == self.turn and self.halfmove != state.halfmove):
            self.cli.send_cmd((postopos(self.selected[0])+
                        postopos(self.selected[1])), save_history=False)
        # move was ilegal? preserve selected piece
        elif (len(self.selected) == 2 and self.halfmove == state.halfmove):
            self.selected.pop()
        elif (self.kind == 'playing' and len(self.selected) == 1 and
                self.side == self.turn):
            pass
        else:
            self.selected.clear()
        self.halfmove = state.halfmove
        if len(self._history) == 1:
            self.number = state.game_number
            self.player = [state.bname+self.rating[0],
                           state.wname+self.rating[1]]
            self.player_names = [state.bname, state.wname]
            self._kind = state.relation
            self.side = ((self.turn and (self._kind == 1)) or
                         ((self._kind == -1) and not self.turn) or
                         (self.kind != 'playing' and
                             self.player_names[0] != config.fics_user))
            self.opponent = self.player_names[not self.side]
            self.me       = self.player_names[self.side]
            self.itime = state.itime
            self.iinc  = state.iinc
            self.name = ('Game {}: '.format(state.game_number) +
                         ('Examining ' if self.kind == 'examining' else
                          'Observing ' if self.kind == 'observing' else '')+
                          ' v/s '.join(self.player[::-1])+' - '+
                          '/'.join([self.itime, self.iinc])+' - '+
                          self.rated).strip()
            if self.kind in ['examining', 'playing']:
                self.gui.seek_graph_destroy()
            if self.board:
                self.board.reset(True)
        else:
            if self.board:
                self.board.reset(False)

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
                self.set_state(self._history[-1].duplicate(self.selected))
                self.interruptus = True
            elif (self.kind != 'playing') or (self.side == self.turn) :
                self.move_sent = True
                return (postopos(self.selected[0])
                            +postopos(self.selected[1]))
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
                    self.set_state(self._history[-1].duplicate(self.selected))
                    self.interruptus = True
                elif (self.kind != 'playing') or (self.side == self.turn) :
                    self.move_sent = True
                    return (postopos(self.selected[0])
                             +postopos(self.selected[1]))
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
    def material(self):
        if len(self._history):
            d = (self._history[-1].wstrength-self._history[-1].bstrength)*(
                    1 if self.side else -1)
            return '=' if not d else '{:+d}'.format(d)

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

if __name__ == '__main__':
    h = []
    h = GameHistory([])

    h.append(Style12('<12> rnbqkbnr pppppppp -------- -------- -------- -------- PPPPPPPP RNBQKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 1 none (0:00) none 0 0 0'))
    h.append(Style12('<12> rnbqkbnr pppppppp -------- -------- ---P---- -------- PPP-PPPP RNBQKBNR B 3 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 1 P/d2-d4 (0:00) d4 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p-pppppp -p------ -------- ---P---- -------- PPP-PPPP RNBQKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 2 P/b7-b6 (0:00) b6 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p-pppppp -p------ ---P---- -------- -------- PPP-PPPP RNBQKBNR B -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 2 P/d4-d5 (0:00) d5 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp -p------ --pP---- -------- -------- PPP-PPPP RNBQKBNR W 2 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 3 P/c7-c5 (0:00) c5 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp -pP----- -------- -------- -------- PPP-PPPP RNBQKBNR B -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 38 0 0 3 P/d5-c6 (0:00) dxc6 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -p------ -------- -------- PPP-PPPP RNBQKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 38 0 0 4 P/b6-b5 (0:00) b5 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -p------ -----B-- -------- PPP-PPPP RN-QKBNR B -1 1 1 1 1 1 170 GuestXXSW GuestXXSW 2 0 0 39 38 0 0 4 B/c1-f4 (0:00) Bf4 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -------- -p---B-- -------- PPP-PPPP RN-QKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 38 0 0 5 P/b5-b4 (0:00) b4 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -------- Pp---B-- -------- -PP-PPPP RN-QKBNR B 0 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 38 0 0 5 P/a2-a4 (0:00) a4 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -------- -----B-- p------- -PP-PPPP RN-QKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 6 P/b4-a3 (0:00) bxa3 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--ppppp --P----- -------- ---Q-B-- p------- -PP-PPPP RN--KBNR B -1 1 1 1 1 1 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 6 Q/d1-d4 (0:00) Qd4 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--pp-pp --P--p-- -------- ---Q-B-- p------- -PP-PPPP RN--KBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 7 P/f7-f6 (0:00) f6 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--pp-pp --P--p-- -------- ---Q-B-- p------- -PPNPPPP R---KBNR B -1 1 1 1 1 1 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 7 N/b1-d2 (0:00) Nd2 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--p--pp --P--p-- ----p--- ---Q-B-- p------- -PPNPPPP R---KBNR W 4 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 8 P/e7-e5 (0:00) e5 0 0 0'))
    h.append(Style12('<12> rnbqkbnr p--p--pp --P--p-- ----p--- ---Q-B-- p------- -PPNPPPP --KR-BNR B -1 0 0 1 1 1 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 8 o-o-o (0:00) O-O-O 0 0 0'))
    h.append(Style12('<12> rnbqk-nr p--p--pp --P--p-- --b-p--- ---Q-B-- p------- -PPNPPPP --KR-BNR W -1 0 0 1 1 2 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 9 B/f8-c5 (0:00) Bc5 0 0 0'))
    h.append(Style12('<12> rnbqk-nr p--p--pp --P--p-- --b-p--- -Q---B-- p------- -PPNPPPP --KR-BNR B -1 0 0 1 1 3 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 9 Q/d4-b4 (0:00) Qb4 0 0 0'))
    h.append(Style12('<12> rnbqk--r p--pn-pp --P--p-- --b-p--- -Q---B-- p------- -PPNPPPP --KR-BNR W -1 0 0 1 1 4 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 10 N/g8-e7 (0:00) Ne7 0 0 0'))
    h.append(Style12('<12> rnbqk--r p--pn-pp --P--p-- --b-p--- -Q---B-- p-----P- -PPNPP-P --KR-BNR B -1 0 0 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 10 P/g2-g3 (0:00) g3 0 0 0'))
    h.append(Style12('<12> rnbq-rk- p--pn-pp --P--p-- --b-p--- -Q---B-- p-----P- -PPNPP-P --KR-BNR W -1 0 0 0 0 1 170 GuestXXSW GuestXXSW 2 0 0 38 38 0 0 11 o-o (0:00) O-O 0 0 0'))

    #for i in range(len(h)-1):
        #print('{} {} {}'.format(i, h[i+1].move, contiguous(h[i], h[i+1])))
        


    print('Main line: '+' '.join([x.move for x in h]))
    print('All lines:')
    l, c = h.get_lines()
    print(l)
    print(c)


'''

What to do when incoming state can not be connected to the mainline? (as for
instance, when jumps occur) should verification be done on-site?

-> always check when stablishing a connection (setting next or prev) if the
incomming state has no connection to the stored _history, store the
rewind(_history[0]) in an _non_connected list (if its not already there) and do
_history.clear() before inserting the new state. afterwards, when new states
arrive, check if there is a connection with the lines in _non_connected if its
not empty (auto repair)

_non_connected lines could be shown separatedly to see where the missing link is

ojo con clock updates? -> replace

verification: check if move transforms one state in the other ojo: move legality
has already been checked by server, we only need to check that piece and origin
match 
'''

