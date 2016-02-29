# model - chess game model

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

from papageorge.notation import San, CoordsMove
import papageorge.config as config

from time import time
import re

BB_MASK = 0xFFFFFFFFFFFFFFFF

class BB(object):
    def __init__(self, state):
        self.piece = { x:0 for x in 'RNBQKPrnbqkp' }
        for i, x in enumerate(state):
            if x != '-':
                self.piece[x] |= 1<<i
        self.cocc = [0,0]
        for x in self.piece.keys():
            self.cocc[x.isupper()] |= self.piece[x]
        self.occ = self.cocc[0] | self.cocc[1]

    def pieces_but(self, x):
        r = 0
        for p in 'RNBQKPrnbqkp'.replace(x,''):
            r |= self.piece[p]
        return r

def print_rank(x, mark=[]):
    if len(mark):
        s = '{:08b}'.format(x)[::-1]
        for i in mark:
            s = s[0:i]+'*'+s[i+1::]
        print(s)
    else:
        print('{:08b}'.format(x)[::-1])

def printBB(x, mark=[]):
    for i in range(56, -1, -8):
        if not len(mark):
            print_rank((x>>i)&255)
        else:
            marks = []
            for j in mark:
                if j in range(i, i+8):
                    marks.append(j-i)
            print_rank((x>>i)&255, mark=marks)

def pos2sq(pos):
    return (pos%8, pos//8)

def pos2pos(pos):
    return ord(pos[0])-97+((int(pos[1])-1)<<3)

def postopos(pos):
    if isinstance(pos, tuple):
        return chr(97+pos[0])+str(pos[1]+1)
    else:
        return chr(pos%8+97)+str(pos//8+1)


def rank_mask(x):
    if x >= 0 and x < 8:
        return 0xFF<<(8*x)
    else:
        return 0x0

def file_mask(x):
    if x >= 0 and x < 8:
        return 0x0101010101010101<<x
    else:
        return 0x0

# RANK
def rank(x, sq):
    return x>>(sq-sq%8)&255

def pos_in_rank(sq):
    return sq%8

def rank_posmap(pos, sq):
    return pos+sq-sq%8

# FILE
#sq' = ((sq >> 3) | (sq << 3)) & 63;
def flip(x):
   k1 = 0x5500550055005500
   k2 = 0x3333000033330000
   k4 = 0x0f0f0f0f00000000
   t  = k4 & (x ^ (x << 28))
   x ^=       t ^ (t >> 28)
   t  = k2 & (x ^ (x << 14))
   x ^=       t ^ (t >> 14)
   t  = k1 & (x ^ (x <<  7))
   x ^=       t ^ (t >>  7)
   return x

def file(x, sq):
    return flip(x)>>((sq%8)<<3)&255

def pos_in_file(sq):
    return sq//8

def file_posmap(pos, sq):
    return (pos<<3)+sq%8

# MAIN DIAGONAL
def rotR(x, s):
    return ((x >> s) | (x << (64-s)))&BB_MASK

def rot45clk(x):
   x ^= 0xAAAAAAAAAAAAAAAA & (x ^ rotR(x,  8))
   x ^= 0xCCCCCCCCCCCCCCCC & (x ^ rotR(x, 16))
   x ^= 0xF0F0F0F0F0F0F0F0 & (x ^ rotR(x, 32))
   return x;

def mdiag(x, sq):
    i = (sq%8-sq//8)&0xF
    shift = ((-i)&7)*8+i*(i<8)
    mask = 255&((-256)>>(8-abs(8-i)))
    return ((rot45clk(x) >> shift) | mask)&255

def pos_in_mdiag(sq):
    return min(sq%8, sq//8)

def mdiag_posmap(pos, sq):
    i = (sq%8-sq//8)&0xF
    shift = ((-i)&7)*8+i*(i<8)
    sq = shift+pos
    return (sq + 8*((sq&7))) & 63

# ANTI DIAGONAL
def rot45aclk(x):
   x ^= 0x5555555555555555 & (x ^ rotR(x,  8))
   x ^= 0x3333333333333333 & (x ^ rotR(x, 16))
   x ^= 0x0f0f0f0f0f0f0f0f & (x ^ rotR(x, 32))
   return x

def adiag(x, sq):
    i = (sq%8+sq//8)^0x7
    shift = ((-i)&7)*8+(8-i%8)*(i>8)
    mask = 255&((-256)>>(8-abs(8-i)))
    return ((rot45aclk(x) >> shift) | mask)&255

def pos_in_adiag(sq):
    return min(sq%8,7-(sq//8))

def adiag_posmap(pos, sq):
    i = (sq%8+sq//8)^0x7
    shift = ((-i)&7)*8+(8-i%8)*(i>8)
    sq = shift+pos
    return (sq + 8*((sq&7)^7)) & 63

import array
# Reach for sliding pieces, given occupancy bitboard
reach = []
for i in range(8):
    l = array.array('B', (0,)*256)
    for j in range(256):
        l[j] = 1<<i
        if i<7:
            m = 1<<(i+1)
            while m&255 and not m&j:
                l[j] |= m
                m <<= 1
        if i>0:
            m = 1<<(i-1)
            while m&255 and not m&j:
                l[j] |= m
                m >>= 1
    reach.append(l)

# ray between two squares in a rank
ray = []
for i in range(8):
    l = array.array('B', (0,)*8)
    for j in range(8):
        if i!=j:
            m = 1<<((j if j<i else i)+1)
            t = 1<<(j if i<j else i)
            while m&255 and not m&t:
                l[j] |= m
                m <<= 1
    ray.append(l)

def knight_attacks(sq):
    r = sq//8
    a = 1<<sq
    x  = rank_mask(r+2)&(a<<17|a<<15)
    x |= rank_mask(r+1)&(a<<10|a<<6)
    x |= rank_mask(r-1)&(a>>10|a>>6)
    x |= rank_mask(r-2)&(a>>17|a>>15)
    return x

def king_attacks(sq):
    r = sq//8
    a = 1<<sq
    x  = rank_mask(r+1)&(a<<7|a<<8|a<<9)
    x |= rank_mask(r)  &(a<<1|a>>1)
    x |= rank_mask(r-1)&(a>>7|a>>8|a>>9)
    return x

def pawn_attacks(sq, side):
    r = sq//8
    a = 1<<sq
    if side:
        x = rank_mask(r-1)&(a>>7|a>>8|a>>9)
        x |= (r==3)*(a>>16)
    else:
        x = rank_mask(r+1)&(a<<7|a<<8|a<<9)
        x |= (r==4)*(a<<16)
    return x

def find_attacker_slider(dest_list, occ_bb, piece_bb, target_bb, pos,
                             pos_map, domain_trans, pos_inv_map):
    r = reach[pos_map(pos)][domain_trans(target_bb, pos)]
    m = r & domain_trans(piece_bb, pos)
    while m:
        r = m&-m
        rpos = r.bit_length()-1
        if not (ray[rpos][pos_map(pos)] & domain_trans(occ_bb, pos)):
            dest_list.append(pos_inv_map(rpos, pos))
        m ^= r

def find_attacker_jumper(dest_list, piece_bb, pos, jumper_attacks):
    m = piece_bb & jumper_attacks(pos)
    while m:
        r = m&-m
        rpos = r.bit_length()-1
        dest_list.append(rpos)
        m ^= r

def find_attacker_pawn(dest_list, occ_bb, piece_bb, pos, side):
    m = piece_bb & pawn_attacks(pos, side)
    while m:
        r = m&-m
        rpos = r.bit_length()-1
        if rpos%8 == pos%8:
            M = rank_mask(pos//8)
            M |= rank_mask(rpos//8+(1 if side else -1))
            if not (M & file_mask(pos%8) & occ_bb):
                dest_list.append(rpos)
        else:
            dest_list.append(rpos)
        m ^= r

def find_attacker(bitboard, piece, pos,
                  attacker_file=None, attacker_rank=None, res=None):
    if res == None:
        res = list()
    for p in piece:
        bbp = bitboard.piece[p]

        if attacker_file != None:
            bbp &= file_mask(attacker_file)
        if attacker_rank !=None:
            bbp &= rank_mask(attacker_rank)

        bbt = bitboard.occ^bbp

        kind = p.lower()

        if kind in 'rq':
            find_attacker_slider(res, bitboard.occ, bbp, bbt, pos,
                                    pos_in_rank, rank, rank_posmap)
            find_attacker_slider(res, bitboard.occ, bbp, bbt, pos,
                                    pos_in_file, file, file_posmap)
        if kind in 'bq':
            find_attacker_slider(res, bitboard.occ, bbp, bbt, pos,
                                    pos_in_mdiag, mdiag, mdiag_posmap)
            find_attacker_slider(res, bitboard.occ, bbp, bbt, pos,
                                    pos_in_adiag, adiag, adiag_posmap)
        elif kind == 'n':
            find_attacker_jumper(res, bbp, pos, knight_attacks)
        elif kind == 'k':
            find_attacker_jumper(res, bbp, pos, king_attacks)
        elif kind == 'p':
            find_attacker_pawn(res, bitboard.occ, bbp, pos, p.isupper())

    if len(res) == 1:
        return res[0]
    else:
        return None

def make(txt, sq_from, sq_to):
    a = txt[0:sq_from] + '-' + txt[sq_from+1::]
    return a[0:sq_to] + txt[sq_from] + a[sq_to+1::]

def put(txt, sq, piece):
    return txt[0:sq] + piece + txt[sq+1::]

_DIGIT_RULE = re.compile('^(.*)(\d)(.*)$')
_ES_RULE = re.compile('^([^-]*)(-+)(.*)$')

class GameState(str):
    cmove = move = 'none'
    names = ['', '']
    game_number = relation = itime = iinc = time = wtime = btime = 0
    halfmove = -1
    turn = True
    castling = 0b1111
    enpassant = -1
    prev = None
    comment = None

    # Castling Mask         Turn short?
    _CM = (( 0b0001 ,     # 0    0
             0b0010 ),    # 0    1
           ( 0b0100 ,     # 1    0
             0b1000 ))    # 1    1
    # Castling attacker range
    _CAR = (( (58,61),    # 0    0
              (60,63) ),  # 0    1
            ( (2,5),      # 1    0
              (4,7)  ))   # 1    1
    # Castling path range
    _CPR = (( (57,60),    # 0    0
              (61,63) ),  # 0    1
            ( (1,4),      # 1    0
              (5,7)  ))   # 1    1
    # Castling piece squares
    _CPS = ((((56, 59), (60, 58)),
             ((63, 61), (60, 62))),
            (((0, 3), (4, 2)),
             ((7, 5), (4, 6))))

    # piece values:
    _PV = {'q':9, 'r':5, 'b':3, 'n':3, 'p':1 , '-':0, 'k':0}

    def __new__(cls,
     value='RNBQKBNRPPPPPPPP--------------------------------pppppppprnbqkbnr'):
        fen = False
        if isinstance(value, GameState):
            return value.copy()
        elif '/' in value.split()[0]:
            fen = value.split()
            board = fen[0].split('/')
            for i in range(8):
                m = _DIGIT_RULE.match(board[i])
                while m:
                    board[i] = m.group(1) + int(m.group(2))*'-' + m.group(3)
                    m = _DIGIT_RULE.match(board[i])
            value = ''.join(board[::-1])
        ver = next((x for x in value if x not in 'RNBQKPrnbqkp-'), False)
        if not (len(value) != 64 or ver):
            self = super(GameState, cls).__new__(cls, value)
        else:
            self = super(GameState, cls).__new__(cls, 64*'-')
        self.strength = [0,0]
        self.figures = list()
        for i, x in enumerate(self):
            self.strength[x.isupper()] += self._PV[x.lower()]
            if x is not '-':
                self.figures.append(((i%8,i//8), x))
        self.next = list()
        if fen:
            self.turn = fen[1] == 'w'
            self.castling = 0
            for i, l in enumerate('qkQK'):
                self.castling += (l in fen[2])*(1<<i)
            self.enpassant = -1 if fen[3] == '-' else ord(fen[3][0])-97
            self.halfmove = (int(fen[5])-1)*2 + (not self.turn) -1
        return self

    def copy(self):
        s = GameState(str(self))
        for pn in ['game_number', 'turn', 'names', 'relation', 'itime', 'iinc',
                   'wtime', 'btime', 'halfmove', 'cmove', 'move', 'castling']:
            setattr(s, pn, getattr(self, pn))
        return s

    def piece_in(self, pos):
        if isinstance(pos, tuple):
            square = self[pos[1]*8+pos[0]]
        else:
            square = self[pos]
        return square if square != '-' else False

    def empty_range(self, r):
        return not bool(next((self[x] for x in r if self[x] != '-'), False))

    def __sub__(self, y):
        return [ i for i in range(64) if self[i] != y[i] ]

    def __eq__(self, y):
        if not y:
            return False
        else:
            return (super().__eq__(y) and self.halfmove == y.halfmove and
                    self.cmove == y.cmove)

    def make_cleanup(self, txt, cmove, move):
        s = GameState(txt)
        s.game_number = self.game_number
        s.turn        = not self.turn
        s.names       = self.names
        s.relation    = self.relation
        s.itime       = self.itime
        s.iinc        = self.iinc
        s.wtime       = self.wtime
        s.btime       = self.btime
        s.halfmove    = self.halfmove + 1
        s.cmove       = cmove
        s.move        = move
        s.prev        = self
        self.next.append(s) # <-- it is done by history.update
        # Block castling
        if 'O-O' in move:
            s.castling = (self.castling &
                    ~(self._CM[self.turn][0]|self._CM[self.turn][1]))
        elif cmove[0] == 'R' and (cmove[1:3] in ['a1', 'a8']):
            s.castling = (self.castling & ~self._CM[self.turn][0])
        elif cmove[0] == 'R' and (cmove[1:3] in ['h1', 'h8']):
            s.castling = (self.castling & ~self._CM[self.turn][1])
        else:
            s.castling = self.castling
        # en passant
        if (cmove[0] == 'P' and
                int(cmove[3]) == (2 if self.turn else 7)  and
                int(cmove[6]) == (4 if self.turn else 5)):
            s.enpassant = ord(cmove[2])-97
        else:
            s.enpassant = -1
        s.time = time()
        return s

    def make(self, move):
        if isinstance(move, list):
            m = CoordsMove(self, move)
        else:
            m = San(move)

        bb = BB(self)

        # Castling
        if m.castling_short or m.castling_long:
            L = []
            for s in range(*self._CAR[self.turn][bool(m.castling_short)]):
                find_attacker(bb, 'prnbqk' if self.turn else 'PRNBQK', s, res=L)
            if ((self._CM[self.turn][bool(m.castling_short)] & self.castling)
                and self.empty_range(range(
                           *self._CPR[self.turn][bool(m.castling_short)])) and
                    len(L) == 0):
                moves = self._CPS[self.turn][bool(m.castling_short)]
                a = make(self, *moves[0])
                b = make(a, *moves[1])
                return self.make_cleanup(b,
                        'o-o' if m.castling_short else 'o-o-o',
                        'O-O' if m.castling_short else 'O-O-O')
            else:
                return False

        piece = m.piece.upper() if self.turn else m.piece.lower()
        sq_to = pos2pos(m.sq_to)
        attacker_file = ord(m.file_from)-97 if m.file_from else None
        attacker_rank = int(m.rank_from)-1  if m.rank_from else None

        sq_from = find_attacker(bb, piece, sq_to, attacker_file, attacker_rank)

        # Attacker not found or attacking my self
        if (not isinstance(sq_from, int) or not (self.turn == self[sq_from].isupper()) or
                (self[sq_to] != '-' and (self.turn == self[sq_to].isupper()))):
            return False

        # En passant
        if m.piece == 'P' and abs((sq_from%8)-(sq_to%8)) == 1 and self[sq_to] == '-':
            if sq_to%8==self.enpassant and sq_to//8==(5 if self.turn else 2):
                a = put(self, sq_to + (-8 if self.turn else 8), '-')
                b = make(a, sq_from, sq_to)
                return self.make_cleanup(b,
                        m.piece+'/'+postopos(sq_from)+'-'+postopos(sq_to),
                        m)
            else:
                # no se puede en passant
                return False

        b = make(self, sq_from, sq_to)

        # Promotion
        if m.piece == 'P' and sq_to//8 in [0,7]:
            if m.promotion:
                b = put(b, sq_to,
                     m.promotion.upper() if self.turn else m.promotion.lower())
            else:
                b = put(b, sq_to, 'Q' if self.turn else 'q')
                m.promotion = 'Q'

        # check for checks
        L = []
        find_attacker(BB(b), 'prnbqk' if self.turn else 'PRNBQK',
                      b.index('K' if self.turn else 'k'), res=L)

        if len(L):
            return False
        else:
            cmove = m.piece+'/'+postopos(sq_from)+'-'+postopos(sq_to)+(
                    ('='+m.promotion) if m.promotion else '')
            return self.make_cleanup(b, cmove, m)

    def fen(self):
        fen = list()
        board = list()
        for i in range(8):
            board.append(self[8*i:8*i+8])
            m = _ES_RULE.match(board[i])
            while m:
                board[i] = m.group(1) + str(len(m.group(2))) + m.group(3)
                m = _ES_RULE.match(board[i])
        fen.append('/'.join(board[::-1]))
        fen.append('w' if self.turn else 'b')
        castling = ''
        for i, l in enumerate('qkQK'):
            castling = bool((1<<i)&self.castling)*l + castling
        fen.append(castling)
        if self.enpassant > 0:
            fen.append(chr(97+self.enpassant) + ('6' if self.turn else '3'))
        else:
            fen.append('-')
        fen.append('-')
        fen.append(str((self.halfmove if self.halfmove > 0 else 0)//2+1))
        return ' '.join(fen)

class Style12(GameState):
    def __new__(cls, value):
        svalue = value.split()
        self = super(Style12, cls).__new__(cls, ''.join(svalue[8:0:-1]))
        self.turn = svalue[9] == 'W'
        self.halfmove  = (int(svalue[26])-1)*2 + (not self.turn) - 1
        self.cmove = svalue[27]
        self.move = svalue[29]
        self.castling = int(''.join(svalue[11:15]),2)
        self.enpassant = int(svalue[10])
        self.wtime = int(svalue[24])
        self.btime = int(svalue[25])
        self.time = time()
        # not really neded
        self.style12 = value
        self.game_number = int(svalue[16])
        self.names = svalue[17:19][::-1]
        self.relation = int(svalue[19])
        self.itime = svalue[20]
        self.iinc  = svalue[21]
        return self

def contiguous(src, dst):
    if dst.halfmove-src.halfmove != 1 or dst.cmove == 'none':
        return False
    D = set(dst - src)
    # Canstling
    if dst.cmove == 'o-o':
        x = 0 if src.turn else 56
        if (D == {4+x, 5+x, 6+x, 7+x} and
                src.piece_in(4+x).lower() == 'k' and
                src.piece_in(7+x).lower() == 'r'):
            return True
        else:
            return False
    if dst.cmove == 'o-o-o':
        x = 0 if src.turn else 56
        if (D == {0+x, 2+x, 3+x, 4+x} and
                src.piece_in(4+x).lower() == 'k' and
                src.piece_in(0+x).lower() == 'r'):
            return True
        else:
            return False
    p, m = dst.cmove.split('/')
    s, d = m.split('-')
    s = pos2pos(s)
    d = pos2pos(d)
    DD = {s,d}^D
    # En passant
    if len(DD) == 1:
        dp = DD.pop()
        if (p.lower() == 'p' and
                dp//8 == (4 if src.turn else 3) and
                src.piece_in(s).lower() == 'p' and
                src.piece_in(dp).lower() == 'p' and
                not src.piece_in(d)):
            return True
        else:
            return False
    # promotion
    if ('=' in dst.cmove and src.piece_in(s).lower() == 'p' and
            dst.piece_in(d).lower() == dst.cmove.split('=')[1].lower()):
        return True
    if (len(DD) or src.piece_in(s).lower() != p.lower()):
        return False
    else:
        return True

class StateDirectory(dict):
    def __missing__(self, key):
        self[key] = list()
        return self[key]

    def back_sorted(self):
        for i in sorted(self.keys(), reverse=True):
            for x in self[i]:
                yield x

def rewind(state):
    while state.prev:
        state = state.prev
    return state

class GameHistory(list):
    def __new__(cls, value=None):
        self = super(GameHistory, cls).__new__(cls, value)
        self._directory = StateDirectory()
        self._not_connected = list()
        if isinstance(value, list):
            for x in value:
                self._directory[x.halfmove].append(x)
        return self

    def extend(self, l):
        for x in l:
            self.update_reg(x)
        super().extend(l) 

    def append(self, x):
        self.update_reg(x)
        super().append(x) 

    def insert(self, idx, x):
        self.update_reg(x)
        super().insert(idx, x)

    def update_reg(self, state):
        s = next((x for x in self._directory[state.halfmove] if state == x), None)
        while s:
            self._directory[state.halfmove].remove(s)
            s = next((x for x in self._directory[state.halfmove] if state == x), None)
        self._directory[state.halfmove].append(state)

    def remove_move(self, x):
        y = x.prev
        if y:
            y.next.remove(x)
            x.prev = None
        else:
            return
        L = list()
        while x:
            self._directory[x.halfmove].remove(x)
            L.extend(x.next)
            x.next.clear()
            x.prev = None
            x = L.pop() if L else None
        return self.set_mainline(y)

    def remove_variation(self, x):
        while x.prev and len(x.prev.next)<2:
            x = x.prev
        return self.remove_move(x)

    def set_main_variation(self, x):
        y = x
        while x.prev:
            l = x.prev.next
            l.insert(0, l.pop(l.index(x)))
            x = x.prev
        return self.set_mainline(y)

    def remove_variations(self):
        x = self.parent_node
        while x:
            for y in x.next[1::]:
                self.remove_move(y)
            x = x.next[0] if x.next else None

    def update(self, state):
        # is there an identical state we would want to replace?
        s = next((x for x in self._directory[state.halfmove] if state == x), None)
        if s:
            state.next = list(s.next)
            for x in s.next:
                x.prev = state
            if s.prev:
                state.prev = s.prev
                idx = s.prev.next.index(s)
                s.prev.next.remove(s)
                s.prev.next.insert(idx, state)
            self._directory[s.halfmove].remove(s)
            if s in self:
                idx = self.index(s)
                self.remove(s)
                self.insert(idx, state)

        # is the new state contiguous to any existing state?
        s = next((x for x in self._directory[state.halfmove-1]
                        if contiguous(x, state)), None)
        if s and not state.prev:
            s.next.append(state)
            state.prev = s
            if self and s == self[-1]:
                self.append(state)

        if not self or state not in self and state.prev == self[-1]:
            self.append(state)

        # is the any existing state without prev contiguous to the new state?
        s = next((x for x in self._directory[state.halfmove+1]
                        if contiguous(state, x) and x.prev == None), None)
        if s:
            state.next.append(s)
            s.prev = state
            if s in self._not_connected:
                self._not_connected.remove(s)

        if not state.prev:
            self._not_connected.append(state)
            return False
        else:
            return True

    def set_mainline(self, x):
        if x is None:
            return False
        sr = list()
        l = list()
        y = x
        while x and x not in self:
            l.insert(0, x)
            x = x.prev
        if x in self:
            rl = self[self.index(x)+1::]
            for x in rl:
                self.remove(x)
            self.extend(l)
            return (y, l, rl)
        self.clear()
        if x not in self and l:
            self.extend(l)
        else:
            self.append(x)
        return False

    def marked(self):
        if len(self) > 1:
            l = self[-1] - self[-2]
            return l if len(l)<=4 else []
        else:
            return []

    @property
    def parent_node(self):
        return rewind(self[0])

    def go_deeper(self, lines, state, line):
        if not len(state.next):
            lines.append(' '.join(line+['{} {}'.format(state.halfmove,state.move)]))
        else:
            for x in state.next:
                self.go_deeper(lines, x, line+['{} {}'.format(state.halfmove,state.move)])

    def get_lines(self):
        lines = []
        self.go_deeper(lines,rewind(self[0]),[])
        # ncl = []
        # for x in self._not_connected:
            # self.go_deeper(ncl,x,[])
        return lines

