#!/bin/bash

echo "WARNING: This may change the positions of live devices! Type 'AGREE' or 'COVERAGE' if you still want to run these tests:"
read ok
if [ $ok == 'AGREE' ]; then
  echo "RUNNING TESTS"
  python run_tests.py tests_puts
elif [ $ok == 'COVERAGE' ]; then
  echo "RUNNING TESTS WITH COVERAGE"
  coverage run run_tests.py tests_puts
else
  echo "ABORTING"
fi
