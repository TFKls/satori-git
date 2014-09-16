#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "$OFFICE"
rm -rf result
satori_test --cpus 2-3 --time 300 --memory $[4*1024*1024*1024] howto_skip_this_hack_in_argparse --test test.yaml --submit test/sol.cpp --result result
popd
