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

import sys, linecache, traceback, os, datetime

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import GObject, Gtk

from papageorge.cli import CLI
from papageorge.gui import GUI
import papageorge.config as config

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    dstr = datetime.datetime.strftime(datetime.datetime.now(),
            '%Y-%m-%d %H:%M:%S')
    return '{} EXCEPTION IN ({}, LINE {} "{}"): {}\n{}'.format(dstr,filename,
            lineno, line.strip(), exc_obj, traceback.format_exc())

def run(fics_pass):
    GObject.threads_init()
    if config.general.log:
        config.logfd = open(os.path.expanduser(config.general.log),'a')
    config.cli = CLI(fics_pass)
    config.gui = GUI()
    try:
        config.cli.connect_mainloop()
    except: 
        txt = PrintException()
        if config.logfd:
            config.log(str(txt))
        config.cli.exit(True)
    if config.logfd:
        config.logfd.close()
    Gtk.main_quit()

