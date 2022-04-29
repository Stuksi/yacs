#!/bin/bash

ITERATION=1
WEEK_LONG_ITERATIONS=60480

while [ $ITERATION -lt $WEEK_LONG_ITERATIONS ]
do
  echo "iteration $ITERATION"
  python3 service.py
  sleep 10
  ITERATION=$((ITERATION + 1))
done
