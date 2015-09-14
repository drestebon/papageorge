Papageorge
==========

A simple client for the `Free Internet Chess Server (FICS)`_

.. _`Free Internet Chess Server (FICS)`: http://freechess.org/ 

Dependencies
------------

To run Papageorge you will need:

    1. Python3_
    2. PyGObject_
    3. urwid_

.. _Python3: https://www.python.org/ 
.. _PyGObject: http://wiki.gnome.org/action/show/Projects/PyGObject
.. _urwid: http://urwid.org/

Installation
------------

First, get the source code with:

.. code-block:: bash

    $ git clone https://github.com/drestebon/papageorge.git

and install with

.. code-block:: bash

    # python setup.py install

Usage
-----

Run it with:

.. code-block:: bash

    $ papageorge [username password]

If you don't provide any arguments you will be asked for your login
information.

Papageorge has three parts, no more, no less. I use Papageorge with a tiling
window manager, so it is convenient to have one window for each of the
following:

The Console
...........

.. image:: http://saveimg.com/images/2015/09/14/TFeCS4jkA.png

Here you can directly enter fics commands. There are some special
commands for the interface, which start with a ``%``. The only one
worth noticing is the ``%c`` which establishes a connection with
freechess.org.  The console highlights your name and moves in the SAN
notation. When you click on a move, it will be sent to the fics. I use
this when examining a game with the help of Analysisbot, to go through
the move it proposes. When you click on the handle of a user, a dialog
with some actions (for now match and tell) will pop up. I use it with
the *who* command to match my peers.  You can also press F5 to open the
Seek Graph.

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

============  ========================================
Key           Action
============  ========================================
F5            Launch the Seek Graph window
Escape        Launch the actions dialog
f             Flip board
b             Toggle border with rank-file coordinates
Right         Fast-forward a move
Left          Rewind a move
Up            Fast-forward many moves
Down          Rewind many moves
<Shift>Up     Fast-forward to the end of the game
<Shift>Down   Rewind to the beginning of the game
============  ========================================

You can bind keys to issue fics commands in the configuration file.

Configuration file
..................

You can customize Papageorge with ``~/.papageorge.conf``. The provided model,
includes the default colors for the board and some useful key-bindings.
