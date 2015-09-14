# config - configure papageorge with ~/.papageorge.conf

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

import os

_board_settings = {
        'bg'                    : '#101010',
        'text_active'           : '#ffffff',
        'text_inactive'         : '#707070',
        'turn_box'              : '#343434',
        'turn_box_excl'         : '#702828',
        'dark_square'           : '#acacc6',
        'dark_square_selected'  : '#8787a1',
        'light_square'          : '#d3d3ec',
        'light_square_selected' : '#f8f8ff',
        'border'                : '#000000',
        'square_move_sent'      : '#acacc6',
        'square_marked'         : '#f2f2f2',
        'font'                  : 'Inconsolata'
        }

_board_commands = [
        #['g', '"say caca!"'],
        ]

fics_user = ''

def rgb(hcolor):
    i = int(hcolor.lstrip('#'),16)
    return (((i>>16)&255)/255,
             ((i>>8)&255)/255,
                  (i&255)/255)

class SettingsSet(object):
    def __init__(self, settings):
        self._settings = settings
    def __getattr__(self, name):
        if 'commands' in name:
            return _board_commands
        if name in self._settings:
            if '#' in self._settings[name]:
                return rgb(self._settings[name])
            else:
                return self._settings[name]
        raise AttributeError(name)
 
COMMENT_CHAR = '%'
OPTION_CHAR =  '='

def parse_config(filename):
    f = open(filename)
    for line in f:
        if COMMENT_CHAR in line:
            line, comment = line.split(COMMENT_CHAR, 1)
        if OPTION_CHAR in line:
            sset, line = line.split('_',1)
            option, value = line.split(OPTION_CHAR, 1)
            option = option.strip()
            value = value.strip()
            if 'board' in sset:
                if option in _board_settings.keys():
                    _board_settings[option] = value
                elif 'cmd_' in option:
                    spam, line = line.split('_',1)
                    accel, texto = line.split(OPTION_CHAR, 1)
                    accel = accel.strip()
                    texto = texto.strip()
                    _board_commands.append((accel, texto))
                else:
                    raise Exception
    f.close()
 
conf_file = os.path.expanduser('~/.papageorge.conf')
if os.path.isfile(conf_file):
    parse_config(conf_file)

board = SettingsSet(_board_settings)

