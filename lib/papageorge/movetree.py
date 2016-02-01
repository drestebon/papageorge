# movetree - move sheet for Board

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

from gi.repository import GObject, Gtk, Gdk
from time import time
import threading

if __name__ == '__main__':
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.abspath(os.path.join(here, '../')))

import papageorge.config as config
from papageorge.general import *

class CommentEditor(Gtk.Window):
    def __init__(self, parent, node):
        self.node = node
        self.parent = parent
        title = 'Edit the comment for: {}'.format(node.move)
        Gtk.Window.__init__(self, title=title)
        self.set_border_width(5)
        self.set_modal(True)
        self.set_transient_for(parent.board.win)
        self.set_default_size(300,-1)
        vbox = Gtk.VBox().new(False, 1)
        self.add(vbox)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        vbox.pack_start(scrolledwindow, True, True, 0)

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(node.comment if node.comment else '')
        scrolledwindow.add(self.textview)

        hbox = Gtk.HBox().new(False, 1)
        vbox.pack_start(hbox, False, False, 0)

        button = Gtk.Button.new_with_mnemonic('_OK')
        button.connect("clicked", self.on_ok_clicked)
        hbox.pack_end(button, False, False, 0)
        button = Gtk.Button.new_with_mnemonic('_Cancel')
        button.connect("clicked", self.on_cancel_clicked)
        hbox.pack_end(button, False, False, 0)
        self.show_all()

    def on_cancel_clicked(self, button):
        self.destroy()

    def on_ok_clicked(self, button):
        s, e = self.textbuffer.get_bounds()
        self.node.comment = self.textbuffer.get_text(s,e,False)
        self.parent.fill_row_with_node(self.node)
        self.destroy()

class MoveTree(Gtk.ScrolledWindow):
    def __init__(self, board):
        self.board = board
        self.pool = dict()
        self.model = Gtk.TreeStore(str, str, str, str, str, str,
                                   int, int , int, str)
        view = Gtk.TreeView()
        view.modify_bg(Gtk.StateType.NORMAL,
                Gdk.Color.parse(config.movesheet.bg)[1])
        view.set_model(self.model)
        # 0 1 2 3  4  5  6 7  8  9
        # # W B c# cW cB - wW wB id
        self.column = list()
        for i, n in enumerate(['#', 'W', 'B']):
            col = Gtk.TreeViewColumn(n, Gtk.CellRendererText(),
                    text=i, background=i+3, weight=i+6)
            col.side = i
            col.set_expand(True)
            col.set_alignment(0.5)
            view.append_column(col)
            self.column.append(col)
        view.set_enable_tree_lines(True)
        view.set_has_tooltip(True)
        view.set_activate_on_single_click(True)
        view.connect('row-activated', self.clicked)
        # view.connect('size-allocate', self.treeview_changed)
        view.connect('query-tooltip', self.tooltip)
        view.connect('button-press-event', self.on_click)
        view.set_can_focus(False)
        view.get_selection().set_mode(Gtk.SelectionMode.NONE)
        Gtk.ScrolledWindow.__init__(self)
        self.add(view)
        self.treeview = view
        self.set_can_focus(False)
        self.populate()

    @property
    def parent_node(self):
        return self.board.game._history[0]

    @property
    def curr_line(self):
        return self.board.game._history

    def is_row(self, x):
        return x.halfmove>-1 and (
               (x.halfmove%2 and x.prev and x.prev.next.index(x)) or
               (x.halfmove%2 and not x.prev) or not x.halfmove%2)

    def tooltip(self, widget, x, y, keyboard_mode, tooltip):
        bx, by = widget.convert_widget_to_bin_window_coords(x, y)
        coords = widget.get_path_at_pos(bx, by)
        if coords:
            path, column, cx, cy = coords
        else:
            return False
        col = self.column.index(column)
        it = self.model.get_iter(path)
        nid = int(self.model.get_value(it, 9))
        xx = self.pool[nid][col-1]
        if col and xx and xx.comment:
            tooltip.set_text(xx.comment)
            widget.set_tooltip_cell(tooltip, path, column, None)
            return True
        else:
            return False

    def on_click(self, widget, event):
        if event.button == 3:
            path, column, cx, cy = widget.get_path_at_pos(event.x, event.y)
            it = self.model.get_iter(path)
            nid = int(self.model.get_value(it, 9))
            col = self.column.index(column)
            xx = self.pool[nid][col-1]
            if col and xx:
                menu = Gtk.Menu()
                menu.attach_to_widget(widget, None)
                menu_it = Gtk.MenuItem.new_with_label('Edit comment')
                menu_it.connect('activate', self.edit_comment, xx)
                menu.append(menu_it)
                menu_it = Gtk.MenuItem.new_with_label('Remove comment')
                menu_it.connect('activate', self.remove_comment, xx)
                menu.append(menu_it)
                menu.popup(None, None, None, None, event.button, event.time)
                menu.show_all()
                return True
            else:
                return False
        else:
            return False

    def edit_comment(self, widget, node):
        CommentEditor(self, node)

    def remove_comment(self, widget, node):
        node.comment = None
        self.fill_row_with_node(node)

    def clicked(self, tv, path, column):
        if column.side:
            it = self.model.get_iter(path)
            nid = int(self.model.get_value(it, 9))
            y = x = self.pool[nid][column.side-1]
            if x is None:
                return
            sr = list()
            l = list()
            while x not in self.curr_line and x.prev:
                l.insert(0, x)
                if self.is_row(x):
                    self.set_color_curr_line(x)
                    sr.append(x)
                    if x.halfmove%2 and x.prev:
                        self.set_color_curr_line(x.prev, True)
                        sr.append(x.prev)
                        cl = self.child_list(x.prev)
                        if len(cl):
                            for i in cl[0:cl.index(x)]:
                                self.set_color_curr_line(i, True)
                                sr.append(i)
                x = x.prev
            rl = self.curr_line[self.curr_line.index(x)+1::]
            for x in rl:
                if x not in sr and self.is_row(x):
                    self.set_color_black(x)
                self.curr_line.remove(x)
            if (self.board.game.kind & KIND_EXAMINING and
                not self.board.game.kind & KIND_OBSERVING and len(rl)):
                config.cli.send_cmd("backward {}".format(len(rl)),
                                    wait_for='Game {}: {} backs up {}'.format(
                                    self.board.game.number,
                                    config.fics_user,len(rl)))
            x = self.curr_line[-1]
            if x not in sr:
                if self.is_row(x):
                    self.set_color_curr_line(x)
                elif x.prev:
                    self.set_color_curr_line(x.prev)
            if (self.board.game.kind & KIND_EXAMINING and
                    not self.board.game.kind & KIND_OBSERVING):
                config.cli.send_moves(l)
            else:
                self.curr_line.extend(l)
                self.set_color_curr_move(self.curr_line[-1])
                self.board.redraw()
            #for x in self.curr_line:
                #print(x)

    def set_color_curr_move(self, x):
        if not x.halfmove%2 or x.halfmove%2 and (
                x.prev and x.prev.next.index(x) or not x.prev):
            path = self.node_path(x)
        else:
            path = self.node_path(x.prev)
        row = self.model.get_iter(Gtk.TreePath(path))
        self.model.set_value(row, 3, config.movesheet.curr_move_n)
        self.model.set_value(row, 4, config.movesheet.curr_line
                              if x.halfmove %2 else config.movesheet.curr_move)
        self.model.set_value(row, 5, config.movesheet.curr_move
                              if x.halfmove %2 else config.movesheet.off)

    def set_color_curr_line(self, x, only_white = False):
        path = self.node_path(x)
        row = self.model.get_iter(Gtk.TreePath(path))
        self.model.set_value(row, 3, config.movesheet.curr_line_n)
        self.model.set_value(row, 4, config.movesheet.curr_line)
        self.model.set_value(row, 5, config.movesheet.off
                                 if only_white else config.movesheet.curr_line)

    def set_color_black(self, x):
        path = self.node_path(x)
        row = self.model.get_iter(Gtk.TreePath(path))
        self.model.set_value(row, 3, config.movesheet.off_n)
        self.model.set_value(row, 4, config.movesheet.off)
        self.model.set_value(row, 5, config.movesheet.off)

    # def treeview_changed(self, widget, event, data=None):
        # x = self.curr_line[-1]
        # column = self.treeview.get_column((x.halfmove % 2)+1)
        # path = self.node_path(x)
        # if path and path[0] > -1:
            # path = Gtk.TreePath()
            # self.treeview.set_cursor(path, column, False)

    def child_list(self, node):
        x = node
        y = None
        if x.halfmove < 0:
            return list(x.next)
        if x.halfmove == 0 and x.prev and len(x.prev.next):
            return x.prev.next[x.prev.next.index(x)+1::]
        if x.halfmove % 2:
            if x.prev:
                y = x
                x = x.prev
            else:
                return list()
        l = list()
        if x.prev:
            for z in x.prev.next:
                l.append(z)
                l.extend(z.next[1::])
        else:
            l = x.next[1::]
        if y in l:
            l = l[l.index(y)+1::]
        if x in l:
            l = l[l.index(x)+1::]
        return l

    def next_node(self, node):
        y = x = node
        while x.halfmove//2 == y.halfmove//2:
            if len(x.next):
                x = x.next[0]
            else:
                return None
        return x

    def prev_node(self, node):
        y = x = node
        while x.halfmove//2 == y.halfmove//2 or not self.is_row(x):
            if x.prev:
                x = x.prev
            else:
                return None
        if x is self.parent_node:
            return None
        else:
            return x

    def repopulate(self):
        self.model.clear()
        self.populate()

    def populate(self, x=None):
        if x == None:
            x = self.parent_node
        if x.halfmove < 0:
            if len(x.next):
                x = x.next[0]
            else:
                return
        l = self.child_list(x)
        L = list()
        p = self.node_path(x) #[0]
        while x:
            if len(p)>1:
                parent = self.model.get_iter(Gtk.TreePath(p[0:-1]))
            else:
                parent = None
            self.fill_row(self.model.append(parent), x)
            if (l and x not in l) or not l:
                l = self.child_list(x)
            elif x in l:
                l.remove(x)
            nx = self.next_node(x)
            if l:
                L.append(nx)
                p.append(0)
                x = l[0]
            elif nx:
                x = nx
                p[-1] += 1
            elif L:
                x = L.pop()
                p.pop()
                while L and not x:
                    x = L.pop()
                    p.pop()
                p[-1] += 1
            else:
                return
        x = self.curr_line[-1]
        column = self.treeview.get_column((x.halfmove % 2)+1)
        path = Gtk.TreePath(self.node_path(x))
        self.treeview.set_cursor(path, column, False)

    def node_path(self, node):
        y = x = node
        if x is not None:
            y = x
            l = []
            while x and x.prev:
                z = x
                x = x.prev
                if x.next.index(z):
                    l.append(y.halfmove//2-x.next[0].halfmove//2)
                    d = self.child_list(x.next[0]).index(z)
                    l.extend(d*[0])
                    y = x.next[0]
            l.append(y.halfmove//2-x.halfmove//2 - (1 if x.halfmove<0 else 0))
            path = l[::-1]
            return path
        else:
            return None

    def node_parent(self, x):
        while x and x.prev:
            z = x
            x = x.prev
            if x.next.index(z):
                l = self.child_list(x.next[0])
                i = l.index(z)
                if i:
                    return l[i-1]
                elif x.halfmove % 2:
                    return x.next[0]
                else:
                    return x
        return None
        # if x is self.parent_node:
            # return None

    def fill_row(self, row, x, set_black = False):
        if not set_black:
            self.model.set_value(row, 0, str(1+x.halfmove//2)+'.')
            self.model.set_value(row, 1, '...' if x.halfmove%2 else x.move)
        self.model.set_value(row, 2, x.move if x.halfmove%2 else x.next[0].move
                                        if len(x.next) else '')

        w = x.prev if x.halfmove%2 else x
        b = (x if x.halfmove%2 else x.next[0] if len(x.next) else None)

        self.model.set_value(row, 3,
           config.movesheet.curr_move_n
                 if (w == self.curr_line[-1] or b == self.curr_line[-1]) else
           config.movesheet.curr_line_n
                 if (w in self.curr_line or b in self.curr_line) else
                                                       config.movesheet.off_n)

        self.model.set_value(row, 4,
                config.movesheet.curr_move
                    if w == self.curr_line[-1] else
                config.movesheet.curr_line
                    if w in self.curr_line else config.movesheet.off)
        self.model.set_value(row, 5,
                config.movesheet.curr_move
                    if b == self.curr_line[-1] else
                config.movesheet.curr_line
                    if b in self.curr_line else config.movesheet.off)

        self.model.set_value(row, 6, 100)
        self.model.set_value(row, 7, 1000 if w and w.comment else 400)
        self.model.set_value(row, 8, 1000 if b and b.comment else 400)
        
        nid = id(w) if w else id(b)
        self.model.set_value(row, 9, str(nid))
        self.pool[nid] = (w, b)

    def fill_row_with_node(self, node):
        path = self.node_path(node)
        self.fill_row(self.model.get_iter(Gtk.TreePath(path)), node)

    def fill_colors(self, x):
        if not x or (x and not self.is_row(x)):
            return
        path = Gtk.TreePath(self.node_path(x))
        row = self.model.get_iter(path)
        w = x.prev if x.halfmove%2 else x
        b = (x if x.halfmove%2 else x.next[0] if len(x.next) else None)
        self.model.set_value(row, 3,
            config.movesheet.curr_move_n
                if (w == self.curr_line[-1] or b == self.curr_line[-1]) else
            config.movesheet.curr_line_n
                  if (w in self.curr_line or b in self.curr_line) else
           config.movesheet.off_n)
        self.model.set_value(row, 4,
                config.movesheet.curr_move
                    if w == self.curr_line[-1] else
                config.movesheet.curr_line
                    if w in self.curr_line else config.movesheet.off)
        self.model.set_value(row, 5,
                config.movesheet.curr_move
                    if b == self.curr_line[-1] else
                config.movesheet.curr_line
                    if b in self.curr_line else config.movesheet.off)
        return path

    def recolor(self, x):
        node = x if self.is_row(x) else x.prev
        path = self.fill_colors(node)
        self.treeview.expand_to_path(path)
        column = self.treeview.get_column((x.halfmove % 2)+1)
        self.treeview.set_cursor(path, column, False)
        self.fill_colors(self.prev_node(node))
        self.fill_colors(self.next_node(node))

    def new_node(self, x):
        if x.halfmove < 0:
            return None
        p = self.node_parent(x)
        l = self.child_list(x)
        if x.halfmove % 2 and x.prev and not x.prev.next.index(x):
            path = self.node_path(x.prev)
            row = self.model.get_iter(Gtk.TreePath(path))
            self.fill_row(row, x, True)
            if x == self.curr_line[-1]:
                aha = self.model.iter_previous(row)
                if aha:
                    self.model.set_value(aha, 3, config.movesheet.curr_line_n)
                    self.model.set_value(aha, 4, config.movesheet.curr_line)
                    self.model.set_value(aha, 5, config.movesheet.curr_line)
                aha = self.model.iter_next(row)
                if aha:
                    self.model.set_value(aha, 3, config.movesheet.off_n)
                    self.model.set_value(aha, 4, config.movesheet.off)
                    self.model.set_value(aha, 5, config.movesheet.off)
        else:
            if len(l):
                path = self.node_path(p)
                self.model.remove(self.model.get_iter(Gtk.TreePath(path)))
                pp = self.node_parent(p)
                nn = self.next_node(p)
                self.fill_row(self.model.insert_before(pp, nn), p)
                self.populate(self.child_list(p)[0])
            else:
                path = self.node_path(x)
                if len(path) > 1:
                    parent = self.model.get_iter(Gtk.TreePath(path[0:-1]))
                else:
                    parent = None
                if self.model.iter_n_children(parent) > path[-1]:
                    row = self.model.get_iter(Gtk.TreePath(path))
                    nid = int(self.model.get_value(row, 9))
                    w, b = self.pool[nid]
                    w = w if w else b
                    if x.halfmove//2 == w.halfmove//2:
                        self.fill_row(row, x)
                        if x == self.curr_line[-1]:
                            aha = self.model.iter_previous(row)
                            if aha:
                                self.model.set_value(aha, 3, config.movesheet.curr_line_n)
                                self.model.set_value(aha, 4, config.movesheet.curr_line)
                                self.model.set_value(aha, 5, config.movesheet.curr_line)
                            aha = self.model.iter_next(row)
                            if aha:
                                self.model.set_value(aha, 3, config.movesheet.off_n)
                                self.model.set_value(aha, 4, config.movesheet.off)
                                self.model.set_value(aha, 5, config.movesheet.off)
                    elif x.halfmove//2 < w.halfmove//2:
                        if x == self.curr_line[-1]:
                            self.model.set_value(row, 3, config.movesheet.off_n)
                            self.model.set_value(row, 4, config.movesheet.off)
                            self.model.set_value(row, 5, config.movesheet.off)
                        self.fill_row(self.model.insert_before(parent,row),x)
                    else: 
                        if x == self.curr_line[-1]:
                            self.model.set_value(row, 3, config.movesheet.curr_line_n)
                            self.model.set_value(row, 4, config.movesheet.curr_line)
                            self.model.set_value(row, 5, config.movesheet.curr_line)
                        self.fill_row(self.model.insert_after(parent,row),x)
                else:
                    row = self.model.append(parent)
                    self.fill_row(row, x)
                    if x == self.curr_line[-1]:
                        aha = self.model.iter_previous(row)
                        if aha:
                            self.model.set_value(aha, 3, config.movesheet.curr_line_n)
                            self.model.set_value(aha, 4, config.movesheet.curr_line)
                            self.model.set_value(aha, 5, config.movesheet.curr_line)
            if x == self.curr_line[-1]:
                path = Gtk.TreePath(path)
                self.treeview.expand_to_path(path)
                column = self.treeview.get_column((x.halfmove % 2)+1)
                self.treeview.set_cursor(path, column, False)

class TestCli:
    def __init__(self):
        foo = 'caca'
    def key_from_gui(self, keyval):
        print("cli.key_from_gui(): {}".format(keyval))
    def send_cmd(self, txt, echo=False, save_history=False, wait_for=None, ans_buff=None):
        print("cli.send_cmd(): " + txt)
    def print(self, txt, attr=None):
        print("cli.print(): " + txt)
    def redraw(self):
        print('cli.redraw()')

class TestGui:
    def __init__(self):
        foo = 'caca'
        self.games = []
    def new_seek_graph(self, initial_state=None):
        return True
    def seek_graph_destroy(self):
        return True
    def game_destroy(self, game):
        Gtk.main_quit()

if __name__ == '__main__':

    config.cli = TestCli()
    config.gui = TestGui()

    from papageorge.game import Game
    from papageorge.pgn import Pgn

    data = ['<12> r--q-rk- pp---pp- --np---p ----pb-Q -PBbN--- P--P---- --P--PPP -RB--RK- B -1 0 0 0 0 3 118 estebon mrose 2 5 10 35 35 294 57 15 Q/d1-h5 (0:28) Qh5 0 0 0',
            '<12> r--q-rk- pp---pp- --np---p ----pb-- -PBbN--- P--P---- --P--PPP -RBQ-RK- W -1 0 0 0 0 2 118 estebon mrose 2 5 10 35 35 312 106 15 B/c8-f5 (0:21) Bf5 0 0 0',
            '<12> r-bq-rk- pp---pp- --np---p ----p--- -PBbN--- P--P---- --P--PPP -RBQ-RK- B -1 0 0 0 0 1 118 estebon mrose 2 5 10 35 35 312 117 14 N/g5-e4 (0:15) Ne4 0 0 0',
            '<12> r-bq-rk- pp---pp- --np---p ----p-N- -PBb---- P--P---- --P--PPP -RBQ-RK- W -1 0 0 0 0 0 118 estebon mrose 2 5 10 35 35 317 117 14 P/h7-h6 (0:33) h6 0 0 0',
            '<12> r-bq-rk- pp---ppp --np---- ----p-N- -PBb---- P--P---- --P--PPP -RBQ-RK- B -1 0 0 0 0 1 118 estebon mrose 2 5 10 35 35 317 140 13 N/f3-g5 (0:13) Ng5 0 0 0']

    class TestBoard:
        def __init__(self):
            self.game = Game(data[0])

            # self.game = Game()
            # self.game.setup_from_pgn(Pgn(path='/home/e/blah.pgn'))

            self.game.set_board(self)
            self.movetree = None

        def set_movetree(self, mt):
            self.movetree = mt

        def redraw(self):
            print('TestBoard.redraw()')

        def reset(self, arg):
            print('TestBoard.reset()')

    b  = TestBoard()
    mt = MoveTree(b)
    b.set_movetree(mt)

    for x in data[1::]+data[1::][::-1]:
        b.game.set_state(x)

    w = Gtk.Window()
    w.add(mt)
    w.show_all()
    w.connect('delete-event', Gtk.main_quit)
    Gtk.main()


