"""
This is a work in progress!

Modules:

* ``pest`` - Base class
* ``res`` - Class for working with PEST residuals files
* ``rei`` - Aggregates information from multiple interim residuals (.rei) files
* ``rec`` - Class for reading and getting simple information/stats from record (.rec) files
* ``parsen`` - Class for working with parameter sensitivities
* ``plots`` - Classes for generating plots
* ``maps`` - Classes for generating maps
* ``FileReader`` - Class for reading [annoying, long] text files
 
PEST class
**********************************
 
.. automodule:: pst
 
Residuals Class
***************
 
.. automodule:: res

.. autosummary::

REI Class
*********
 
.. automodule:: rei

REC Class
*********

.. automodule:: rec


Parameter Sensitivity Class
***************************
 
.. automodule:: parsen

Plotting Class
****************
 
.. automodule:: plots

Mapping Class
****************
 
.. automodule:: maps

FileReader Class
****************

.. automodule:: FileReader

"""
from .pest import Pest
from .parsen import ParSen
from .Cor import Cor
from .res import Res
from .rei import Rei
from .rec import Rec
from .identpar import IdentPar
from .plots import *
from .maps import *
from .mat_handler import *
from .pst_handler import pst
from .FileReader import FileReader
