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

class cRGB(tuple):
    def __new__(cls, value):
        i = int(value.lstrip('#'),16)
        return tuple.__new__(cls, (((i>>16)&255)/255,
                                   ((i>>8)&255)/255,
                                        (i&255)/255))

_settings = {
            'board' : {
                'bg'                    : cRGB('#101010'),
                'border_color'          : cRGB('#000000'),
                'text_active'           : cRGB('#ffffff'),
                'text_inactive'         : cRGB('#707070'),
                'turn_box'              : cRGB('#343434'),
                'turn_box_excl'         : cRGB('#702828'),
                'dark_square'           : cRGB('#a0a0a8'),
                'light_square'          : cRGB('#bdbdc5'),
                'dark_square_selected'  : cRGB('#909098'),
                'light_square_selected' : cRGB('#d0d0d8'),
                'square_move_sent'      : cRGB('#b0b0b8'),
                'square_marked'         : cRGB('#f2f2f2'),
                'font'                  : 'Inconsolata',
                'font_size'             : 18,
                'border'                : False,
                'font_coords_size'      : 10,
                'command'               : [(False,)],
                'accel_fforward'        : '<Shift>Up',
                'accel_frewind'         : '<Shift>Down',
                'accel_forward'         : 'Up',
                'accel_rewind'          : 'Down',
                'accel_prev_move'       : 'Left',
                'accel_next_move'       : 'Right',
                'accel_flip'            : '<Control>f',
                'accel_promote'         : 'Tab',
                'accel_promote'         : '<Shift>Tab',
                'accel_border'          : '<Control>b',
                'accel_board_commands'  : 'Escape',
                'accel_seek_graph'      : 'F5'
            },
            'console' : {
                'default'               : '#999',
                'game_end'              : '#eee',
                'echo'                  : '#aa0',
                'handle_mouse'          : True,
                'highlight'             : [(False,)],
                'palette'               : [],
                'command'               : [(False,)]
            },
            'general' : {
                'log'                   : False,
                'log_file'              : '~/papageorge.log'
            }
        }

fics_user = ''

COMMENT_CHAR = ';'
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
            if sset in _settings.keys():
                if option in _settings[sset].keys():
                    if isinstance(_settings[sset][option], bool):
                        _settings[sset][option] = bool(eval(value))
                    elif isinstance(_settings[sset][option], list):
                        if (len(_settings[sset][option]) and 
                                isinstance(_settings[sset][option][0], tuple)):
                            _settings[sset][option].append(tuple((eval(value))))
                        else:
                            _settings[sset][option].append(value)
                    else:
                        _settings[sset][option] = \
                                type(_settings[sset][option])(value)
    f.close()
    for x in _settings:
        for y in _settings[x]:
            if isinstance(_settings[x][y], list):
                if (False,) in _settings[x][y]:
                    _settings[x][y].remove((False,))


conf_file = os.path.expanduser('~/.papageorge.conf')
if os.path.isfile(conf_file):
    parse_config(conf_file)

class SettingsSet(object):
    def __init__(self, sset):
        self.sset = sset
    def __getattr__(self, name):
        return _settings[self.sset][name]

for name in _settings.keys():
    globals()[name] = SettingsSet(name)

