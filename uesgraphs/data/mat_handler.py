"""
This module handles Dymola .mat result files.

Code History and Attribution:
---------------------------
1. Original Implementation:
   - Author: Kevin Davies
   - Organization: Hawaii Natural Energy Institute (HNEI) and Georgia Tech Research Corporation (GTRC)
   - Copyright: 2010-2014
   - License: BSD
   - link: https://github.com/kdavies4/ModelicaRes/tree/master

2. First Modification:
   - Project: ebcpy
   - Modification: Updated for compatibility with newer Python versions
   - Date: 2019 - 2024
   - Changes made: Removal of matplotlib and natu dependencies
   - link: https://github.com/RWTH-EBC/ebcpy/blob/master/ebcpy/modelica/simres.py

3. Current Version:
   - Extracted and adapted from ebcpy version
   - Date: 23.01.2025
   - Purpose: Minimise dependencies in uesgraphs
   - Changes made: None

Original Copyright Notice:
------------------------

# Copyright (c) 2010-2014, Kevin Davies, Hawaii Natural Energy Institute (HNEI),
# and Georgia Tech Research Corporation (GTRC).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of Georgia Tech Research Corporation nor the names of
#       its contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#     * This software is controlled under the jurisdiction of the United States
#       Department of Commerce and subject to Export Administration Regulations.
#       By downloading or using the Software, you are agreeing to comply with
#       U. S. export controls.  Diversion contrary to law is prohibited.  The
#       software cannot be exported or reexported to sanctioned countries that
#       are controlled for Anti-Terrorism (15 CFR Part 738 Supplement 1) or to
#       denied parties, http://beta-www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern.
#       EAR99 items cannot be exported or reexported to Iraq for a military
#       purpose or to a military end-user (15 CFR Part 746.3).  Export and
#       reexport include any release of technology to a foreign national within
#       the United States.  Technology is released for export when it is
#       available to foreign nationals for visual inspection, when technology is
#       exchanged orally or when technology is made available by practice or
#       application under the guidance of persons with knowledge of the
#       technology.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL GEORGIA TECH RESEARCH CORPORATION BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Docstring of ebcpy-version:

Module based on the simres module of modelicares. As no new content is going to be
merged upstream, this "fork" of the to_pandas() function is used.

Update 18.01.2021:
As modelicares is no longer compatible with matplotlib > 3.3.2, we integrated all
necessary functions from modelicares to still be able and use loadsim functions.

.. versionadded:: 0.1.7
"""
from itertools import count
from collections import namedtuple
from scipy.io import loadmat
import pandas as pd
import numpy as np


# Namedtuple to store the time and value information of each variable
Samples = namedtuple('Samples', ['times', 'values', 'negated'])


def loadsim(fname, constants_only=False):
    r"""Load Dymola\ :sup:`®` or OpenModelica simulation results.

    **Arguments:**

    - *fname*: Name of the results file, including the path

         The file extension ('.mat') is optional.

    - *constants_only*: *True* to load only the variables from the first data
      matrix

         The first data matrix usually contains all of the constants,
         parameters, and variables that don't vary.  If only that information is
         needed, it may save resources to set *constants_only* to *True*.

    **Returns:** An instance of dict
    """
    # This does the task of mfiles/traj/tload.m from the Dymola installation.

    def parse(description):
        """Parse the variable description string into description, unit, and
        displayUnit.
        """
        description = description.rstrip(']')
        display_unit = ''
        try:
            description, unit = description.rsplit('[', 1)
        except ValueError:
            unit = ''
        else:
            try:
                unit, display_unit = unit.rsplit('|', 1)
            except ValueError:
                pass # (displayUnit = '')
        description = description.rstrip()

        return description, unit, display_unit
    
    # Load the file.
    mat, aclass = read(fname, constants_only)

    # Check the type of results.
    if aclass[0] == 'AlinearSystem':
        raise AssertionError(fname + ' is a linearization result.  Use LinRes '
                             'instead.')
    if aclass[0] != 'Atrajectory':
        raise AssertionError(fname + ' is not a simulation or '
                                     'linearization result.')

    # Determine if the data is transposed.
    try:
        transposed = aclass[3] == 'binTrans'
    except IndexError:
        transposed = False
    else:
        if not (transposed or aclass[3] == 'binNormal'):
            raise AssertionError\
                ('The orientation of the Dymola/OpenModelica results is not '
                 'recognized.  The third line of the "Aclass" variable is "%s", but '
                 'it should be "binNormal" or "binTrans".' % aclass[3])

    # Get the format version.
    version = aclass[1]

    # Process the name, description, parts of dataInfo, and data_i variables.
    # This section has been optimized for speed.  All time and value data
    # remains linked to the memory location where it is loaded by scipy.  The
    # negated variable is carried through so that copies are not necessary.  If
    # changes are made to this code, be sure to compare the performance (e.g.,
    # using %timeit in IPython).
    if version == '1.0':
        data = mat['data'].T if transposed else mat['data']
        times = data[:, 0]
        names = get_strings(mat['names'].T if transposed else mat['names'])
        variables = {name: Variable(Samples(times, data[:, i], False),
                                    '', '', '')
                     for i, name in enumerate(names)}
    elif version != '1.1':
        raise AssertionError('The version of the Dymola/OpenModelica '
                             f'result file ({version}) is not '
                             'supported.')
    else:
        names = get_strings(mat['name'].T if transposed else mat['name'])
        descriptions = get_strings(mat['description'].T if transposed else
                                   mat['description'])
        data_info = mat['dataInfo'] if transposed else mat['dataInfo'].T
        data_sets = data_info[0, :]
        sign_cols = data_info[1, :]
        variables = dict()
        for i in count(1):
            try:
                data = (mat['data_%i' % i].T if transposed else
                        mat['data_%i' % i])
            except KeyError:
                break # There are no more "data_i" variables.
            else:
                if data.shape[1] > 1: # In case the data set is empty.
                    times = data[:, 0]
                    variables.update({name:
                                      Variable(Samples(times,
                                                       data[:,
                                                            abs(sign_col) - 1],
                                                       sign_col < 0),
                                               *parse(description))
                                      for (name, description, data_set,
                                           sign_col)
                                      in zip(names, descriptions, data_sets,
                                             sign_cols)
                                      if data_set == i})

        # Time is from the last data set.
        variables['Time'] = Variable(Samples(times, times, False),
                                     'Time', 's', '')

    return variables


def read(fname, constants_only=False):
    r"""Read variables from a MATLAB\ :sup:`®` file with Dymola\ :sup:`®` or
    OpenModelica results.

    **Arguments:**

    - *fname*: Name of the results file, including the path

         This may be from a simulation or linearization.

    - *constants_only*: *True* to load only the variables from the first data
      matrix, if the result is from a simulation

    **Returns:**

    1. A dictionary of variables

    2. A list of strings from the lines of the 'Aclass' matrix
    """

    # Load the file.
    try:
        if constants_only:
            mat = loadmat(fname, chars_as_strings=False, appendmat=False,
                          variable_names=['Aclass', 'class', 'name', 'names',
                                          'description', 'dataInfo', 'data',
                                          'data_1', 'ABCD', 'nx', 'xuyName'])
        else:
            mat = loadmat(fname, chars_as_strings=False, appendmat=False)
    except IOError as error:
        raise IOError(f'"{fname}" could not be opened.'
                      '  Check that it exists.') from error

    # Check if the file contains the Aclass variable.
    try:
        aclass = mat['Aclass']
    except KeyError as error:
        raise TypeError(f'"{fname}" does not appear to be a Dymola or OpenModelica '
                        'result file.  The "Aclass" variable is '
                        'missing.') from error

    return mat, get_strings(aclass)


def get_strings(str_arr):
    """Return a list of strings from a character array.

    Strip the whitespace from the right and recode it as utf-8.
    """
    return ["".join(word_arr).replace(" ", "")
            for word_arr in str_arr]


class Variable(namedtuple('VariableNamedTuple', ['samples', 'description', 'unit', 'displayUnit'])):
    """Special namedtuple to represent a variable in a simulation, with
    methods to retrieve and perform calculations on its values

    This class is usually not instantiated directly by the user, but instances
    are returned when indexing a variable name from a simulation result
    (:class:`SimRes` instance).
    """

    def times(self):
        """Return sample times"""
        return self.samples.times

    def values(self):
        """Return sample values"""
        return -self.samples.values if self.samples.negated else self.samples.values


def mat_to_pandas(fname='dsres.mat',
                  names=None,
                  aliases=None,
                  with_unit=True,
                  constants_only=False):
    """
    Return a `pandas.DataFrame` with values from selected variables
    for the given .mat file.

    The index is time. The column headings indicate the variable names and
    units.

    :param str fname:
        The mat file to load.
    :param list names:
        If None (default), then all variables are included.
    :param dict aliases:
        Dictionary of aliases for the variable names

        The keys are the "official" variable names from the Modelica model
        and the values are the names as they should be included in the
        column headings. Any variables not in this list will not be
        aliased. Any unmatched aliases will not be used.
    :param bool with_unit:
        Boolean to determine format of keys. Default value is True.

        If set to True, the unit will be added to the key. As not all modelica-
        result files export the unit information, using with_unit=True can lead
        to errors.
    :param bool constants_only:
        The first data matrix usually contains all of the constants,
        parameters, and variables that don't vary.  If only that information is
        needed, it may save resources to set *constants_only* to *True*.
    """
    _variables = loadsim(fname, constants_only)
    # Avoid mutable argument
    if aliases is None:
        aliases = {}

    # Create the list of variable names.
    if names:
        if 'Time' not in names:
            names = names.copy()
            names.append('Time')
        non_existing_variables = list(set(names).difference(_variables.keys()))
        if non_existing_variables:
            raise KeyError(f"The following variable names are not in the given .mat file: "
                           f"{', '.join(non_existing_variables)}")
    else:
        names = _variables.keys()

    # Create a dictionary of names and values.
    times = _variables['Time'].values()
    data = {}
    for name in names:

        # Get the values
        array_values = _variables[name].values()
        if np.array_equal(_variables[name].times(), times):
            values = array_values  # Save computation.
        elif np.isinf(array_values).all():
            values = array_values[0]  # Inf values can't be resampled
        # Check if all values are constant to save resampling time
        elif np.count_nonzero(array_values -
                              np.max(array_values)) == 0:
            # Passing a scalar converts automatically to an array.
            values = array_values[0]
        else:
            values = _variables[name].values(t=times)  # Resample.
        unit = _variables[name].unit

        # Apply an alias if available.
        try:
            name = aliases[name]
        except KeyError:
            pass

        if unit and with_unit:
            data.update({name + ' / ' + unit: values})
        else:
            data.update({name: values})

    # Create the pandas data frame.
    if with_unit:
        time_key = 'Time / s'
    else:
        time_key = 'Time'
    return pd.DataFrame(data).set_index(time_key)

def mat_to_parquet(save_as,
                      fname='dsres.mat',
                  names=None,
                  aliases=None,
                  with_unit=True,
                  constants_only=False):
    df = mat_to_pandas(fname=fname,
                       names=names,
                       aliases=aliases,
                       with_unit=with_unit,
                       constants_only=constants_only)
    save_as = save_as + '.gzip'
    df.to_parquet(save_as, compression='gzip')

    return save_as