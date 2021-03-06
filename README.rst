Papageorge
==========

A simple client for the `Free Internet Chess Server (FICS)`_

.. _`Free Internet Chess Server (FICS)`: http://freechess.org/ 

Dependencies
------------

To run Papageorge you will need:

    1. Python3_
    2. PyGObject_
    3. Pycairo_
    4. urwid_

.. _Python3: https://www.python.org/ 
.. _PyGObject: http://wiki.gnome.org/action/show/Projects/PyGObject
.. _Pycairo: http://www.cairographics.org/pycairo
.. _urwid: http://urwid.org/

Installation
------------

First, get the source code with:

.. code-block:: bash

    $ git clone https://github.com/drestebon/papageorge.git

and install with

.. code-block:: bash

    $ sudo python setup.py install

You can then create a launcher for papageorge. You can also run it directly
from the source directory.

If you want, you can copy the configuration file ``papageorge.conf`` in your
home directory and fit it to your needs (more details below).

Archlinux
.........

Papageorge is available at Archlinux's AUR_.

.. _AUR: https://aur.archlinux.org/packages/papageorge-git/

Mac OS X
........

In Mac OS PyGObjec_ is available through Homebrew_ and urwid_ through pip:

.. _Homebrew: https://brew.sh

.. code-block:: bash

    $ brew install pygobject3 --with-python3
    $ pip3 install urwid

Other
.....

In Debian 8.2 and Ubuntu 15.04 you can create a ``.deb`` file with
``create_deb.sh``. You may need to install ``python3-stdeb``:

.. code-block:: bash

    $ sudo apt-get install python3-stdeb

Then you create the ``.deb`` package running:

.. code-block:: bash

    $ ./create_deb.sh

on the papageorge source directory and install it with:

.. code-block:: bash

    $ sudo dpkg -i deb_dist/python3-papageorge_0.1.1-1_all.deb

if it fails on missing dependencies, install them with:

.. code-block:: bash

    $ sudo apt-get -f install

and you should be ready to go.

Usage
-----

Run it with:

.. code-block:: bash

    $ papageorge [username password]

If you don't provide any arguments you will be asked for your login
information.

Papageorge has three parts, no more, no less. Three is the number of parts you
will meet in papageorge and the number of parts in papageorge is three. I use
Papageorge with a tiling window manager, so it is convenient to have one window
for each of the following three parts:

The Console
...........

.. image:: /../screenshots/console.png

Here you can directly enter FICS commands. 

=========================== ===============================================================================================================
Command                     Action
=========================== ===============================================================================================================
``%c``                      Connect to FICS
``%q``                      Quit
``%M [U [D [time [inc]]]]`` Challenge available users with a rating ``U`` and ``D`` points above and below you. Defaults are ``50 50 5 10``
``F5``                      Launch the Seek Graph window
Click on handle             Open actions dialog (match, tell, finger)
Click on move               Issue it (useful with AnalysisBot)
``<Shift>``                 Back down to normal mouse behaviour (select to copy , f.ex.)
``Tab`` and ``<Shift>Tab``  Auto-complete commands and user handles
``up`` and ``down``         Browse command history. If something is tipped, search for matching commands
``Esc``                     Clear the command line
=========================== ===============================================================================================================


The Seek Graph
..............

.. image:: /../screenshots/seekgraph.png

Here the available seeks are displayed. Squares are computers, circles
are humans. The light grey ones are rated games, the dark grey ones are
not. Click to match.

The Board
.........

.. image:: /../screenshots/board.png

Here you play, examine or observe games. Some keys are bound per
default:

================== ========================================
Key                Action
================== ========================================
``Escape``         Launch the actions dialog
``<Control>Tab``   Set promotion
``<Control>f``     Flip board
``<Control>b``     Toggle border with rank-file coordinates
``<Control>space`` Toggle the move sheet
``Right``          Fast-forward a move
``Left``           Rewind a move
``Up``             Fast-forward many moves
``Down``           Rewind many moves
``<Shift>Up``      Fast-forward to the end of the game
``<Shift>Down``    Rewind to the beginning of the game
``F5``             Launch the Seek Graph window
non-binded keys    Send to console
================== ========================================

You can change these bindings and add new ones in the configuration file.

Right clicking the board pops up a menu with different actions, such as
resigning or saving the game to a ``.pgn`` file, among others.

Configuration file
..................

You can customize Papageorge with ``~/.papageorge.conf``. The provided model,
includes the default colors for the board and the console and some useful
key-bindings.

Timeseal
........

To use timeseal get the executable_ and then configure it properly in
``~/.papageorge.conf``.

.. _executable: http://sourceforge.net/projects/scidvspc/files/support%20files/timeseal.Linux-i386.gz/download
