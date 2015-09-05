Papageorge
==========

A simple client for the Free Internet Chess Server (FICS)

Dependencies
------------

To run papageorge you will need:

    1. Python3_
    2. PyGObject_
    3. urwid_

.. _Python3: https://www.python.org/ 
.. _PyGObjec: http://wiki.gnome.org/action/show/Projects/PyGObject
.. _urwid: http://urwid.org/

Installation
------------

First, get the source code using:

.. code-block:: bash

    $ git clone https://github.com/drestebon/papageorge.git

and then install with

.. code-block:: bash

    # python setup.py install

Usage
-----

Run it with:

.. code-block:: bash

    $ papageorge [username password]

Keybindings
...........

Console:

====  =====================
Key   Action
====  =====================
<f5>  Open SeekGraph window
====  =====================

Board:

============    ========================================
Key             Action
============    ========================================
<Shift-Down>    Toggle border with rank-file coordinates
<f5>            Open SeekGraph window
<Esc>           Open action dialog
f               Flip board
b               Toggle border with rank-file coordinates
<Right>         Fast-forward a move
<Left>          Rewind a move
<Up>            Fast-forward many moves
<Down>          Rewind many moves
<Shift-Up>      Fast-forward to the end of the game
<Shift-Down>    Rewind to the beggining of the game
g               say Hallo!
a               tell Analysisbot obsme
A               tell Analysisbot stop
============    ========================================

