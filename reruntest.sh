#!/bin/bash
nbdev_build_lib
nbdev_build_test
python remove_test_folders.py
if [ -z $2 ]; then
    failed="--last-failed"
else
    if [ $2 = "failed" ]; then
        failed="--last-failed"
    else
        if [ $2 = "all" ]; then
            failed=""
        else
            echo "Argument $2 not recognized. Options: failed | all"
        fi
    fi
fi

if [ -z $1 ]; then
    echo "pdb at end"
    pytest --pdb $failed tests -v  --show-capture=no
else
    if [ $1 = "end" ]; then
        echo "pdb at end"
        pytest --pdb $failed tests -v  --show-capture=no
    else
        if [ $1 = "start" ]; then
            echo "pdb at beginning"
            pytest --trace $failed tests -v  --show-capture=no
        else
            if [ $1 = "none" ]; then
                pytest $failed tests -v  --show-capture=no
            else
                echo "Argument $1 not recognized. Options = end | start | none"
            fi
        fi
    fi
fi
