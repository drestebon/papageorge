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
                                            int, int , int)
        view = Gtk.TreeView()
        view.modify_bg(Gtk.StateType.NORMAL,
                Gdk.Color.parse(config.movesheet.bg)[1])
        view.set_model(self.model)
        # 0 1 2 3  4  5  6 7  8
        # # W B c# cW cB - CW CB 
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
        view.connect('size-allocate', self.treeview_changed)
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
        xx = self.pool[str(path)][col-1]
        if col and xx and xx.comment:
            tooltip.set_text(xx.comment)
            widget.set_tooltip_cell(tooltip, path, column, None)
            return True
        else:
            return False

    def on_click(self, widget, event):
        if event.button == 3:
            path, column, cx, cy = widget.get_path_at_pos(event.x, event.y)
            col = self.column.index(column)
            xx = self.pool[str(path)][col-1]
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
            # pth = str(self.model.get_path(it))+';{}'.format(column.side-1)
            pth = str(self.model.get_path(it)) #+';{}'.format(column.side-1)
            y = x = self.pool[pth][column.side-1]
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

    def treeview_changed(self, widget, event, data=None):
        x = self.curr_line[-1]
        column = self.treeview.get_column((x.halfmove % 2)+1)
        path = self.node_path(x)
        if path and path[0] > -1:
            path = Gtk.TreePath()
            self.treeview.set_cursor(path, column, False)

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
        
        pth = str(self.model.get_path(row))
        self.pool[pth] = (w, b)

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
            self.fill_row(self.model.get_iter(Gtk.TreePath(path)), x, True)
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
                try:
                    node = self.model.get_iter(Gtk.TreePath(path))
                    self.fill_row(node, x)
                except:
                    nn = self.next_node(x)
                    if nn:
                        nn = self.model.get_iter(Gtk.TreePath(
                                                        self.node_path(nn)))
                    self.fill_row(self.model.insert_before(parent, nn), x)
        path = Gtk.TreePath(path)
        if x == self.curr_line[-1]:
            self.treeview.expand_to_path(path)
            column = self.treeview.get_column((x.halfmove % 2)+1)
            self.treeview.set_cursor(path, column, False)
            if p:
                self.fill_colors(p)
            pn = self.prev_node(x)
            if pn:
                self.set_color_curr_line(pn)

