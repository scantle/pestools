from .FileReader import FileReader
import numpy as np
import pandas as pd

class Sen(object):
    """ Sen Class

    Author: Leland Scantlebury

    Parameters
    ----------
        sen_file: str

    Attributes
    ----------
        nParam: int, number of parameters
        nParamGroups: int, number of unique groups
        param_groups: list, unique parameter groups
        _iter: int, current iteration during read
        nIterations: int, number of iterations
        iter_sens: DataFrame, parameter sensitives for each iteration
        iter_vals: DataFrame, parameter values for each iteration

    Notes
    ----------
    Only tested with output from PEST_HP version 17.05
    """

    def __init__(self, sen_file):

        self.nParam = 0
        self.nGroups = 0
        self._iter = 0

        with FileReader(sen_file) as sen:
            # Sensitivities from each iteration
            self._read_iterations(sen)

            # Process new data
            print('SEN: Read parameters and sensitivities for {} iterations'.format(self._iter))
            self.nIterations = self._iter
            self.nParam = self.iter_sens.shape[0]
            self.param_groups = self.iter_sens['Param_Group'].unique()
            self.nParamGroups = len(self.param_groups)

            # Sensitivities for each observation group
            self._read_obs_groups(sen)

    def _read_iterations(self, sen):
        while True:
            last_pos = sen.fileobject.tell()
            try:
                sen.find_phrase('iteration')
            except EOFError:
                sen.fileobject.seek(last_pos)
                break
                pass
            self._iter += 1
            sen.skiplines(1) # Skip header
            if self._iter == 1:
                # Don't know nparam yet
                self.nParam = sen.get_datadist()  # Assumes 1 per line
                # Get initial dataframes
                names = ['Parameter', 'Param_Group', 'Value_1', 'Sensitivity_1']
                partemp = sen.get_DataFrame(manual_rewind=True, nrows=self.nParam,
                                    delim_whitespace=True, names = names, index_col=0)
                self.iter_sens = partemp.drop('Value_1', axis=1).copy()
                self.iter_vals = partemp.drop('Sensitivity_1', axis=1).copy()
            else:
                names = ['Parameter', 'Value_{}'.format(self._iter), 'Sensitivity_{}'.format(self._iter)]
                partemp = sen.get_DataFrame(manual_rewind=True, nrows=self.nParam, usecols=[0, 2,3],
                                    delim_whitespace=True, names = names, index_col=0)
                self.iter_vals[names[1]] = partemp[names[1]]
                self.iter_sens[names[2]] = partemp[names[2]]

    def _read_obs_groups(self, sen):
        while True:

            # Get group name (On last round, will return 'All')
            name = self._strip_obs_group_name(sen)

            # Check if has non-zero weight obs/prior info
            if(self._has_obs(sens)):
                # Read in sensitivies

            # Check if done
            if name == 'All': break