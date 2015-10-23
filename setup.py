#!/usr/bin/python

from distutils.core import setup

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 3',
    'Topic :: Games/Entertainment :: Board Games',
    ]

setup (
    name             = 'papageorge',
    version          = '0.1.1',
    author           = 'drestebon',
    author_email     = 'sanestebon@gmail.com',
    classifiers      = CLASSIFIERS,
    keywords         = 'python gtk chess fics board linux',
    description      = 'Simple client for the Free Internet Chess Server',
    license          = 'GPL3',
    url              = 'http://github.com/drestebon/papageorge',
    package_dir      = {'': 'lib'},
    packages         = ['papageorge'],
    scripts          = ['papageorge'],
    package_data     = {'papageorge' : ['JinSmart/*/*']},
    data_files       = [('share/applications', ['papageorge.desktop']),
			('share/icons/hicolor/24x24/apps', ['papageorge.png']),
			('share/icons/hicolor/scalable/apps', ['papageorge.svg'])]
                       
)
