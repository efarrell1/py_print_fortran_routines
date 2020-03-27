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
