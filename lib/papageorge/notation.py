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

_san_res = [
    re.compile('(?P<cl>O-O-O)|(?P<cs>O-O)'
               '|(?:{}|{}|{}|{}|{}|{})'.format(_ff, _rf, _ft, _rt, _pr, _p)),
    re.compile('(?:(?P<ff>{})?x)'
               '?(?P<ft>{})'
               '(?P<rt>[18])'
               '=(?!K)(?P<pr>{})'.format(_file, _file, _piece) +
               '|(?:{}|{}|{}|{}|)'.format(_cl, _cs, _rf, _p)),
    re.compile('(?:(?P<ff>{})?x)?'
               '(?P<ft>{})'
               '(?![18])(?P<rt>{})'.format(_file, _file, _rank) +
               '|(?:{}|{}|{}|{}|{})'.format(_pr, _cl, _cs, _rf, _p)),
    re.compile('(?P<p>{})'
               '(?P<ff>{})?'
               '(?P<rf>{})?x?'
               '(?P<ft>{})'
               '(?P<rt>{})'.format(_piece, _file, _rank, _file, _rank) +
               '|(?:{}|{}|{})'.format(_pr, _cl, _cs))
]

class San(str):
    def __init__(self, txt):
        self.sq_from = self.sq_to = None
        self.next = []
        self.prev = []
        for r in _san_res:
            m = r.match(txt)
            if m:
                self.piece          = m.group('p') if m.group('p') else 'P'
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

_promotion = 'x?{}[18]=(?!K){}'.format(_file, _piece)
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
                                                   _vstart, _vend, _result))

class Pgn():
    def __new__(cls, path=None, hdr=None, it=None):
        self = object.__new__(cls)
        self.main_line = list()
        self.header = list()
        if hdr:
            self.header.append(hdr)
        hdr_done = False
        last_move = None
        var_stem = list()
        if path:
            with open(path, 'r') as fd:
                it = _pgn_re.finditer(fd.read())
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
            elif m.group('vstart'):
                hdr_done = True
                var_stem.append(last_move)
            elif m.group('vend'):
                hdr_done = True
                last_move = var_stem.pop()
            elif m.group('move'):
                hdr_done = True
                s = San(m.group('move'))
                s.prev = last_move
                if last_move:
                    last_move.next.insert(0,s)
                last_move = s
                if not len(var_stem):
                    self.main_line.append(s)
        return self

def go_deeper(lines, state, line):
    if not len(state.next):
        lines.append(line+[state])
    else:
        for x in state.next:
            go_deeper(lines, x, line+[state])

#path = '/home/e/vari.pgn'
#path = '/home/e/fish.pgn'
#path = '/home/e/sicilian-najdorf.pgn'
#P = Pgn(path)

#for p in P:
    #print()
    #for x in p.header:
        #print('[{} "{}"]'.format(x[0],x[1]))
    #lines = []
    #go_deeper(lines, p.main_line[0], [])
    #for x in lines:
        #print(x)
        #print(len(x))

