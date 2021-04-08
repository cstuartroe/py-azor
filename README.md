# py-azor

This is the Python implementation of the [Azor programming language](https://github.com/cstuartroe/azor). It is the reference, and currently only,
implementation.

It is an interpreter. Future implementations of Azor may be transpilers or even full, honest-to-god compilers.

## Requirements

`py-azor` requires no Python libraries. The only requirement is that you use Python >= 3.6, but hey, if you weren't already doing that
you were basically living in the Dark Ages.

It does require that you have the `azor` submodule of this repo downloaded, because it accesses the standard library `stdlib.azor` from that repo.

## Usage

`python azor.py path/to/something.azor`

Not sure what file to run? Try

`python azor.py azor/tests/test.azor`
