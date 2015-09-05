#!/usr/bin/python

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

import sys, linecache, traceback

from papageorge.gui import *
from papageorge.cli import *

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

def run(fics_user, fics_pass):
    GObject.threads_init()
    #log = open('log','w')
    log = None
    cli = SCBoard_cli(fics_user, fics_pass, log)
    cli.connect_gui(GUI(cli))
    try:
        cli.connect_mainloop()
    except: 
        txt = PrintException()
        if log:
            log.write(str(txt)+'\n')
        cli.exit(True)
    if log:
        log.close()
    Gtk.main_quit()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        fics_user, fics_pass = sys.argv[1:3]
    else:
        fics_user = input('user: ')
        if fics_user != 'guest' and len(fics_user) > 0:
            fics_pass = input('pass: ')
        else:
            fics_pass = ''
    if len(fics_user) == 0:
        fics_user = 'guest'
        fics_pass = ''
    GObject.threads_init()
    #log = open('log','w')
    log = None
    cli = SCBoard_cli(fics_user, fics_pass, log)
    cli.connect_gui(GUI(cli))
    try:
        cli.connect_mainloop()
    except: 
        txt = PrintException()
        if log:
            log.write(str(txt)+'\n')
        cli.exit(True)
    if log:
        log.close()
    Gtk.main_quit()

