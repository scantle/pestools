from .FileReader import FileReader
import numpy as np
import pandas as pd

class Rec(object):
    """ Rec Class

    Author: Leland Scantlebury

    Parameters
    ----------
        rec_file: str

    Attributes
    ----------
        run_mode: str
        pest_version: float
        nParam: int
        nAdjParam
        nGroups
        nObs
        nPrior
        obs: DataFrame
        obsgroups: Series
        nobsgroups: int
        phi: list
        obs_contribution: DataFrame
        param: DataFrame
        _iter: int
        iter_variance: list
        summary: DataFrame
    Notes
    ----------
    Only tested on Regularisation and Parameter estimation modes
    """

    def __init__(self, rec_file):

        self.phi = []
        self.lambdas = []
        self.obs_contribution = None
        self._iter = 0

        with FileReader(rec_file) as rec:
            # Get PEST Version
            rec.find_phrase('version', rewind=True)
            self.pest_version = float(rec.get_cleanline(2))
            # Get run mode
            rec.find_phrase('PEST run mode')
            rec.nextline()
            self.run_mode = rec.get_cleanline()

            # Get case dimensions
            rec.find_phrase('Case dimensions')
            rec.nextline()
            names = ['nParam','nAdjParam','nGroups','nObs','nPrior']
            for item in names:
                val = rec.get_cleanline().split()
                val = int(val[val.index(':')+1])
                setattr(self, item, val)

            # Get observations (mainly for a count of groups...)
            rec.find_phrase('Observations:')
            rec.nextline()
            rec.skiplines(1)
            names = ['Observation name', 'Observation', 'Weight', 'Group']
            self.obs = rec.get_DataFrame(manual_rewind=True, nrows=self.nObs,
                                         delim_whitespace=True, names=names)
            self.obsgroups = self.obs['Group'].unique()
            self.nobsgroups = len(self.obsgroups)

            # Skipping a billion things, then...

            # Get opt record
            rec.find_phrase('OPTIMISATION RECORD', case_sens=True)
            rec.nextline()
            rec.skiplines(1)  # INITIAL CONDITIONS:
            self._pre_iteration(rec)
            self._add_iteration(rec)
            # The read adding loop begins!
            while True:
                try:
                    rec.find_phrase('OPTIMISATION ITERATION NO', case_sens=True)
                    self.modelcalls = rec.get_cleanline(-1)
                    self._pre_iteration(rec)
                    self._add_iteration(rec)
                except EOFError:
                    break
                    pass
            # Cleanup
            self._iter -= 1
            print('End of Rec file reached.')
            print('\tIterations {}'.format(self._iter))
            # Calculate variance for each iteration
            self.calc_variance()

    def _pre_iteration(self, rec):
        """
        To deal with the little differences in Rec file types based on run mode.
        """
        if self.run_mode=='Regularisation mode':
            if self._iter == 0:
                self.weight_factor = [float(rec.get_cleanline(-1))]
                self.meas_obj_func = [float(rec.get_cleanline(-1))]
                self.reg_obj_func = [float(rec.get_cleanline(-1))]
                rec.find_phrase('Sum of squared weighted residuals', rewind=True)
            else:
                self.weight_factor.append(float(rec.get_cleanline(-1)))
                self.meas_obj_func.append(float(rec.get_cleanline(-1)))
                self.reg_obj_func.append(float(rec.get_cleanline(-1)))
                rec.find_phrase('Starting phi', rewind=True)

    def _add_iteration(self, rec):
        # Reading
        current_phi = rec.get_cleanline(-1)
        contributions = []
        for item in self.obsgroups:
            contributions.append(rec.get_cleanline(-1))
        # Lambdas not present in initial
        if self._iter >0: self._read_lambdas(rec)
        rec.find_phrase('Current parameter values')
        names = ['Parameter', 'Iteration ' + str(self._iter)]
        if self._iter == 0:
            names[1] = 'Initial'
        current_pvalues = rec.get_DataFrame(manual_rewind=True, nrows=self.nParam, usecols=[0, 1],
                                            delim_whitespace=True, names = names, index_col=0)
        # Storage
        # We could check the iteration counter (_iter) or if the variables are set. Either way.
        self.phi.append(current_phi)
        if self.obs_contribution is None:
            self.obs_contribution = pd.DataFrame(data=contributions, columns=['Initial'])
        else:
            self.obs_contribution[self._iter] = contributions
        if self._iter == 0:
            self.param = current_pvalues
        else:
            self.param[names[1]] = current_pvalues[names[1]]

        self._iter +=1

    def _read_lambdas(self, rec):
        """
        Gets best Marquardt lambda at end of iteration.
        """
        current_lambdas = []
        corresponding_phi = []
        # PEST tests at least two lambdas
        for i in range(0,2):
            rec.find_phrase('Lambda =', rewind=True)
            current_lambdas.append(float(rec.get_cleanline(2)))
            corresponding_phi.append(float(rec.get_cleanline(2)))
        # Then it might test more. Must be careful to avoid searching entire document to EOF
        # Another option is testing for PEST's lambda search calculations using settings specified
        # in the "Control Settings" section
        while True:
            #rec.find_phrase('lambda', case_sens=False, rewind=True)
            last_pos = rec.fileobject.tell()
            line = rec.get_cleanline()
            if 'No more lambdas' in line: break  # End in "original" PEST
            if 'Current' in line:                # End in PEST_HP
                rec.fileobject.seek(last_pos)
                break
            if 'lambda =' in line:
                current_lambdas.append(float(line.split()[2]))
                # Get Phi
                phi = rec.get_cleanline(2)
                if phi == 'cannot':  # Model run failure
                    corresponding_phi.append(np.nan)
                else:
                    corresponding_phi.append(float(phi))
        # May be worth it someday to keep some kind of record of all lambdas, but we're just going
        # for the one with the lowest phi
        lowest_lambda = current_lambdas[corresponding_phi.index(min(corresponding_phi))]
        self.lambdas.append(lowest_lambda)

    def calc_variance(self):
        # Ensure there were iterations
        if self._iter > 0:
            self.iter_variance = []
            for i in range(1,self._iter + 1):
                diff = self.param['Iteration '+ str(i)] - self.param['Initial']
                self.iter_variance.append(diff.var(ddof=0))

    @property
    def summary(self):
        # Ensure there were iterations
        if self._iter > 0:
            sumdict = {'Iteration': self.param.columns,
                       'Phi': self.phi,
                       'Variance': [pd.np.nan] + self.iter_variance}
            if self.run_mode=='Regularisation mode':
                sumdict['Multiplier Weight'] = self.weight_factor
            summary = pd.DataFrame.from_dict(sumdict)
            return summary
        else:
            print("No Iterations - no summary table to produce.")
