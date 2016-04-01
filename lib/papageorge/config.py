# config - configure papageorge with ~/.papageorge.conf

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

import os, datetime

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
                'auto_replace'          : 'on',
                'accel_fforward'        : '<Shift>Up',
                'accel_frewind'         : '<Shift>Down',
                'accel_forward'         : 'Up',
                'accel_rewind'          : 'Down',
                'accel_prev_move'       : 'Left',
                'accel_next_move'       : 'Right',
                'accel_flip'            : '<Control>f',
                'accel_promote'         : '<Control>Tab',
                'accel_border'          : '<Control>b',
                'accel_board_commands'  : 'Escape',
                'accel_seek_graph'      : 'F5',
                'accel_movesheet'       : '<Control>space',
                'handle_justify'        : 'right'
            },
            'movesheet' : {
                'bg' :          '#343434',
                'curr_move'   : '#ffffff',
                'curr_move_n' : '#f2f2f2',
                'curr_line'   : '#e5e5e5',
                'curr_line_n' : '#d9d9d9',
                'off'         : '#cccccc',
                'off_n'       : '#bfbfbf'
            },
            'console' : {
                'default_color'         : '#999',
                'game_end_color'        : '#eee',
                'echo_color'            : '#aa0',
                'echo_high_color'       : '#ee0',
                'handle_mouse'          : True,
                'highlight'             : [(False,)],
                'palette'               : [],
                'command'               : [(False,)],
                'color'                 : dict()
            },
            'general' : {
                'log'                   : False,
                'startup_command'       : ['style 12',
                                           'iset gameinfo',
                                           'set interface papageorge 0.1'],
                'connection_test_timeout' : 0,
                'timeseal'              : False
            }
        }

fics_user = ''

COMMENT_CHAR = ';'
OPTION_CHAR =  '='

def parse_bool(txt):
    if txt.lower() in ['true', 'on']:
        return True
    elif txt.lower() in ['false', 'off']:
        return False
    else:
        return txt

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
                        _settings[sset][option] = parse_bool(value)
                    elif isinstance(_settings[sset][option], list):
                        if (len(_settings[sset][option]) and
                                isinstance(_settings[sset][option][0], tuple)):
                            _settings[sset][option].append(tuple((eval(value))))
                        else:
                            _settings[sset][option].append(value)
                    elif isinstance(_settings[sset][option], dict):
                        key, val = tuple((eval(value)))
                        _settings[sset][option].update({key : val})
                    else:
                        _settings[sset][option] = \
                                type(_settings[sset][option])(value)
    f.close()

conf_file = os.path.expanduser('~/.papageorge.conf')
if os.path.isfile(conf_file):
    parse_config(conf_file)

for x in _settings:
    for y in _settings[x]:
        if isinstance(_settings[x][y], list):
            if (False,) in _settings[x][y]:
                _settings[x][y].remove((False,))

_default_highlights_re = {
  'announcements' : '^\s+\*\*ANNOUNCEMENT\*\*',
  '-->'           : '^--> (?P<handle>\w+)(\(\w+\))*',
  'tells'         : '^(?P<handle>\w+)(\([\w\*]+\))* tells you: ',
  'shouts'        : '^(?P<handle>\w+)(\([\w\*]+\))* (c-)*shouts: ',
  'chat'          : '^(?P<handle>\w+)(\([\w\*]+\))*\(\d+\): ',
  'channel'       : '^(?P<handle>\w+)(\([\w\*]+\))*\({}\): ',
  'user'          : '^(?P<handle>{})(\([\w\*]+\))* tells you: ',
  'kibitzes'      : '^(?P<handle>\w+)(\([\w\*]+\))*\[(?P<id>\d+)\] kibitzes: ',
  'whispers'      : '^(?P<handle>\w+)(\([\w\*]+\))*\[(?P<id>\d+)\] whispers: ',
  'says'          : '^(?P<handle>\w+)(\([\w\*]+\))*\[(?P<id>\d+)\] says: ',
}

for i, x in enumerate(_settings['console']['highlight']):
    if x[0] in _default_highlights_re :
        _settings['console']['highlight'][i] = \
                            (_default_highlights_re[x[0]], x[1])
        x = _settings['console']['highlight'][i]
    if x[0].split()[0] in ['channel', 'user']:
        _settings['console']['highlight'][i] = \
        (_default_highlights_re[x[0].split()[0]].format(x[0].split()[1]), x[1])
        x = _settings['console']['highlight'][i]
    if x[1] in _settings['console']['color'] :
        _settings['console']['highlight'][i] = \
                            (x[0], _settings['console']['color'][x[1]])

if _settings['general']['timeseal']:
    _settings['general']['timeseal'] = \
          os.path.abspath(os.path.expanduser(_settings['general']['timeseal']))

class SettingsSet(object):
    def __init__(self, sset):
        self.sset = sset
    def __getattr__(self, name):
        return _settings[self.sset][name]

for name in _settings.keys():
    globals()[name] = SettingsSet(name)


FICS_COMMANDS = [
    'abort', 'accept', 'addlist', 'adjourn', 'alias', 'allobservers', 'assess',
    'backward', 'bell', 'best', 'boards', 'bsetup', 'bugwho', 'cbest',
    'clearmessages', 'convert_bcf', 'convert_elo', 'convert_uscf', 'copygame',
    'crank', 'cshout', 'date', 'decline', 'draw', 'examine', 'finger', 'flag',
    'flip', 'fmessage', 'follow', 'forward', 'games', 'gnotify', 'goboard',
    'handles', 'hbest', 'help', 'history', 'hrank', 'inchannel', 'index',
    'info', 'it', 'jkill', 'jsave', 'kibitz', 'limits', 'llogons', 'logons',
    'mailhelp', 'mailmess', 'mailmoves', 'mailoldmoves', 'mailsource',
    'mailstored', 'match', 'messages', 'mexamine', 'moretime', 'moves', 'news',
    'next', 'observe', 'oldmoves', 'open', 'password', 'pause', 'pending',
    'pfollow', 'play', 'pobserve', 'promote', 'pstat', 'qtell', 'quit', 'rank',
    'refresh', 'resign', 'resume', 'revert', 'say', 'seek', 'servers', 'set',
    'shout', 'showlist', 'simabort', 'simallabort', 'simadjourn',
    'simalladjourn', 'simgames', 'simmatch', 'simnext', 'simobserve',
    'simopen', 'simpass', 'simprev', 'smoves', 'smposition', 'sought',
    'sposition', 'statistics', 'stored', 'style', 'sublist', 'switch',
    'takeback', 'tell', 'time', 'unalias', 'unexamine', 'unobserve', 'unpause',
    'unseek', 'uptime', 'ustat', 'variables', 'whisper', 'who', 'withdraw',
    'xkibitz', 'xtell', 'xwhisper', 'znotify' ]

FICS_HELP = [
    '_index', 'abort', 'abuse', 'academy', 'accept', 'addlist', 'addresses',
    'adjourn', 'adjournments', 'adjudicate', 'adjudication', 'adm_app',
    'adm_info', 'adm_new', 'admins', 'alias', 'allobservers', 'assess',
    'atomic', 'audiochat', 'avail_vars', 'backward', 'bclock', 'bell', 'best',
    'blind', 'blindfold', 'blindh', 'blitz', 'block_codes', 'bname', 'boards',
    'brating', 'bsetup', 'bughouse', 'bughouse_strat', 'bugreport', 'bugwho',
    'busy', 'ca', 'category', 'cbest', 'censor', 'chan_1', 'chan_4', 'channel',
    'channel_list', 'channels', 'chess_adviser', 'chess_advisor',
    'clearmessage', 'clearmessages', 'clock', 'clocks', 'clrsquare', 'cls',
    'cls_info', 'command', 'commands', 'commit', 'computer_app',
    'computer_list', 'computers', 'confidentiality', 'convert_bcf',
    'convert_elo', 'convert_uscf', 'copygame', 'crank', 'crazyhouse',
    'crazyhouse_strat', 'credit', 'crstat', 'cshout', 'csnewse', 'csnewsf',
    'csnewsi', 'csnewsp', 'csnewst', 'date', 'decline', 'disclaimer',
    'disconnection', 'draw', 'eco', 'eggo', 'email', 'etime', 'examine', 'exl',
    'fen', 'fics_faq', 'fics_lingo', 'finger', 'flag', 'flip', 'fmessage',
    'follow', 'formula', 'forward', 'fr', 'fr_rules', 'ftp_hints', 'games',
    'games', 'getgame', 'getgi', 'getpi', 'ginfo', 'glicko', 'gnotify',
    'goboard', 'handle', 'handles', 'hbest', 'help', 'highlight', 'history',
    'hrank', 'hrstat', 'hstat', 'icsdrone', 'idlenotify', 'inchannel', 'index',
    'indexfile', 'inetchesslib', 'info', 'intellegence', 'interfaces',
    'intro_analysis', 'intro_basics', 'intro_general', 'intro_information',
    'intro_moving', 'intro_playing', 'intro_settings', 'intro_talking',
    'intro_welcome', 'irc_help', 'iset', 'it', 'iv_allresults', 'iv_atomic',
    'iv_audiochat', 'iv_block', 'iv_boardinfo', 'iv_compressmove',
    'iv_crazyhouse', 'iv_defprompt', 'iv_extascii', 'iv_extuserinfo', 'iv_fr',
    'iv_gameinfo', 'iv_graph', 'iv_list', 'iv_lock', 'iv_pendinfo',
    'iv_seekinfo', 'iv_seekremove', 'iv_startpos', 'ivariables', 'jkill',
    'journal', 'jsave', 'kibitz', 'kiblevel', 'lag', 'lecture1', 'lessons',
    'lightning', 'limits', 'links', 'lists', 'llogons', 'logons', 'losers',
    'losers_chess', 'mailhelp', 'mailmess', 'mailmoves', 'mailoldmoves',
    'mailstored', 'mamer', 'manual_usage', 'manual_vars', 'match',
    'meeting_1_followup', 'meeting_1_long', 'meeting_1_short',
    'meetings_index', 'messages', 'mexamine', 'moretime', 'motd', 'motd_fri',
    'motd_help', 'motd_mon', 'motd_sat', 'motd_sun', 'motd_thu', 'motd_tue',
    'motd_wed', 'moves', 'mule', 'new_features', 'newbie', 'news', 'next',
    'noescape', 'noplay', 'notes', 'notify', 'observe', 'odds', 'oldmoves',
    'oldpstat', 'open', 'partner', 'password', 'pause', 'pending', 'pfollow',
    'pgn', 'ping', 'play', 'pobserve', 'powericsfaq', 'prefresh', 'primary',
    'private', 'promote', 'pstat', 'ptell', 'ptime', 'qtell', 'quit', 'rank',
    'rating_changes', 'ratings', 'rcopygame', 'rd', 'refresh', 'register',
    'relay', 'relay_operator', 'rematch', 'replay', 'resign', 'result',
    'resume', 'revert', 'rfollow', 'rmatch', 'robofics', 'robserve', 'rstat',
    'sabort', 'say', 'sdraw', 'seek', 'servers', 'set', 'setup', 'shout',
    'shout_quota', 'showadmins', 'showlist', 'showsrs', 'simabort',
    'simadjourn', 'simallabort', 'simalladjourn', 'simgames', 'simmatch',
    'simnext', 'simobserve', 'simopen', 'simpass', 'simprev', 'simuls',
    'skype', 'smoves', 'smposition', 'sought', 'spending', 'sposition', 'sr',
    'sr_info', 'standard', 'statistics', 'stats', 'stc', 'stored', 'style',
    'style12', 'sublist', 'suicide_chess', 'summon', 'switch', 'system_alias',
    'takeback', 'team', 'teamgames', 'tell', 'time', 'timeseal',
    'timeseal_mac', 'timeseal_os2', 'timeseal_unix', 'timeseal_windows',
    'timezones', 'tm', 'tomove', 'totals', 'totals_info', 'tournset',
    'town_meetings', 'townmtg1', 'unalias', 'unexamine', 'unobserve',
    'unpause', 'unseek', 'untimed', 'uptime', 'uscf', 'uscf_faq', 'ustat',
    'v_autoflag', 'v_automail', 'v_availinfo', 'v_availmax', 'v_availmin',
    'v_bell', 'v_bugopen', 'v_chanoff', 'v_cshout', 'v_ctell', 'v_echo',
    'v_flip', 'v_formula', 'v_gin', 'v_height', 'v_highlight', 'v_inc',
    'v_interface', 'v_jprivate', 'v_kibitz', 'v_kiblevel', 'v_language',
    'v_mailmess', 'v_messreply', 'v_notakeback', 'v_notifiedby', 'v_open',
    'v_pgn', 'v_pin', 'v_private', 'v_prompt', 'v_provshow', 'v_ptime',
    'v_rated', 'v_ropen', 'v_seek', 'v_shout', 'v_silence', 'v_simopen',
    'v_style', 'v_tell', 'v_time', 'v_tolerance', 'v_tourney', 'v_tzone',
    'v_unobserve', 'v_width', 'variables', 'wclock', 'webpage', 'whenshut',
    'whisper', 'who', 'wild', 'withdraw', 'wname', 'wrating', 'xkibitz',
    'xtell', 'xwhisper', 'zhouse', 'znotify' ]

FICS_HANDLES = list()

def update_handle(hdl):
    if hdl in FICS_HANDLES:
        FICS_HANDLES.insert(0, FICS_HANDLES.pop(FICS_HANDLES.index(hdl)))
    else:
        FICS_HANDLES.insert(0, hdl)

TRANS_TABLE = str.maketrans({ 'á' : "'a", 'é' : "'e", 'í' : "'i", 'ó' : "'o",
                              'ú' : "'u", 'ä' : "ae", 'ö' : "oe", 'ü' : "ue",
                              'ø' : "/o", 'å' : "aa", 'æ' : "ae", 'ß' : "ss",
                              'â' : "^a", 'ê' : "^e", 'î' : "^i", 'ô' : "^o",
                              'û' : "^u", 'Á' : "'A", 'É' : "'E", 'Í' : "'I",
                              'Ó' : "'O", 'Ú' : "'U", 'Ä' : "AE", 'Ö' : "OE",
                              'Ü' : "UE", 'Ø' : "/O", 'Å' : "AA", 'Æ' : "AE",
                              'Â' : "^A", 'Ê' : "^E", 'Î' : "^I", 'Ô' : "^O",
                              'Û' : "^U", 'ñ' : "~n", 'Ñ' : "~N", })

from glob import glob

_here = os.path.dirname(os.path.abspath(__file__))
figPath = os.path.abspath(os.path.join(_here, 'JinSmart'))
fsets = [int(os.path.basename(x)) for x in glob(figPath+'/[0-9]*')]
fsets.sort()

logfd = None

def log(data, sent=False, internal=False):
    if logfd:
        dstr = datetime.datetime.strftime(datetime.datetime.now(),
                                      '%Y-%m-%d %H:%M:%S ')
        direction = '> ' if sent else '< '
        direction = '=' if internal else direction
        logfd.write(dstr+direction+str(data)+'\n')
        logfd.flush()

cli = None
gui = None

block12 = list()

