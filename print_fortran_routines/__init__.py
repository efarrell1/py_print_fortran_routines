import glob
from collections import Counter
from pathlib import Path
import subprocess
import filecmp


def modify_fortran_file(input_file, output_file=None, ignore_functions=[],
                        write=True):
    """
    Input:
    - input_file: .f or .f90 filename which you want to modify
    - output_file: location of the new .f or .f90 file which you want to write
    to, containing all the write(*,*) statements
    - write: if True, write to output_file. if False, return list of strings
             to write to file. This is so I can use it for modifying multiple
             files and checking if files are modified already

    Returns: None

    Purpose: takes in f.90 filename, writes write(*,*) statements at the
    start and end of every function & subroutine and saves output file.
    """

    # types of function / subroutines to consider
    function_types = ('subroutine', 'integer function', 'logical function')

    # function names to ignore (will not insert write(*,*) statements in these)
    # this can be modified as desired, e.g. if there are subroutines that
    # you don't want to analyse
    # ignore_functions = [] by default

    # write(*,*) statements will be inserted after any lines beginning with
    # these at start of functions/subroutines
    fortran_types = ("real", "type", "use", "comment", "integer", "logical",
                     "!", " ", "include", "9", "character", "implicit",
                     "interface", "procedure", "optional", "double", "save",
                     "equivalence", "select case", "complex", "data", "*", ">",
                     "import", "class", "parameter")

    def read_initial_file(filename):
        """
        reads file and returns original, the lines without spaces &
        the name of file
        """
        inputFile = open(filename, "r+")
        original_file = inputFile.readlines()
        inputFile.close()

        f_short = filename.split('/')[-1]  # gets short filename
        f_nospaces = [l.strip() for l in original_file]  # remove white spaces

        return original_file, f_nospaces, f_short

    def get_lastline(line, is_subroutine):
        """
        given first line, returns last line of fortran function/subroutines
        """
        if is_subroutine:
            rname = line.split('(', 1)[0].split('!')[0].rstrip()
            return 'end ' + rname
        else:
            f_endname = line.split(' function')[-1].split('!')[0]
            f_endname = 'end function' + f_endname.split('(', 1)[0].rstrip()
            return f_endname

    def get_subroutine_data(f_nospaces, f_short):
        """
        returns contents of first, last lines of subroutines and
        first and last write(*,*) statements
        first & last lines of subroutines e.g.'subroutine do_something(x, y)'
        """
        first_lines = [l for l in f_nospaces if l.startswith(function_types)]
        is_subroutine = [True if 'subroutine' in l else False
                         for l in first_lines]
        last_lines = [get_lastline(l, sub)
                      for l, sub in zip(first_lines, is_subroutine)]

        # contents of write(*,*) statements to insert into fortran code
        routines = [l.split('(', 1)[0] for l in first_lines]
        start_texts = [' '.join(['      write(*,*)', "'", "start --", r, "--",
                       f_short, "'\n"]) for r in routines]
        finish_texts = [' '.join(['      write(*,*)', "'", "finsh --", r, "--",
                        f_short, "'\n"]) for r in routines]

        return [first_lines, last_lines, start_texts, finish_texts]

    def correct_startline(file_contents, start_index, end_index):
        """
        returns correct index to insert starting_text, skipping any lines
        beginning with anything in fortran_types
        """
        routine = file_contents[start_index:end_index + 1]
        line_indices = list(range(start_index, end_index+1))

        # Skip if beginning with fortran_types, blank or contain ''&' in
        # previous line (True => skip line)
        type = [l.lower().startswith(fortran_types) for l in routine]
        ends_and = [True] + ['&' in l or '!' in l for l in routine][:-1]
        is_blank = [True if y == '' else False for y in routine]
        incase = [True if any(x.startswith('select case') for x in routine[:i])
                  and any(x.startswith('end select') for x in routine[i:])
                  else False for i, val in enumerate(routine)]
        is_header = [True if any((a, b, c, d)) else False
                     for a, b, c, d in zip(type, ends_and, is_blank, incase)]

        return next((j for j, header in zip(line_indices, is_header)
                     if not header), line_indices[-1])

    def write_one_subroutine(modified_file, nospaces, a, b, stext, etext):
        """
        returns modified_file with write(*,*) added for single subroutine
        a, b = first & last lines of subroutine
        """

        nospaces = [l.strip().lower() for l in modified_file]
        istart = nospaces.index(a.lower())

        if b.lower() not in nospaces[istart:] and 'subroutine' in b:
            b = 'end subroutine'

        try:
            iend = istart + nospaces[istart:].index(b.lower())
            rout_contents = nospaces[istart:iend+1]

            while stext.strip() in rout_contents:
                istart = iend + 1 + nospaces[iend + 1:].index(a.lower())
                iend = istart + nospaces[istart:].index(b.lower())
                rout_contents = nospaces[istart:iend+1]
        except ValueError:
            return modified_file

        # get index for start write(*,*) statement
        istart = correct_startline(nospaces, istart, iend)

        # if it is an ignore function, dont' insert write(*,*) statements
        if any(x in stext for x in ignore_functions):
            return modified_file

        # if in an interface section, don't insert write statements
        no_comments = [x.split('!')[0].strip().lower() for x in nospaces]
        try:
            jint = no_comments[:istart][::-1].index('interface')
            if 'end interface' not in no_comments[istart - jint:istart][::-1]:
                return modified_file
        except ValueError:
            pass

        try:
            jint = no_comments[:istart][::-1].index('abstract interface')
            if 'end interface' not in no_comments[istart - jint:istart][::-1]:
                return modified_file
        except ValueError:
            pass

        # insert write(*,*) at start of routine
        modified_file.insert(istart, stext)

        # inserts write(*,*) at end of routine but before 'contains' if exists
        if 'contains' in rout_contents:
            icontain = rout_contents.index('contains') + 1
            modified_file.insert(nospaces.index(a.lower()) + icontain, etext)
        else:
            modified_file.insert(iend + 1, etext)

        return modified_file

    def modify_original_file(original, f_nospaces, f_short):
        """
        returns modified original_file
        """
        subdata = get_subroutine_data(f_nospaces, f_short)
        first_lines, last_lines, stexts, etexts = subdata

        routines = [l.split('(', 1)[0] for l in first_lines]
        modified_file = original.copy()

        nospaces = [l.strip().lower() for l in modified_file]

        # a and b are indices of start and end of routine
        for a, b, stext, etext in zip(first_lines, last_lines, stexts, etexts):
            modified_file = write_one_subroutine(modified_file, nospaces,
                                                 a, b, stext, etext)

        return modified_file

    def write_to_file(output_file, modified_original):
        """
        write modified_original to file
        """
        outFile = open(output_file, 'w')
        outFile.writelines(modified_original)
        outFile.close()

    # runs all the functions
    original_file, f_nospaces, f_short = read_initial_file(input_file)
    mod_original = modify_original_file(original_file, f_nospaces, f_short)
    if write:
        write_to_file(output_file, mod_original)
    else:
        return mod_original


def modify_mesa_terminal_output(input_file, output_file, i_ignore=2,
                                files=[]):
    """
    Input:
    - input_file: output text file from mesa run with write(*,*) statements
    - output_file: modified version of the output file to write to
    - i_ignore: integer all routines which occur more than this many times
      will be ignored in the output_file. This is to remove routines which
      occur hundreds of times are uninteresting and just minor check routines.
    - files: if files is not empty, only routines/functions come from files in
      this list will be included in output_file.

    Returns: None

    Purpose: takes in mesa terminal output from the write(*,*) statements
    and modifies and tabs in to make it legible and easy to understand.
    """
    separator = '\t\t'  # how much to tab in by

    def read_initial_file(filename):
        inputFile = open(filename, "r+")
        original_file = inputFile.readlines()
        inputFile.close()
        return original_file

    def get_finish_index(mstrip, i, finish_name):
        # gets index that function finishes at
        if mstrip[i][:5] == 'start' and finish_name in mstrip[i:]:
            return i + mstrip[i:].index(finish_name)
        else:
            return -9

    def remove_ignore(modified):
        ignore_functions = dict(Counter(modified))
        return [l for l in modified if ignore_functions[l] < i_ignore]

    def modify_original_file(original_file):
        '''
        Modifies original file
        '''
        modified = original_file.copy()

        # which functions to choose / ignore
        modified = [l.strip() for l in modified]
        starting = ('start', 'finsh')  # consider only lines beginning with
        modified = [x for x in modified if x.startswith(starting)]
        modified = [m.strip() for m in modified]
        modified = remove_ignore(modified)
        if files:
            modified = [x for x in modified
                        if x.endswith(tuple(files))]

        # to look for finished pairs
        finish_names = ['finsh' + x[5:] if x[:5] == 'start' else False
                        for x in modified]

        # gap until finish for each start function
        indexlist = [get_finish_index(modified, i, x) for i, x in
                     enumerate(finish_names)]
        # indices for start and end of tabbed regions
        start_indxs = [i for i, val in enumerate(indexlist) if val != -9]
        end_indxs = [x for x in indexlist if x != -9]

        # does all the tabbing
        tab_amounts = [0] * len(indexlist)
        for i, val in enumerate(indexlist):
            if val != -9:
                tab_amounts[i] = sum(x > val for x in indexlist[:i])
        # tabs in statements without matching start/finish
        for i, val in reversed(list(enumerate(indexlist))):
            if val == -9:
                try:
                    tab_amounts[i] = tab_amounts[i+1]
                except IndexError:
                    tab_amounts[i] = 0

        # make sure finish statements are tabbed the same as start statements
        for start, end in zip(start_indxs, end_indxs):
            tab_amounts[end] = tab_amounts[start]

        modified = [n*separator + m for n, m in zip(tab_amounts, modified)]
        modified = [x + '\n' for x in modified]
        return modified

    def write_to_file(output_file, modified):
        # write modified_original to file
        outFile = open(output_file, 'w')
        outFile.writelines(modified_original)
        outFile.close()

    # read file & modify list & write to file
    original_file = read_initial_file(input_file)
    modified_original = modify_original_file(original_file)
    write_to_file(output_file, modified_original)


def all_mesa_f_files(mesa_dir):
    """
    Returns list of all MESA .f90 files & standard_run_star_extras & run_star.f
    """
    standard_files = glob.glob(mesa_dir + '/*/*/*.f90')
    standard_files = [str(x) for x in standard_files]
    other_files = [mesa_dir + '/include/standard_run_star_extras.inc',
                   mesa_dir + '/star/job/run_star.f']
    standard_files = standard_files + other_files
    return standard_files


def lib_mesa_f_files(mesa_dir):
    """
    Returns list of selected MESA .f90 files & standard_run_star_extras.
    Feel free to choose the files that you are interested in. This gives a
    nice template for the main libraries called each timestep, I feel.
    """
    lib_files = glob.glob(mesa_dir + '/*/public/*_lib.f90')
    star_files = ['private/evolve.f90',
                  'public/star_lib.f90',
                  'job/run_star.f90',
                  'job/run_star_support.f90']
    star_files = [mesa_dir + '/star/' + x for x in star_files]
    star_files.append(mesa_dir + '/include/standard_run_star_extras.inc')
    main_files = lib_files + star_files
    return main_files


def star_mesa_f_files(mesa_dir):
    """
    Returns list of selected MESA .f90 files & standard_run_star_extras.
    These ones provide a nice skeleton of each timestep.
    """
    other_files = ['/star/private/evolve.f90', '/star/job/run_star.f',
                   '/include/standard_run_star_extras.inc']

    short_files = ['adjust_mass', 'eps_grav', 'micro',
                   'overshoot', 'solve_hydro', 'solve_burn', 'struct_burn_mix',
                   'timestep', 'winds', 'star_newton', 'write_model',
                   'solve_hydro', 'solve_mix', 'mesh_adjust', 'net']
    star_files = ['/star/private/' + x + '.f90' for x in short_files]
    star_other = star_files + other_files
    star_other = [mesa_dir + x for x in star_other]
    return star_other


def basic_mesa_f_files(mesa_dir):
    """
    Returns list of selected MESA .f90 files & standard_run_star_extras.
    These ones provide a nice skeleton of each timestep.
    """
    basic_files = ['public/star_lib.f90',
                   'job/run_star.f90',
                   'job/run_star.f',
                   'job/run_star_support.f90',
                   'private/evolve.f90']
    basic_files = [mesa_dir + '/star/' + x for x in basic_files]
    basic_files.append(mesa_dir + '/include/standard_run_star_extras.inc')
    return basic_files


def write_mesa_routines(mesa_dir, mesa_dir_print, files='main', reset=True,
                        ignore_functions=['subroutine check']):
    '''
    Input:
    - mesa_dir: directory of current installation of MESA
    - mesa_dir_print: new directory
    - files: 'all': means all .f90 files in MESA. List of these files that are
                    used can be accessed by all_mesa_fortran_files()
             'main': applies to list of selected MESA .f90 files &
                     standard_run_star_extras. List of these files that are
                     used can be accessed by main_mesa_fortran_files()
             otherwise you can just pass a list of custom MESA files to this
             parameter and it will work
    - ignore_functions: list of routines/functions in fortran that will be
                        ignored when going through file. Suggested example
                        ['subroutine check'] for MESA as these subroutines are
                        probably not the ones you are looking for.

    This script applies modify_fortran_file to files in
    a MESA directory. This insert write statements to .f and .f90 files in
    mesa_dir_print.

    Inserts write(*,*) into all files in file_list
    and removes write(*,*) from all other files.
    I do some checks so that files that already contain write(*,*)
    statements are not re-written as that means you have to recompile them
    This minimises the re compile time if you are doing this multiple times
    with different combinations of files_to_modify.
    Also if reset = True, files that contain write(*,*) statements but
    are not in files_to_modify are reset to their original state (i.e.
    overwritten with the default file)
    '''

    def modify_specific(files_to_modify):
        """
        Modifies list of files as described in docs above.
        """
        input_filenames = files_to_modify
        output_filenames = [mesa_dir_print + x.split(mesa_dir)[-1]
                            for x in input_filenames]
        all_files = all_mesa_f_files(mesa_dir)
        all_files_print = [mesa_dir_print + x.split(mesa_dir)[-1]
                           for x in all_files]

        for i, o in zip(input_filenames, output_filenames):
            with open(o, "r+") as f:
                original_file = f.readlines()
                modified_original = modify_fortran_file(
                                    i,
                                    ignore_functions=ignore_functions,
                                    write=False)
                if not original_file == modified_original:
                    outFile = open(o, 'w')
                    outFile.writelines(modified_original)
                    outFile.close()

        if reset:
            for i, o in zip(all_files, all_files_print):
                if o not in output_filenames and not filecmp.cmp(i, o):
                    subprocess.call(['cp', i, o])

    # Maps between files keyword and function to get them
    file_key = {'all': all_mesa_f_files,
                'lib': lib_mesa_f_files,
                'star': star_mesa_f_files,
                'basic': basic_mesa_f_files}
    try:
        fortran_files = file_key[files](mesa_dir)
    except KeyError:
        fortran_files = files
    # Calls modify_fortran_file for each file
    modify_specific(fortran_files)
