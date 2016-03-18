# board - Board class

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

import papageorge.movetree as movetree        
import papageorge.config as config
from papageorge.general import *
from papageorge.pgn import Pgn

from math import floor, ceil
import gi
from gi.repository import Gtk, GLib, GObject, GdkPixbuf, Gdk, Pango, PangoCairo
import cairo
from time import localtime, strftime
import urwid

class OfferDialog(Gtk.Window):
    def __init__(self, board, txt):
        self.board = board
        Gtk.Window.__init__(self, title="Offer")
        self.set_default_size(1,1)
        self.set_border_width(10)
        self.set_modal(True)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.set_transient_for(board.win)
        Box = Gtk.VBox().new(False, 1)
        txt = '\n'+txt+'\n'
        Box.pack_start(Gtk.Label().new(txt), False, False, 0)
        hbox = Gtk.HBox().new(False, 1)
        Box.pack_start(hbox, False, False, 0)
        button = Gtk.Button.new_with_mnemonic("_Cancel")
        button.connect("clicked", self.on_cancel)
        hbox.pack_end(button, False, False, 0)
        if 'abort' in txt:
            button = Gtk.Button.new_with_mnemonic('_Abort')
            button.command = lambda x: 'abort'
            button.connect("clicked", self.on_button_clicked)
            hbox.pack_end(button, False, False, 0)
        else:
            for label, command in [
                    ('_Decline', lambda x: 'decline'),
                    ('_Accept', lambda x: 'accept')
                    ]:
                button = Gtk.Button.new_with_mnemonic(label)
                button.command = command
                button.connect("clicked", self.on_button_clicked)
                hbox.pack_end(button, False, False, 0)
        self.add(Box)
        self.show_all()

    def on_cancel(self, button):
        self.destroy()

    def on_button_clicked(self, button):
        cmd = button.command(self)
        if cmd:
            config.cli.send_cmd(cmd, echo=True, save_history=False)
        self.destroy()

    def key_cmd(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

class BoardExit(Gtk.Window):
    def __init__(self, board):
        self.board = board
        Gtk.Window.__init__(self, title=board.game.name)
        self.set_default_size(1,1)
        self.set_border_width(10)
        self.set_modal(True)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.set_transient_for(board.win)
        Box = Gtk.VBox().new(False, 1)
        for label, command, close in [
                ('_Abort', lambda x: 'abort', True),
                ('_Draw', lambda x: 'abort', False),
                ('Ad_journ', lambda x: 'adjourn', False),
                ('_Resign', lambda x: 'resign', True),
                ('C_lose', lambda x: False, True),
                ('_Cancel', lambda x: False, False),
                ]:
            button = Gtk.Button.new_with_mnemonic(label)
            button.command = command
            button.close = close
            button.connect("clicked", self.on_button_clicked)
            Box.pack_start(button, False, False, 0)
        self.add(Box)
        self.show_all()

    def on_button_clicked(self, button):
        cmd = button.command(self)
        if cmd:
            config.cli.send_cmd(cmd, echo=True, save_history=False)
        if button.close:
            config.gui.game_destroy(self.board.game)
        self.destroy()

    def key_cmd(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

class PgnGameSelector(Gtk.Window):
    def __init__(self, board, pgn_list):
        Gtk.Window.__init__(self, title="Select a game")
        self.set_default_size(500,200)
        self.set_border_width(10)
        self.set_modal(True)
        self.set_transient_for(board.win)
        self.parent = board
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        Box = Gtk.VBox().new(False, 1)
        self.add(Box)
        self.scrollable_treelist = Gtk.ScrolledWindow()
        Box.pack_start(self.scrollable_treelist, True, True, 0)
        self.scrollable_treelist.set_vexpand(True)
        self.pgn_list = pgn_list
        self.model = Gtk.ListStore(str, str, str)
        for x in pgn_list:
            d = next((y[1] for y in x.header if y[0].lower() == 'date'), '')
            w = next((y[1] for y in x.header if y[0].lower() == 'white'), '')
            b = next((y[1] for y in x.header if y[0].lower() == 'black'), '')
            self.model.append([d, w, b])
        view = Gtk.TreeView()
        view.set_model(self.model)
        view.set_activate_on_single_click(False)
        view.connect('row-activated', self.selected)
        for i, n in enumerate(['Date', 'White', 'Black']):
            col = Gtk.TreeViewColumn(n, Gtk.CellRendererText(), text=i)
            col.set_expand(True)
            col.set_alignment(0.5)
            view.append_column(col)
        self.scrollable_treelist.add(view)
        self.view = view
        HBox = Gtk.HBox().new(False, 1)
        Box.pack_start(HBox, False, False, 0)
        button = Gtk.Button.new_with_mnemonic('_OK')
        button.connect("clicked", self.on_ok_clicked)
        HBox.pack_end(button, False, False, 0)
        button = Gtk.Button.new_with_mnemonic('_Cancel')
        button.connect("clicked", self.on_cancel_clicked)
        HBox.pack_end(button, False, False, 0)
        self.show_all()

    def selected(self, tv, path, column):
        self.parent.game.setup_from_pgn(self.pgn_list[int(str(path))])
        self.parent.game.setup_from_pgn(pgn)
        config.cli.print('PGN loaded: navigate using the move sheet (press "'+
                         config.board.accel_movesheet+'" to activate)',
                         urwid.AttrSpec(config.console.echo_color, 'default'))
        self.destroy()

    def on_cancel_clicked(self, button):
        self.destroy()

    def on_ok_clicked(self, button):
        selection = self.view.get_selection().get_selected()
        if selection:
            i = int(str(self.model.get_path(selection[1])))
            self.parent.game.setup_from_pgn(self.pgn_list[i])
            self.destroy()

class BoardCommandsPopover(Gtk.Popover):
    def __init__(self, parent):
        self.parent = parent
        Gtk.Popover.__init__(self)
        self.connect('closed', self.on_delete)
        self.set_border_width(5)
        self.set_relative_to(parent)
        self.set_modal(True)
        self.set_position(Gtk.PositionType.RIGHT)
        if gi.version_info >= (3,16,0):
            self.set_transitions_enabled(False)
        vbox = Gtk.VBox().new(True, 1)
        self.add(vbox)
        if parent.game.interruptus:
            button = Gtk.Button.new_with_mnemonic('Close All Finished Games')
            button.get_children()[0].set_halign(Gtk.Align.START)
            button.connect("clicked", self.close_all)
            vbox.pack_start(button, True, True, 0)
        if parent.game.kind & KIND_PLAYING:
            if not parent.game.interruptus:
                for label, command in [
                        ('_Draw',      lambda x : 'draw'),
                        ('_Resign',    lambda x : 'resign'),
                        ('_Abort',     lambda x : 'abort'),
                        ('Ad_journ',   lambda x : 'adjourn'),
                        ('R_efresh',   lambda x : 'refresh'),
                        ('_More Time', lambda x :
                         'moretime {}'.format(x.more_time.get_value_as_int())),
                        ]:
                    button = Gtk.Button.new_with_mnemonic(label)
                    button.get_children()[0].set_halign(Gtk.Align.START)
                    button.command = command
                    button.connect("clicked", self.on_button_clicked)
                    vbox.pack_start(button, True, True, 0)
                # Moretime
                self.more_time = Gtk.SpinButton()
                self.more_time.set_adjustment(
                        Gtk.Adjustment(60, 0, 1000, 10, 60, 0))
                self.more_time.get_adjustment().configure(
                        60, 0, 1000, 10, 60, 0)
                vbox.pack_start(self.more_time, True, True, 0)
            else:
                for label, command in [
                        ('_Examine Last', lambda x : 'exl'),
                        ('_Rematch', lambda x : 'rematch'),
                        ('Say _Good Game!', lambda x : 'say Good Game!'),
                        ]:
                    button = Gtk.Button.new_with_mnemonic(label)
                    button.get_children()[0].set_halign(Gtk.Align.START)
                    button.command = command
                    button.connect("clicked", self.on_button_clicked)
                    vbox.pack_start(button, True, True, 0)
        elif parent.game.kind & KIND_OBSERVING:
            if parent.game.interruptus:
                cmd_list = [
                    ('Follow {}'.format(self.parent.game.player_names[0]),
                       lambda x : 'follow {}'.format(x.parent.game.player_names[0])),
                    ('Follow {}'.format(self.parent.game.player_names[1]),
                       lambda x : 'follow {}'.format(x.parent.game.player_names[1])),
                    ]
            else:
                cmd_list = [
                    ('_AnalysisBot obs {}'.format(self.parent.game.number),
                       lambda x : 'tell Analysisbot obs {}'.format(x.parent.game.number)),
                    ('AnalysisBot _stop', lambda x : 'tell Analysisbot stop'),
                    ('_Copy Game',
                       lambda x : 'copygame {}'.format(x.parent.game.number)),
                    ('Follow {}'.format(self.parent.game.player_names[0]),
                       lambda x : 'follow {}'.format(x.parent.game.player_names[0])),
                    ('Follow {}'.format(self.parent.game.player_names[1]),
                       lambda x : 'follow {}'.format(x.parent.game.player_names[1])),
                    ('_Refresh',
                       lambda x : 'refresh'),
                    ('_Unobserve',
                       lambda x : 'unobserve {}'.format(x.parent.game.number)),
                    ]
            for label, command in cmd_list:
                button = Gtk.Button.new_with_mnemonic(label)
                button.get_children()[0].set_halign(Gtk.Align.START)
                button.command = command
                button.connect("clicked", self.on_button_clicked)
                vbox.pack_start(button, True, True, 0)
        elif parent.game.kind & KIND_EXAMINING:
            for label, command in [
                   ('_AnalysisBot obs {}'.format(self.parent.game.number),
                       lambda x : 'tell Analysisbot obs {}'.format(x.parent.game.number)),
                    ('AnalysisBot _stop', lambda x : 'tell Analysisbot stop'),
                    ('_Refresh',   lambda x : 'refresh'),
                    ('_Unexamine', lambda x : 'unexamine'),
                    ]:
                button = Gtk.Button.new_with_mnemonic(label)
                button.get_children()[0].set_halign(Gtk.Align.START)
                button.command = command
                button.connect("clicked", self.on_button_clicked)
                vbox.pack_start(button, True, True, 0)
            button = Gtk.Button.new_with_mnemonic('_Load PGN')
            button.connect("clicked", self.on_load_clicked)
            button.get_children()[0].set_halign(Gtk.Align.START)
            vbox.pack_start(button, True, True, 0)
        button = Gtk.Button.new_with_mnemonic('Save to _PGN')
        button.connect("clicked", self.on_save_clicked)
        button.get_children()[0].set_halign(Gtk.Align.START)
        vbox.pack_start(button, True, True, 0)
        button = Gtk.Button.new_with_mnemonic('_Cancel')
        button.get_children()[0].set_halign(Gtk.Align.START)
        button.connect("clicked", self.on_cancel_clicked)
        vbox.pack_start(button, True, True, 0)

    def close_all(self, button):
        self.hide()
        for g in [g for g in config.gui.games if g.interruptus]:
            config.gui.game_destroy(g)

    def on_button_clicked(self, button):
        config.cli.send_cmd(button.command(self),
                                 True, save_history=False)
        self.hide()

    def on_cancel_clicked(self, button):
        self.hide()

    def on_delete(self, widget):
        pass

    def on_save_clicked(self, widget):
        self.hide()
        dialog = Gtk.FileChooserDialog("Choose a location", self.parent.win,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        frame = Gtk.Frame.new("PGN options")
        box = Gtk.VBox()
        frame.add(box)
        timestamps = Gtk.CheckButton('Store time stamps as comments')
        box.pack_start(timestamps, False, False, 0)
        append = Gtk.CheckButton('Append game at the end of file')
        append.set_active(True)
        box.pack_start(append, False, False, 0)
        box.show_all()
        dialog.set_extra_widget(frame)
        dialog.set_default_size(-1, -1)
        date = strftime('%Y.%m.%d', localtime())
        dialog.set_current_name('{}_{}_{}.pgn'.format(date,
                                             self.parent.game.player_names[1],
                                             self.parent.game.player_names[0]))
        dialog.set_do_overwrite_confirmation(True)
        def confirm_overwrite(widget, check):
            if check.get_active():
                return Gtk.FileChooserConfirmation.ACCEPT_FILENAME
            else:
                return Gtk.FileChooserConfirmation.CONFIRM
        dialog.connect('confirm_overwrite', confirm_overwrite, append)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            mode = 'a' if append.get_active() else 'w'
            with open(dialog.get_filename(), mode) as fd:
                self.parent.game.pgn(fd, timestamps.get_active())
        dialog.destroy()

    def on_load_clicked(self, widget):
        self.hide()
        dialog = Gtk.FileChooserDialog("Choose a file", self.parent.win,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_size(1, 1)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            pgn = Pgn(path=dialog.get_filename())
            if isinstance(pgn, list):
                PgnGameSelector(self.parent, pgn)
            else:
                self.parent.game.setup_from_pgn(pgn)
                config.cli.print(
                        'PGN loaded: navigate using the move sheet (press "'+
                        config.board.accel_movesheet+'" to activate)',
                        urwid.AttrSpec(config.console.echo_color, 'default'))
        dialog.destroy()


class DimensionsSet(object):
    turnbox_y = turn_x = turn_y = turn_width = turn_height = turn_off = \
    tp_xoff = tp_yoff = tc_xoff = tc_yoff = bp_xoff = bp_yoff = bc_xoff = \
    bc_yoff = xoff = yoff = side = bside = bxoff = byoff = G = lw = \
    fig_size = wwidth = wheight = promote_height = promote_width = \
    promote_yoff = promote_xoff = promote_txoff = promote_tyoff = \
    promote_fyoff = material_x = material_y = font_size = font_coords_size = \
    draw_border = border_width = _border_width = 0
    sside = 1

    def __setattr__(self, name, value):
        if name == 'sside':
            object.__setattr__(self, name, value if value>0 else 1)
        else:
            object.__setattr__(self, name, value if value>=0 else 0)

    @property
    def border_width(self):
        return self._border_width if self.draw_border else 0

    @border_width.setter
    def border_width(self, value):
        self._border_width = value

class ChangeGameDialog(Gtk.Dialog):
    def __init__(self, parent, new_game):
        Gtk.Dialog.__init__(self, 'Change Game', parent.win)
        label = Gtk.Label('Open game:\n'+new_game.name)
        self.get_content_area().pack_start(label, False, False, 0)
        self.add_button('in _This Window', 1)
        self.add_button('in _Other Window', 0)
        self.set_default_response(1)
        self.show_all()

class Board (Gtk.DrawingArea):
    def __init__(self, game):
        # Window cfg
        da = Gtk.DrawingArea.__init__(self)
        bg = Gdk.RGBA.from_color(Gdk.color_parse('#101010'))
        self.override_background_color(Gtk.StateType.NORMAL, bg)
        self.connect('draw', self.on_draw)
        self.connect('size_allocate', self.on_resize, config.board.font_size)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key_press_event', self.key_cmd)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button_press_event', self.mouse_cmd)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect('scroll_event', self.scroll_cmd)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect('button_release_event', self.mouse_release)
        self.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        self.connect('motion-notify-event', self.mouse_move)
        self.set_can_focus(True)
        self.grab_focus()
        #
        self.png_figures = {x : None for x in 'KQRBNPkqrbnp'}
        self.ico_figures = {x : None for x in 'KQRBNPkqrbnp'}
        self.key_commands = [
          (config.board.accel_fforward          , self.cmd_fforward),
          (config.board.accel_frewind           , self.cmd_frewind),
          (config.board.accel_forward           , self.cmd_forward),
          (config.board.accel_rewind            , self.cmd_rewind),
          (config.board.accel_prev_move         , self.cmd_prev_move),
          (config.board.accel_next_move         , self.cmd_next_move),
          (config.board.accel_flip              , self.cmd_flip),
          (config.board.accel_promote           , self.cmd_promote),
          ('<Shift>'+config.board.accel_promote , self.cmd_promote),
          (config.board.accel_border            , self.cmd_border),
          (config.board.accel_board_commands    , self.cmd_board_commands),
          (config.board.accel_seek_graph        , config.gui.new_seek_graph),
          (config.board.accel_movesheet         , self.cmd_movetree),
        ]
        for accel, txt in config.board.command:
            self.key_commands.append((accel,
               lambda event, txt=txt, self=self: config.cli.cmd_line.eval_bind(eval(txt))))
        self.game = game
        self.flip = not self.game.side
        self.pop = BoardCommandsPopover(self)
        self.geom = DimensionsSet()
        self.promote_to = 0
        self.promote_show = False
        self.promote_timeout = None
        if self.game.kind & (KIND_EXAMINING | KIND_PLAYING):
            config.gui.seek_graph_destroy()
        if config.board.border:
            self.cmd_border(True)
        else:
            self.geom.draw_border = False
        GObject.timeout_add(99, self.redraw_turn)

        self.win = Gtk.Window(title=self.game.name)
        self.win.game = self
        self.paned = Gtk.HPaned()
        self.win.add(self.paned)
        self.paned.pack1(self)
        self.movetree = None
        #self.paned.pack2(Gtk.Button.new_with_mnemonic('_Cancel'))
        self.win.set_default_size(480,532)
        self.win.connect('delete-event', self.on_board_delete)
        self.win.add_events(Gdk.EventMask.FOCUS_CHANGE_MASK)
        self.win.connect('focus-in-event', self.on_board_focus)
        self.win.show_all()

    def offer(self, txt):
        OfferDialog(self, txt)

    def change_game(self, new_game):
        if config.board.auto_replace == 'on':
            self.set_game(new_game)
        else:
            dialog = ChangeGameDialog(self, new_game)
            if dialog.run():
                self.set_game(new_game)
            else:
                new_game.set_board(Board(new_game))
            dialog.destroy()

    def set_game(self, game):
        self.game.board = None
        config.gui.game_destroy(self.game)
        self.game = game
        game.set_board(self)
        self.reset(True)

    def reset(self, hard):
        if hard:
            self.pop = BoardCommandsPopover(self)
            self.flip = not self.game.side
            if self.game.kind & KIND_PLAYING:
                self.geom.draw_border = False
            self.win.set_title(self.game.name)
            self.on_resize(self, 0)
        self.redraw()

    def cmd_border(self, event, value=False):
        self.geom.draw_border = value if value else not self.geom.draw_border
        self.on_resize(self, 0)
        self.redraw()

    def cmd_movetree(self, event, value=False):
        mt = self.paned.get_child2()
        if mt:
            if mt.get_visible():
                mt.hide()
            else:
                mt.show()
        else:
            self.movetree = movetree.MoveTree(self)
            self.paned.pack2(self.movetree, False, True)
            self.paned.set_position(self.geom.wwidth*0.7)
            self.win.show_all()
        self.grab_focus()
        #GObject.idle_add(self.paned.queue_draw)

    def cmd_board_commands(self, event, mevent=None):
        if self.promote_show:
            self.promote_hide()
            return
        ri = self.get_allocation().copy()
        ri.width=ri.height=0
        if mevent:
            ri.x = mevent.x
            ri.y = mevent.y
        self.pop.set_pointing_to(ri)
        self.pop.show_all()

    def cmd_fforward(self, event):
        self.game.forward(999)
        self.redraw()
        return True

    def cmd_frewind(self, event):
        self.game.backward(999)
        self.redraw()
        return True

    def cmd_forward(self, event):
        self.game.forward(6)
        self.redraw()
        return True


    def cmd_rewind(self, event):
        self.game.backward(6)
        self.redraw()
        return True

    def cmd_prev_move(self, event):
        self.game.backward(1)
        self.redraw()
        return True

    def cmd_next_move(self, event):
        self.game.forward(1)
        self.redraw()
        return True

    def cmd_flip(self, event):
        self.flip = not self.flip
        self.on_resize(self, 0)
        self.redraw()
        return True

    def cmd_promote(self, event):
        if self.game.kind & (KIND_PLAYING | KIND_EXAMINING):
            self.promote_show = True
            if self.promote_timeout:
                if event.state & Gdk.ModifierType.SHIFT_MASK:
                    self.promote_to = (self.promote_to - 1)% 4
                else:
                    self.promote_to = (self.promote_to + 1)% 4
                GLib.source_remove(self.promote_timeout)
            config.cli.send_cmd('promote {}'.format('qrbn'[self.promote_to]),
                    save_history=False)
            self.promote_timeout = GObject.timeout_add_seconds(2,
                                                            self.promote_hide)
            GObject.idle_add(self.queue_draw_area,
                self.geom.promote_xoff, self.geom.promote_yoff,
                self.geom.promote_width, self.geom.promote_height)
            return True

    def promote_hide(self):
        self.promote_show = False
        if self.promote_timeout:
            GLib.source_remove(self.promote_timeout)
        self.promote_timeout = None
        GObject.idle_add(self.queue_draw_area,
            self.geom.promote_xoff-5, self.geom.promote_yoff-5,
            self.geom.promote_width+10, self.geom.promote_height+10)

    def key_cmd(self, widget, event):
        state = event.state & ~Gdk.ModifierType.BUTTON1_MASK
        cmd = next((c[1] for c in self.key_commands
                if ( Gtk.accelerator_parse(c[0]) ==
                     ( (Gdk.keyval_to_lower(event.keyval) if
                        event.keyval not in [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
                        else Gdk.KEY_Tab), state)
                   )),
                None)
        if cmd:
            if cmd not in [self.cmd_promote, self.cmd_board_commands]:
                self.promote_hide()
            cmd(event)
        else:
            if event.keyval not in [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R]:
                self.promote_hide()
            config.cli.key_from_gui(event.keyval)
        config.cli.redraw()

    def mouse_cmd(self, widget, event):
        self.promote_hide()
        if event.button == 1:
            x = floor((event.x - self.geom.bxoff)/self.geom.sside)
            y = floor((event.y - self.geom.byoff)/self.geom.sside)
            if x < 0 or x > 7 or y < 0 or y > 7:
                return False
            s = (7-x, y) if self.flip else (x, 7-y)
            cmd = self.game.click(s)
            if(cmd):
                config.cli.send_cmd(cmd, save_history=False)
            self.redraw()
        elif event.button == 3:
            self.cmd_board_commands(None, mevent=event)

    def scroll_cmd(self, widget, event):
        self.promote_hide()
        if event.direction == Gdk.ScrollDirection.UP:
            self.cmd_next_move(None)
        if event.direction == Gdk.ScrollDirection.DOWN:
            self.cmd_prev_move(None)

    def mouse_move(self, widget, event):
        if self.game.piece_clicked and not self.game.piece_flying:
            self.win.get_window().set_cursor(
                    self.ico_figures[self.game.piece_clicked])
            self.game.piece_flying = True
            self.redraw()

    def mouse_release(self, widget, event):
        self.promote_hide()
        self.win.get_window().set_cursor(None)
        x = floor((event.x - self.geom.bxoff)/self.geom.sside)
        y = floor((event.y - self.geom.byoff)/self.geom.sside)
        if x < 0 or x > 7 or y < 0 or y > 7:
            self.game.piece_flying = False
            self.redraw()
            return
        s = (7-x, y) if self.flip else (x, 7-y)
        cmd = self.game.release(s)
        if(cmd):
            config.cli.send_cmd(cmd, save_history=False)
        self.redraw()

    def on_resize(self, widget, cr,
            font_size=config.board.font_size):

        self.geom.font_size = font_size

        self.geom.wwidth = self.get_allocated_width()
        self.geom.wheight = self.get_allocated_height()

        if self.geom.wwidth < 50 or self.geom.wheight < 50:
            return False

        pc = self.get_pango_context()
        pc.set_font_description(
               Pango.FontDescription.from_string(config.board.font+' Bold '
                   +str(font_size))
               )
        m = pc.get_metrics(None)
        clk_height = (m.get_descent()+m.get_ascent())/Pango.SCALE

        lay = Pango.Layout(pc)
        txt = max((t for t in [" 00:00 00"]+ self.game.player),
                key=lambda t: len(t))
        lay.set_text(txt, -1)
        L_turnbox_width, height = lay.get_pixel_size()

        Lside = min(self.geom.wwidth-L_turnbox_width, self.geom.wheight)
        Pside = min(self.geom.wheight-2*clk_height, self.geom.wwidth)

        lay.set_text(" 00:00", -1)
        clk_width, height = lay.get_pixel_size()

        # Landscape
        if Lside > Pside:
            self.geom.side = Lside
            self.geom.xoff = 0
            self.geom.yoff = (self.geom.wheight-self.geom.side)*0.5

            self.geom.tp_xoff = self.geom.side
            self.geom.tp_yoff = self.geom.yoff
            self.geom.tc_xoff = self.geom.side
            self.geom.tc_yoff = self.geom.yoff+clk_height
            self.geom.bp_xoff = self.geom.side
            self.geom.bp_yoff = self.geom.yoff+self.geom.side-2*clk_height
            self.geom.bc_xoff = self.geom.side
            self.geom.bc_yoff = self.geom.yoff+self.geom.side-clk_height
            self.geom.turn_width  = L_turnbox_width
            self.geom.turn_height = 2*clk_height
            self.geom.turn_x      = self.geom.side
            self.geom.turn_y      = self.geom.yoff
            self.geom.turn_off    = self.geom.side-self.geom.turn_height

            if 2*self.geom.turn_height > self.geom.wheight:
                self.on_resize(self, 0, font_size*0.8)
                return False

            lay.set_text("0", -1)
            c_width, height = lay.get_pixel_size()

            self.geom.material_x = self.geom.tc_xoff + clk_width + c_width
            self.geom.material_y = (self.geom.bc_yoff
                            if ( self.flip ^ self.game.side )
                                        else self.geom.tc_yoff)
        # Portrait
        else:
            self.geom.side = Pside
            self.geom.xoff = (self.geom.wwidth-self.geom.side)*0.5
            if self.geom.xoff:
                self.geom.yoff = clk_height
            else:
                self.geom.yoff = (self.geom.wheight-self.geom.side)*0.5

            self.geom.tc_xoff = self.geom.xoff+self.geom.side-clk_width
            self.geom.tc_yoff = self.geom.yoff-clk_height
            self.geom.bc_xoff = self.geom.xoff+self.geom.side-clk_width
            self.geom.bc_yoff = self.geom.yoff+self.geom.side
            self.geom.turn_width  = self.geom.side
            self.geom.turn_height = clk_height
            self.geom.turn_x      = self.geom.xoff
            self.geom.turn_y      = self.geom.yoff-clk_height
            self.geom.turn_off    = self.geom.side+self.geom.turn_height

            self.geom.tp_yoff = self.geom.yoff-clk_height
            self.geom.bp_yoff = self.geom.yoff+self.geom.side

            if config.board.handle_justify == 'right':
                lay.set_text(self.game.player[self.flip]+' ', -1)
                tp = self.geom.tp_xoff = self.geom.tc_xoff-lay.get_pixel_size()[0]
                lay.set_text(self.game.player[not self.flip]+' ', -1)
                bp = self.geom.bp_xoff = self.geom.bc_xoff-lay.get_pixel_size()[0]
                self.geom.material_x = self.geom.xoff
                lay.set_text('000', -1)
                if (tp < self.geom.xoff or
                       bp < self.geom.xoff+lay.get_pixel_size()[0]):
                    self.on_resize(self, 0, font_size*0.8)
                    return False
            else:
                self.geom.tp_xoff = self.geom.xoff
                self.geom.bp_xoff = self.geom.xoff

                lay.set_text(self.game.player[not self.game.side]+' ', -1)
                op_width = lay.get_pixel_size()[0]
                ox = self.geom.xoff + op_width

                lay.set_text(self.game.player[self.game.side], -1)
                p_width, height = lay.get_pixel_size()
                px = self.geom.xoff + p_width

                lay.set_text('000', -1)
                material_width, height = lay.get_pixel_size()

                if self.flip ^ self.game.side:
                    self.geom.material_x = (self.geom.bp_xoff + p_width
                                + self.geom.bc_xoff - material_width)*0.5
                else:
                    self.geom.material_x = (self.geom.tp_xoff + p_width
                                + self.geom.tc_xoff - material_width)*0.5

                if px >= self.geom.material_x or ox >= self.geom.tc_xoff:
                    self.on_resize(self, 0, font_size*0.8)
                    return False

            if self.flip ^ self.game.side:
                self.geom.material_y = self.geom.bp_yoff
            else:
                self.geom.material_y = self.geom.tp_yoff

        def coords_font_size(size):
            pc.set_font_description(
                   Pango.FontDescription.from_string(config.board.font+' '
                       +str(size))
                   )
            m = pc.get_metrics(None)
            fheight = (m.get_descent()+m.get_ascent())/Pango.SCALE
            self.geom.border_width = 1.5*fheight
            self.geom.bside = self.geom.side-2*self.geom.border_width
            self.geom.sside = self.geom.bside*0.125
            lay = Pango.Layout(pc)
            lay.set_text('h', -1)
            width, height = lay.get_pixel_size()
            if width > self.geom.sside or fheight > self.geom.sside:
                return coords_font_size(size*0.8)
            else:
                return size

        self.geom.font_coords_size = coords_font_size(config.board.font_coords_size)

        self.geom.bside = self.geom.side-2*self.geom.border_width
        self.geom.sside = self.geom.bside*0.125
        self.geom.lw = self.geom.sside*0.04

        self.geom.bxoff = self.geom.xoff + self.geom.border_width
        self.geom.byoff = self.geom.yoff + self.geom.border_width

        # Promote
        pc.set_font_description(
                Pango.FontDescription.from_string(config.board.font+' Bold '
                    +str(int(0.8*font_size)))
                )
        lay = Pango.Layout(pc)
        lay.set_text('Promote to:', -1)
        width, height = lay.get_pixel_size()
        self.geom.promote_height = height*2.2+self.geom.sside
        self.geom.promote_width  = height+max(width, 4*self.geom.sside)
        self.geom.promote_yoff   = self.geom.byoff+0.5*(
                                    self.geom.bside-self.geom.promote_height)
        self.geom.promote_xoff   = self.geom.bxoff+0.5*(
                                       self.geom.bside-self.geom.promote_width)
        self.geom.promote_txoff  = self.geom.promote_xoff+0.5*height
        self.geom.promote_tyoff  = self.geom.promote_yoff+0.5*height
        self.geom.promote_fyoff  = 7-(self.geom.promote_yoff
                                -self.geom.byoff+1.7*height)/self.geom.sside


        if self.geom.draw_border:
            pc.set_font_description(
                    Pango.FontDescription.from_string(config.board.font+' '
                        +str(self.geom.font_coords_size))
                    )
            m = pc.get_metrics(None)
            fheight = (m.get_descent()+m.get_ascent())/Pango.SCALE
            lay = Pango.Layout(pc)
            self.file_coords = []
            for x, l in enumerate('abcdefgh'):
                lay.set_text(l, -1)
                width, height = lay.get_pixel_size()
                xx = 7-x if self.flip else x
                self.file_coords.append(
                 (l,
                 self.geom.xoff+self.geom.border_width+self.geom.sside*(0.5+xx)-width*0.5,
                 self.geom.yoff+self.geom.border_width*0.5-fheight*0.5)
                 )
                self.file_coords.append(
                 (l,
                 self.geom.xoff+self.geom.border_width+self.geom.sside*(0.5+xx)-width*0.5,
                 self.geom.yoff+self.geom.border_width*1.5-fheight*0.5+self.geom.bside)
                 )
                txt = str(8-x)
                lay.set_text(txt, -1)
                width, height = lay.get_pixel_size()
                self.file_coords.append(
                    (txt,
                    self.geom.xoff+self.geom.border_width*0.5-width*0.5,
                    self.geom.yoff+self.geom.border_width
                     +self.geom.sside*(0.5+xx)-fheight*0.5)
                )
                self.file_coords.append(
                    (txt,
                    self.geom.xoff+self.geom.border_width*1.5-width*0.5+self.geom.bside,
                    self.geom.yoff+self.geom.border_width
                     +self.geom.sside*(0.5+xx)-fheight*0.5)
                )
        self.reload_figures()
        self.win.set_icon_from_file(config.figPath+'/24/p.png')
        return True

    def reload_figures(self):
        fig_scale = 1.17
        mono_res = next(x for x in config.fsets if x >= self.geom.sside/fig_scale)
        self.geom.G = fig_scale*mono_res/self.geom.sside
        self.mono_res = mono_res
        self.geom.fig_size = self.geom.sside/fig_scale

        for mono in 'KQRBNPkqrbnp':
            fn = config.figPath+'/'+str(mono_res)+"/"+mono+".png"
            fd = cairo.ImageSurface.create_from_png(fn)
            self.png_figures[mono] = cairo.SurfacePattern(fd)
            if self.geom.sside > 0:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(fn,
                        int(ceil(mono_res)), int(ceil(mono_res)))
                self.ico_figures[mono] = Gdk.Cursor.new_from_pixbuf(
                    Gdk.Display.get_default(),pb,int(mono_res/2),
                    int(mono_res/2))

    def on_draw(self, widget, cr):
        # background
        cr.rectangle(0, 0, self.geom.wwidth, self.geom.wheight)
        cr.set_source_rgb(*config.board.bg)
        cr.fill()
        if self.geom.wwidth < 50 or self.geom.wheight < 50:
            return False
        pc = self.get_pango_context()
        pc.set_font_description(
               Pango.FontDescription.from_string(config.board.font+' Bold '
                   +str(self.geom.font_size))
               )
        lay = Pango.Layout(pc)
        # Mesa
        cr.set_source_rgb(*config.board.border_color)
        cr.rectangle(self.geom.xoff, self.geom.yoff,
                     self.geom.side, self.geom.side)
        cr.fill()
        # Tablero
        cr.set_source_rgb(*config.board.dark_square)
        cr.rectangle(self.geom.xoff+self.geom.border_width,
                     self.geom.yoff+self.geom.border_width,
                     self.geom.bside, self.geom.bside)
        cr.fill()
        for i in range(0, 8):
            for j in range(0, 8):
                if (i+j)%2:
                    (x, y) = (7-i, j) if self.flip else (i, 7-j)
                    cr.set_source_rgb(*config.board.light_square)
                    cr.rectangle(
                            (self.geom.xoff+self.geom.border_width+x*self.geom.sside),
                            (self.geom.yoff+self.geom.border_width+y*self.geom.sside),
                            (self.geom.sside), (self.geom.sside))
                    cr.fill()
        for s in self.game.selected:
            i, j = s
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.set_source_rgb(
                   *(config.board.square_move_sent if self.game.move_sent else
                        (config.board.light_square_selected if (i+j)%2 else
                            config.board.dark_square_selected))
                        )
            cr.rectangle((self.geom.xoff + self.geom.border_width + x*self.geom.sside),
                         (self.geom.yoff + self.geom.border_width + y*self.geom.sside),
                         (self.geom.sside), (self.geom.sside))
            cr.fill()
        for s in self.game.marked:
            i, j = s
            cr.set_source_rgb(*config.board.square_marked)
            cr.set_line_width(self.geom.lw)
            (x, y) = (7-i, j) if self.flip else (i, 7-j)
            cr.rectangle((self.geom.xoff + self.geom.border_width +
                          x*self.geom.sside+self.geom.lw*0.5),
                         (self.geom.yoff + self.geom.border_width +
                             y*self.geom.sside+self.geom.lw*0.5),
                         (self.geom.sside-self.geom.lw),
                         (self.geom.sside-self.geom.lw))
            cr.stroke()
        # mini borde
        cr.set_source_rgb(*config.board.bg)
        cr.rectangle(self.geom.xoff, self.geom.yoff,
                     self.geom.side, self.geom.side)
        cr.set_line_width(0.8)
        cr.stroke()
        # TAPON
        if self.game.altline:
            cr.rectangle(self.geom.xoff, self.geom.yoff,
                         self.geom.side, self.geom.side)
            cr.set_source_rgba(1.0, 0.270142, 0.827451, 0.06)
            cr.fill()
        # TAPON
        if self.game.interruptus:
            cr.rectangle(self.geom.xoff, self.geom.yoff,
                         self.geom.side, self.geom.side)
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
            cr.fill()
        # Figuras
        for s, f in self.game.figures():
            self.draw_piece(s,f,cr)
        # time
        time = list(self.game.time)
        # Turn Square
        turn_y = self.geom.turn_y + (0 if not (self.game.turn^self.flip)
                else (self.geom.turn_off))
        cr.rectangle(self.geom.turn_x, turn_y,
                     self.geom.turn_width, self.geom.turn_height)
        self.geom.turnbox_y  = int(turn_y)
        ma_time = time[self.game.turn]
        if ma_time < 20 and ma_time % 2 and self.game.is_being_played():
            cr.set_source_rgb(*config.board.turn_box_excl)
        else:
            cr.set_source_rgb(*config.board.turn_box)
        cr.fill()
        # Player TOP
        if not (self.game.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(self.geom.tp_xoff, self.geom.tp_yoff)
        lay.set_text(self.game.player[self.flip], -1)
        PangoCairo.show_layout(cr, lay)
        cr.move_to(self.geom.tc_xoff, self.geom.tc_yoff)
        ma_time = time[self.flip]
        lay.set_text((" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60),-1)
        PangoCairo.show_layout(cr, lay)
        # Player BOTTOM
        if (self.game.turn^self.flip):
            cr.set_source_rgb(*config.board.text_active)
        else:
            cr.set_source_rgb(*config.board.text_inactive)
        cr.move_to(self.geom.bp_xoff, self.geom.bp_yoff)
        lay.set_text(self.game.player[not self.flip],-1)
        PangoCairo.show_layout(cr, lay)
        cr.move_to(self.geom.bc_xoff, self.geom.bc_yoff)
        ma_time = time[not self.flip]
        lay.set_text((" " if ma_time > 0 else "-") +
                     "{:0>2d}:{:0>2d}".format(abs(ma_time)//60,
                                              abs(ma_time)%60), -1)
        PangoCairo.show_layout(cr, lay)
        # Material
        if (self.game.turn^self.game.side):
            cr.set_source_rgb(*config.board.text_inactive)
        else:
            cr.set_source_rgb(*config.board.text_active)
        cr.move_to(self.geom.material_x, self.geom.material_y)
        lay.set_text(self.game.material,-1)
        PangoCairo.show_layout(cr, lay)
        # Coordenadas
        pc.set_font_description(
                   Pango.FontDescription.from_string(config.board.font+' '
                       +str(self.geom.font_coords_size))
                   )
        lay = Pango.Layout(pc)
        cr.set_source_rgba(*config.board.text_active)
        if self.geom.draw_border:
            for l, x, y in self.file_coords:
                cr.move_to(x, y)
                lay.set_text(l, -1)
                PangoCairo.show_layout(cr, lay)
        # promote to:
        if self.promote_show:
            cr.rectangle(self.geom.promote_xoff, self.geom.promote_yoff,
                         self.geom.promote_width, self.geom.promote_height)
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.6)
            cr.fill()
            pc.set_font_description( Pango.FontDescription.from_string(
                        config.board.font+' Bold '
                        +str(int(0.8*self.geom.font_size)))
                    )
            lay = Pango.Layout(pc)
            lay.set_text('Promote to:', -1)
            cr.set_source_rgba(*config.board.text_active)
            cr.move_to(self.geom.promote_txoff, self.geom.promote_tyoff)
            PangoCairo.show_layout(cr, lay)
            for i, f in enumerate('QRBN' if self.game.side else 'qrbn'):
                s = (2+i,self.geom.promote_fyoff)
                self.draw_piece(s,f,cr, coords=s)
                if 'qrbn'[self.promote_to] == f.lower():
                    cr.set_source_rgb(*config.board.square_marked)
                    cr.set_line_width(self.geom.lw)
                    x, y = s
                    cr.rectangle((self.geom.xoff + self.geom.border_width +
                        x*self.geom.sside+self.geom.lw*0.5),
                                 (self.geom.yoff + self.geom.border_width +
                                     (7-y)*self.geom.sside+self.geom.lw*0.5),
                                 (self.geom.sside-self.geom.lw),
                                 (self.geom.sside-self.geom.lw))
                    cr.stroke()

    # figura
    def draw_piece(self, pos, fig, cr, coords=None):
        cr.save()
        if coords:
            x, y = coords
        else:
            x, y = (7-pos[0], 7-pos[1]) if self.flip else (pos[0], pos[1])
        matrix = cairo.Matrix(
           xx = self.geom.G, yy = self.geom.G,
           x0 = self.geom.G*(-self.geom.bxoff-(x*self.geom.sside
                                   +0.5*(self.geom.sside-self.geom.fig_size))),
           y0 = self.geom.G*(-self.geom.byoff- ((7-y)*self.geom.sside
                                    +0.5*(self.geom.sside-self.geom.fig_size)))
           )
        pattern = self.png_figures[fig]
        pattern.set_matrix(matrix)
        cr.rectangle(
                self.geom.bxoff+x*self.geom.sside+0.5*(self.geom.sside
                                                        -self.geom.fig_size)+1,
                self.geom.byoff+(7-y)*self.geom.sside
                                   +0.5*(self.geom.sside-self.geom.fig_size)+1,
                self.geom.fig_size-2, self.geom.fig_size-2
                )
        cr.clip()
        cr.set_source(pattern)
        cr.paint()
        cr.restore()

    def redraw(self):
        self.game.set_altline()
        GObject.idle_add(self.queue_draw)

    def redraw_turn(self):
        GObject.idle_add(
            self.queue_draw_area,
            self.geom.turn_x, self.geom.turnbox_y,
            self.geom.turn_width, self.geom.turn_height)
        return True

    def on_board_delete(self, widget, event):
        self = widget.game
        if self.game.kind & KIND_EXAMINING and not self.game.kind & KIND_OBSERVING:
            config.cli.send_cmd("unexamine", save_history=False,
               wait_for='You are no longer examining game {}'.format(self.game.number))
            config.gui.game_destroy(self.game)
            return False
        elif self.game.kind & KIND_OBSERVING:
            if not self.game.interruptus:
                config.block12.append(self.game.number)
                config.cli.send_cmd("unobserve {}".format(self.game.number),
                        save_history=False,
                        wait_for='Removing game {}'.format(self.game.number))
            config.gui.game_destroy(self.game)
            return False
        elif self.game.kind & KIND_PLAYING:
            if self.game.interruptus:
                config.gui.game_destroy(self.game)
                return False
            else:
                BoardExit(self)
                return True
        config.gui.game_destroy(self.game)
        return False

    def on_board_focus(self, widget, direction):
        if (self.game.kind & KIND_OBSERVING and
             len([g for g in config.gui.games
                    if g.kind & KIND_OBSERVING and not g.interruptus])>1
             and not self.game.interruptus):
            config.cli.send_cmd('primary {}'.format(self.game.number),
                                save_history=False)

