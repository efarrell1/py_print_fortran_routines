## py_print_fortran_routines

## Installation
Install by cloning or downloading the repository, `cd` into it and then execute

    python setup.py install

or

    pip install .

to  install package on your system.

Also available from

    pip install print_fortran_routines

## Uninstallation
Uninstall by executing

    pip uninstall py_print_fortran_routines


## What this package does
The motivation behind this package is to track which functions / subroutines are being called in a piece of software written in Fortran. I wrote this to apply specifically to [MESA](mesa.sourceforge.net/) (Modules for Experiments in Stellar Astrophysics), but I have applied it to other software. Barring unusual Fortran syntax that I haven't taken account of, in principle it should work for any code. The way this is done is to insert `write(*,*)` statements in the fortran files that contain the functions/subroutines that you would like to keep track of. This means that when each routine is called it will print a statement such as:

``'start -- subroutine do_evolve_step_part1 -- evolve.f90'``

for a routine with a name of 'do_evolve_step_part1' in a file named evolve.f90. When the routine is complete, it will print a statement such as:

``'finsh -- subroutine do_evolve_step_part1 -- evolve.f90'``

Note that I intentionally misspell finish so that it has the same number of characters as 'start' which makes the final output files easier to read & interpret. Feel free to change that if you like!


I also include an folder which shows you how to use print_fortran_routines called pfr_mesa_example. It contains a basic MESA work directory, a python script pfr_test.py and a bash script which is called by the python script.

Tested for mesa-r11701 and mesa-r12778, though should in principle work for all versions. Note that the test folder only works for mesa-r12778 due to changes in run_star_extras.f, though you can just apply print_fortran_routines to your own or any <span style="font-variant:small-caps;">MESA</span> model.

___

## Very Quick Start:
1. Copy your current installation of <span style="font-variant:small-caps;">MESA</span> and compile it.
2. ``cd`` to ``pfr_mesa_example/pfr_test.py`` and set the variables ``mesa_dir`` and ``mesa_dir_print`` at the top of the script.
``mesa_dir`` should be your main MESA installation. ``mesa_dir_print`` is the directory you created in step 1.
3. Run `pfr_test.py`. It will do the following:
    1. Modify a selection of <span style="font-variant:small-caps;">MESA</span> Fortran files
    2. Run a <span style="font-variant:small-caps;">MESA</span> model for one timestep producing an output file called `'output.txt'`.
    3. Run pfr.modify_mesa_terminal_output producing output files called `'routines_short.txt'`, `'routines_medium.txt'` and `'routines_long.txt'`.
4. Done!

___

## Medium Start with print_fortran_routines & <span style="font-variant:small-caps;">MESA</span>
1. Make a (compiled) copy of your current installation of <span style="font-variant:small-caps;">MESA</span>.

2. Use ``pfr.write_mesa_routines(mesa_dir, mesa_dir_print, files)`` to insert `write(*,*)` statements into Fortran Files in <span style="font-variant:small-caps;">MESA</span> where:
   - mesa_dir is your main installation of <span style="font-variant:small-caps;">MESA</span>
   - mesa_dir_print is the new installation of <span style="font-variant:small-caps;">MESA</span> where you want to modify Fortran files
   - files is either a list of Fortran files in <span style="font-variant:small-caps;">MESA</span> in which you want to insert write statements or a string (e.g. 'all' for all <span style="font-variant:small-caps;">MESA</span> files, see below for further details)

3. Run a <span style="font-variant:small-caps;">MESA</span> model using
   `./rn >& output.txt` which pipes the terminal output to a file. Ideally you should run for just one timestep because the output file will become very large very quickly.

4. Use ``pfr.modify_mesa_terminal_output(input_file, output_file, i_ignore=2, files=[])`` to improve the layout of output.txt that you created in Step 3, where
   - `input_file` is the filename of the output.txt file you created in Step 3.
   - `output_file` is the new file that you want to create
   - `i_ignore` (optional) - all routines which occur more than this many times will be ignored in `output_file`. This is to remove routines which occur hundreds of times are uninteresting and just minor check routines.
   - `files`: if files is not empty, only routines/functions which originally existed in `files` will be included in `output_file`.

For more details, see below.



## Detailed usage of print_fortran_routines

There are three main functions in print_fortran_routines.

```python
modify_fortran_file(input_file, output_file=None, ignore_functions=[], write=True)
```

Purpose: takes in Fortran filename, inserts `write(*,*)` statements at the
start and end of every function & subroutine and writes to output file.


Input Parameters
- `input_file`: .f or .f90 filename which you want to modify

- `output_file`: location of the new .f or .f90 file which you want to write
to, containing all the `write(*,*)` statements

- `write`: set to True for normal usage. If false, `modify_fortran_file` returns a list of strings which contain the modified Fortran file. I use this within the write_mesa_routines function.

- `ignore_functions`: list of function/subroutine names that you want to ignore. For example, if you don't want to insert a `write(*,*)` statement in the subroutine `do_evolve_step_part1`, set ``ignore_functions = ['subroutine do_evolve_step_part1']``. Default is empty list.

Returns: None (or list of strings if `write` == False)



```python
modify_mesa_terminal_output(input_file, output_file, i_ignore=2,
                                files=[]):
```
Purpose: Takes in the output text file from running <span style="font-variant:small-caps;">MESA</span> with the `write(*,*)` statements turned on and modifies the layout to make it easier to read and interpret.

Input Parameters:
- `input_file`: output text file from <span style="font-variant:small-caps;">MESA</span> run with `write(*,*)` statements
- `output_file`: writes modified version of the `input_file` to this
- `i_ignore`: (integer) all routines which occur more than `i_ignore` times in `input_file` will be excluded from `output_file`. This is to remove short routines which are called hundreds or thousands of times or uninteresting and minor check routines.

Returns: None



```python
write_mesa_routines(mesa_dir, new_mesa_dir, files='main', reset=True,
                        ignore_functions=['subroutine check']):
```

*Purpose*: Essentially a helpful wrapper to apply modify_fortran_file to <span style="font-variant:small-caps;">MESA</span> files. This is useful because it:

1. Files that already contain `write(*,*)` statements are not modified. This means <span style="font-variant:small-caps;">MESA</span> won't have to recompile them which speeds things up.

2. Automatically resets any Fortran files not included in files to the original unmodified version (i.e. without the write statements). This applies only if `reset` == True.

3. Contains useful present lists of fortran files in <span style="font-variant:small-caps;">MESA</span> such `files='all'` which will include all .f90 files in your <span style="font-variant:small-caps;">MESA</span> installation or `files='star'` which gives a nice overview of the functions used in star/private.


Input Parameters:
- `mesa_dir`: directory of current installation of <span style="font-variant:small-caps;">MESA</span>
- `new_mesa_dir`: new directory of <span style="font-variant:small-caps;">MESA</span> installation (where you want the modified Fortran files)
- `files`: can be either a list of Fortran filenames within mesa_dir in which you want to insert `write(*,*)` statements, or one of the following strings, which is a preset selection of Fortran files:

``'all'``: includes all .f90 files in <span style="font-variant:small-caps;">MESA</span>, as well as ``'/include/standard_run_star_extras.inc'`` and ``'/star/job/run_star.f'``. List of these files can be accessed by

```python
print_fortran_routines.all_mesa_f_files()
```

``'lib'``: includes all of the Fortran files in \*lib.f90 files in public directories in <span style="font-variant:small-caps;">MESA</span> as well as `evolve.f90`, `run_star.f90`,  `run_star_support.f90` and ``/include/standard_run_star_extras.inc'``. List of these files can be accessed by

```python
print_fortran_routines.lib_mesa_f_files()
```


``'star'``: includes all of the Fortran files in star/private as well as ``'/include/standard_run_star_extras.inc'`` and ``'/star/job/run_star.f'``. List of these files can be accessed by

```python
print_fortran_routines.star_mesa_f_files()
```


``'basic'``: includes ``'public/star_lib.f90'``, ``'job/run_star.f90'``, ``'job/run_star.f'``, ``'job/run_star_support.f90'``, ``'private/evolve.f90'`` List of these files can be accessed by

```python
print_fortran_routines.basic_mesa_f_files()
```

- ignore_functions: list of routines/functions in fortran that will be ignored when going through file. Useful as these subroutines are probably not the ones you are looking for.





## Simple Example Application (included in package in pfr_test)
The following code shows a simple example of print_fortran_routines and <span style="font-variant:small-caps;">MESA</span> in action. run the following python script in a MESA work directory, with the bash script below saved as ``compile_run_mesa.sh``.

```python

import print_fortran_routines as pfr
import os
import subprocess


# ----------------------------------------------------- #
# | There are 3 main steps to do a test run:            |
# | 1. Insert the write(*,*) statements in the Fortran  |
# |    files using pfr.write_mesa_routines              |
# | 2. Re-compile MESA and run the model for 1 timestep |
# |    (or more if you like - that will just make a     |
# |    huge output file). This can be done with the     |
# |    bash script called compile_run_mesa.sh.          |
# | 3. Improve the layout of the output.txt to make it  |
# |    easier to interpret. This removes extraneous     |
# |    output and tabs in corresponding start and       |
# |    finish statements.                               |
# |                                                     |
# |   You need to specify 2 directories - one is the    |
# |   normal MESA installation and the other is the one |
# |   that you want to modify.                          |
# ----------------------------------------------------- #


# 0. Specifying directories
mesa_dir = '/Users/eoin/mesa-r12778'
mesa_dir_print = '/Users/eoin/mesa-r12778_print'


# ----------------------------------------------------- #
# 1. Modifies Fortran files in mesa_dir_print
pfr.write_mesa_routines(mesa_dir, mesa_dir_print, files='star')

# ----------------------------------------------------- #

# 2. Compiles and runs MESA and the stellar evolution model
subprocess.run(["bash", "compile_run_mesa.sh", mesa_dir_print])

# ----------------------------------------------------- #

# 3. Improve the layout of the output files - doing this 4 different ways just
#    to indicate different possibilites

inputf = os.path.abspath('output.txt')  # output file from MESA run.

files_v1 = ['run_star.f', 'evolve.f90', 'standard_run_star_extras.inc']
outputf1 = os.path.abspath('routines_short.txt')
pfr.modify_mesa_terminal_output(inputf, outputf1, files=files_v1)

files_v2 = ['net.f90', 'run_star.f', 'standard_run_star_extras.f',
            'micro.f90', 'overshoot.f90', 'evolve.f90',
            'standard_run_star_extras.inc', 'solve_hydro.f90',
            'star_newton.f90', 'struct_burn_mix.f90', 'timestep.f90']
outputf2 = os.path.abspath('routines_medium.txt')
pfr.modify_mesa_terminal_output(inputf, outputf2, files=files_v2)

outputf4 = os.path.abspath('routines_long.txt')
pfr.modify_mesa_terminal_output(inputf, outputf4, i_ignore=10)

# ----------------------------------------------------- #

```

With the following bash code (assumed to be called ``'compile_run_mesa.sh'`` by the python script above).

```bash
#!/bin/bash

# Runs test MESA file

if [ "$#" -lt 1 ]; then
  echo 'Provide MESA directory (the one containing modified Fortran files)'
  exit 1
fi

cwd=$PWD
export MESA_DIR=$1
cd $MESA_DIR
if [ ! -f skip_test ]; then
    touch skip_test
fi

# Compiling MESA
echo "---------- Compiling MESA ----------"
./install
wait
echo "---------- Compiled MESA -----------"
echo

# Compiling Model
cd $cwd
echo "---------- Compiling model ---------"
./clean
./mk
wait
echo "---------- Compiled model -----------"
echo

# Running Model
echo "---------- Running model --------------"
./rn &> output.txt
wait
echo "---------- Finished running model -----"

```
