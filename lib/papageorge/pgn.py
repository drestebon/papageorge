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
from papageorge.model import GameState, GameHistory
from papageorge.notation import San
import re

_check = '[+#]'
_rank  = '[1-8]'
_file  = '[a-h]'
_piece = '[KNBQR]'

_promotion = '{}?x?{}[18]=(?!K){}'.format(_file, _file, _piece)
_pawnmove  = '(?:{}?x)?{}(?![18]){}'.format(_file, _file, _rank)
_stdmove   = '{}{}?{}?x?{}{}'.format(_piece, _file, _rank, _file, _rank)
_castling  = 'O-O(?:-O)?'
_handle    = '[a-z]{3,}'
_san = '(?P<move>(?:{}|{}|{}|{}){}?)'.format(_promotion, _castling,
                                            _pawnmove, _stdmove, _check)
_comment = '{(?P<comment>.+?)}'
_header = '\[(?P<hdr_name>\w+)\s+"(?P<hdr>.+?)"\]'
_vstart = '(?P<vstart>\()'
_vend   = '(?P<vend>\))'
_result = '(?P<result>(?:1/2|[01])-(?:1/2|[01]))'

_pgn_re = re.compile('(?:{}|{}|{}|{}|{}|{})'.format(_header, _comment, _san,
                         _vstart, _vend, _result), re.DOTALL)

class Pgn():
    def __new__(cls, txt=None, path=None, hdr=None, it=None, ic=None):
        self = object.__new__(cls)
        if ic:
            last_move = GameState(ic)
        else:
            last_move = GameState()
        self.main_line = GameHistory([last_move])
        self.header = list()
        if hdr:
            self.header.append(hdr)
        hdr_done = False
        var_stem = list()
        if path:
            with open(path, 'r') as fd:
                it = _pgn_re.finditer(fd.read())
        elif txt:
            it = _pgn_re.finditer(txt)
        for m in it:
            if m.group('hdr_name'):
                if hdr_done:
                    self = [self]
                    tail  = Pgn(hdr=(m.group('hdr_name'), m.group('hdr')),
                                it=it)
                    if isinstance(tail, list):
                        self.extend(tail)
                    else:
                        self.append(tail)
                    break
                else:
                    self.header.append((m.group('hdr_name'),m.group('hdr')))
                    if m.group('hdr_name').lower() == 'fen':
                        last_move = GameState(m.group('hdr'))
                        self.main_line = GameHistory([last_move])
            elif m.group('vstart'):
                hdr_done = True
                var_stem.append(last_move)
                last_move = last_move.prev
            elif m.group('vend'):
                hdr_done = True
                last_move = var_stem.pop()
            elif m.group('move'):
                hdr_done = True
                s = last_move.make(San(m.group('move')))
                # print(m.group('move'), end=' -> ')
                # print(s)
                if not s:
                    config.cli.print('There was an error processing: {}'.format(m.group('move')))
                    w = next((y[1] for y in self.header if y[0].lower() == 'white'), '')
                    b = next((y[1] for y in self.header if y[0].lower() == 'black'), '')
                    config.cli.print('{} v/s {}'.format(w, b))
                    break
                # last_move.next.append(s)
                last_move = s
                if not len(var_stem):
                    self.main_line.append(s)
                else:
                    self.main_line.update_reg(s)
            elif m.group('comment'):
                if last_move.comment:
                    last_move.comment = last_move.comment + ' ' + m.group('comment')
                else:
                    last_move.comment = m.group('comment')

        return self

def go_deeper(lines, state, line):
    if not len(state.next):
        lines.append(line+[state])
    else:
        for x in state.next:
            go_deeper(lines, x, line+[state])

