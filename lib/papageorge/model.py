
if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

from papageorge.game import Style12

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

def pos2pos(pos):
    return ord(pos[0])-97+((int(pos[1])-1)<<3)

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
    m = piece_bb &  pawn_attacks(pos, side)
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
                  attacker_file=None, attacker_rank=None, res=[]):
    for p in piece:
        bbp = bitboard.piece[p]

        if attacker_file:
            bbp &= file_mask(attacker_file)
        if attacker_rank:
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
    return res


if __name__ == '__main__':
    #S = Style12('<12> rnbqkbnr pppppppp -------- -----p-- -------- -------- PPPPPPPP -NBQKBNR W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 1 none (0:00) none 0 0 0')
    S = Style12('<12> -------- -------- -------- --q---r- -------- -------- ----n--p -------- W -1 1 1 1 1 0 170 GuestXXSW GuestXXSW 2 0 0 39 39 0 0 1 none (0:00) none 0 0 0')
    t = 'g1'

    b = BB(S)
    printBB(b.occ)
    print()
    s = pos2pos(t)

    L = []
    for s in range(4,7):
        find_attacker(b, 'prnbqk', s, res=L)
    #L.append(s)
    printBB(b.occ, mark=L)
    #print()

    #print(knight_attacks(s))


    #for i in range(len(h)-1):
        #print('{} {} {}'.format(i, h[i+1].move, contiguous(h[i], h[i+1])))
    #print('Main line: '+' '.join([x.move for x in h]))
    #print('All lines:')
    #l, c = h.get_lines()
    #print(l)
    #print(c)

