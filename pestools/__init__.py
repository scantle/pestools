"""
Utilities for working with PEST output.
 
Modules:

* ``pest`` - Base class
* ``res`` - Class for working with PEST residuals files
* ``rei`` - Aggregates information from multiple interim residuals (.rei) files
* ``parsen`` - Class for working with parameter sensitivities
* ``plots`` - Classes for generating plots
 
Base and PEST control file classes
**********************************
 
.. automodule:: pst
 
Residuals Class
***************
 
.. automodule:: res

.. autosummary::

	

REI Class
*********
 
.. automodule:: rei

Parameter Sensitivity Class
***************************
 
.. automodule:: parsen

Plotting Classes
****************
 
.. automodule:: rei

"""
from pest import Pest
from parsen import ParSen
from Cor import Cor
from res import Res
#from identpar import IdentPar

