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

    # python setup.py install

You can also run it directly from the source directory.

If you want, you can copy the configuration file ``papageorge.conf`` in your
home directory and fit it to your needs.

Archlinux
.........

Papageorge is available at Archlinux's AUR_.

.. _AUR: https://aur.archlinux.org/packages/papageorge-git/

Other
.....

In Debian 8.2 and Ubuntu 15.04 the dependencies are fulfilled installing ``python3-urwid``.


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

.. image:: http://saveimg.com/images/2015/09/14/TFeCS4jkA.png

Here you can directly enter fics commands. 

===============     =====================================================
Command             Action
===============     =====================================================
``%c``              Connect to fics
``%q``              quit
``F5``              Launch the Seek Graph window
Click on handle     Open actions dialog (match, tell, finger)
Click on move       Issue it (usefull with AnalysisBot)
Shift               Back down to normal mouse behaviour (copy and, f.ex.)
===============     =====================================================


The Seek Graph
..............

.. image:: http://saveimg.com/images/2015/09/14/By0aQO.png

Here the available seeks are displayed. Squares are computers, circles
are humans. The light grey ones are rated games, the dark grey ones are
not. Click to match.

The Board
.........

.. image:: http://saveimg.com/images/2015/09/14/bGd7t.png

Here you play, examine or observe games. Some keys are bound per
default:

=============== ========================================
Key             Action
=============== ========================================
``Escape``      Launch the actions dialog
``Tab``         Set promotion
``<Control>f``  Flip board
``<Control>b``  Toggle border with rank-file coordinates
``Right``       Fast-forward a move
``Left``        Rewind a move
``Up``          Fast-forward many moves
``Down``        Rewind many moves
``<Shift>Up``   Fast-forward to the end of the game
``<Shift>Down`` Rewind to the beginning of the game
``F5``          Launch the Seek Graph window
non-binded keys Write to console
=============== ========================================

You can change these bindings and introduced further bindings in the
configuration file.

Configuration file
..................

You can customize Papageorge with ``~/.papageorge.conf``. The provided model,
includes the default colors for the board and the console and some useful
key-bindings.

