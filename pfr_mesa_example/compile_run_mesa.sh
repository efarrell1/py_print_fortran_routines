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
