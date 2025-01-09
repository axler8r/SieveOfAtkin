# Sieve Of Atkin

The Sieve of Atkin is a modern algorithm for finding all prime numbers up to a
specified integer. Compared with the ancient Sieve of Eratosthenes, which marks
off multiples of primes, the Sieve of Atkin does some preliminary work and then
marks off multiples of squares of primes, thus achieving a better theoretical
complexity.

The implementation is in Python. There are three `zsh` scripts to wrap the
Python implementation. Seel [Shell](#shell) below.

To use the Python implementation, see [Python](#python) below.

Also use the executalbe `dist/primes` to generate primes once the executable was
generated. See [Build](#build) below.


## Getting Started
To get a local copy up and running follow these simple steps.
1. Clone the repository.
    ```shell
    $ git clone https://github.com/axler8r/SieveOfAtkin.git
    $ cd SieveOfAtkin
    ```
2. Install the dependencies.
    ```shell
    $ make init
    $ source .venv/bin/activate
    ```
3. Use the application as described in [Shell](#shell), [Python](#python) or
   [Build](#build).


## Shell
All instructions are relative to the project root.

1. Generate primes up to `<number>` using the wrpaer script `mkprime`.
    ```shell
    $ bin/mkprime [--limit <number>] [--threads <number>]
    ```
2. List primes from `<from>` to `<to>`.
    ```shell
    $ bin/lsprime --start <from>  --stop <to>
    ```
3. Check if `<number>` is prime.
    ```shell
    $ bin/isprime <number>
    ```


## Python
The implementation is in Python. `main.py` is the entry point located in
`sieve`. The Sieve of Atkin is implemented in the `sieve_of_atkin.py` module.

1. Generate primes using `main.py`.
    ```shell
    $ PYTHONPATH=$(pwd)/sieve:${PYTHONPATH} python3 -m sieve.main generate [--limit <number>] [--threads <number>] [--file <file>]
    ```
2. List primes from `<from>` to `<to>`.
    ```shell
    $ PYTHONPATH=$(pwd)/sieve:${PYTHONPATH} python3 -m sieve.main list --start <from> --stop <to> [--file <file>]
    ```
3. Check if `<number>` is prime.
    ```shell
    $ PYTHONPATH=$(pwd)/sieve:${PYTHONPATH} python3 -m sieve.main check --number <number> [--file <file>]
    ```

For detailed usage, see the help message:
```shell
$ PYTHONPATH=$(pwd)/sieve:${PYTHONPATH} python3 -m sieve.main --help
```


## Build
To build the executable, run `make exe`. To clean the build, run `make clean`.

1.  Generate primes up to `<number>` using the executable `dist/primes`.
    ```shell
    $ dist/primes generate [--limit <number>] [--threads <number>] [--file <file>]
    ```
2. List primes from `<from>` to `<to>`.
    ```shell
    $ dist/primes list --start <from> --stop <to> [--file <file>]
    ```
3. Check if `<number>` is prime.
    ```shell
    $ dist/primes check --number <number> [--file <file>]
    ```


## License
Distributed under the MIT License. See `LICENSE` for more information.
