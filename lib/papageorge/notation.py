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

import re

_check = '[+#]'
_rank  = '[1-8]'
_file  = '[a-h]'
_piece = '[KNBQR]'
_empty = '(?P<{}>(?!.*))'
_p     = _empty.format('p')
_ff    = _empty.format('ff')
_rf    = _empty.format('rf')
_ft    = _empty.format('ft')
_rt    = _empty.format('rt')
_pr    = _empty.format('pr')
_cs    = _empty.format('cs')
_cl    = _empty.format('cl')

class San(str):
    _san_res = [
        # castling
        re.compile('(?P<cl>O-O-O)|(?P<cs>O-O){}?'.format(_check) +
                 '|(?:{}|{}|{}|{}|{}|{})'.format(_ff, _rf, _ft, _rt, _pr, _p)),
        # promotion
        re.compile('(?:(?P<ff>{})?x)'
                   '?(?P<ft>{})'
                   '(?P<rt>[18])'
                   '=(?!K)(?P<pr>{}){}?'.format(_file, _file, _piece,_check) +
                   '|(?:{}|{}|{}|{})'.format(_cl, _cs, _rf, _p)),
        # pawnmove
        re.compile('(?:(?P<ff>{})?x)?'
                   '(?P<ft>{})'
                   '(?P<rt>{}){}?'.format(_file, _file, _rank, _check) +
                   '|(?:{}|{}|{}|{}|{})'.format(_pr, _cl, _cs, _rf, _p)),
        # stdmove
        re.compile('(?P<p>{})'
                   '(?P<ff>{})?'
                   '(?P<rf>{})?x?'
                   '(?P<ft>{})'
                   '(?P<rt>{}){}?'.format(_piece, _file, _rank, _file, _rank, _check) +
                   '|(?:{}|{}|{})'.format(_pr, _cl, _cs))
    ]

    def __init__(self, txt):
        self.sq_from = self.sq_to = None
        self.next = []
        self.prev = None
        if not len(txt):
            return
        for txt_re, r in zip(['castling','promotion','pawnmove','std'],self._san_res):
            m = r.match(txt)
            if m:
                self.piece          = m.group('p') if m.group('p') else 'P'
                if self.piece == 'P' and m.group('ff') == None:
                    self.file_from      = m.group('ft')
                else:
                    self.file_from      = m.group('ff')
                self.rank_from      = m.group('rf')
                self.file_to        = m.group('ft')
                self.rank_to        = m.group('rt')
                self.promotion      = m.group('pr')
                self.castling_short = m.group('cs')
                self.castling_long  = m.group('cl')
                if self.file_from and self.rank_from:
                    self.sq_from = self.file_from + self.rank_from
                if self.file_to and self.rank_to:
                    self.sq_to = self.file_to + self.rank_to
                break

class CoordsMove(str):
    def __new__(cls, mailbox, S):
        ff = chr(97 + S[0][0])
        rf = str(S[0][1]+1)
        ft = chr(97 + S[1][0])
        rt = str(S[1][1]+1)
        p  = mailbox[S[0][1]*8+S[0][0]].upper()
        pt = mailbox[S[1][1]*8+S[1][0]].upper()

        if p == 'K' and ff == 'e' and ft == 'g':
            self = super(CoordsMove, cls).__new__(cls, 'O-O')
            self.castling_short = 'O-O'
            self.piece          = \
            self.file_from      = \
            self.rank_from      = \
            self.file_to        = \
            self.rank_to        = \
            self.sq_from        = \
            self.sq_to          = \
            self.promotion      = \
            self.castling_long  = None
            return self

        elif p == 'K' and ff == 'e' and ft == 'c':
            self = super(CoordsMove, cls).__new__(cls, 'O-O-O')
            self.castling_long  = 'O-O-O'
            self.piece          = \
            self.file_from      = \
            self.rank_from      = \
            self.file_to        = \
            self.rank_to        = \
            self.sq_from        = \
            self.sq_to          = \
            self.promotion      = \
            self.castling_short = None
            return self

        if p == 'P':
            txt = ff+('' if ff == ft else ('x'+ft))+rt
            self = super(CoordsMove, cls).__new__(cls, txt)
        else:
            txt = p+ff+rf+('' if pt == '-' else 'x')+ft+rt 
            self = super(CoordsMove, cls).__new__(cls, txt)

        self.piece          = p
        self.file_from      = ff
        self.rank_from      = rf
        self.file_to        = ft
        self.rank_to        = rt
        self.sq_from        = ff+rf
        self.sq_to          = ft+rt

        self.promotion      = \
        self.castling_short = \
        self.castling_long  = None

        return self

