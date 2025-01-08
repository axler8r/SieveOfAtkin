# Sieve Of Atkin

The Sieve of Atkin is a modern algorithm for finding all prime numbers up to a
specified integer. Compared with the ancient Sieve of Eratosthenes, which marks
off multiples of primes, the Sieve of Atkin does some preliminary work and then
marks off multiples of squares of primes, thus achieving a better theoretical
complexity.

The implementation is in Python. There are three `zsh` scripts to wrap the
Python implementation. Seel [Shell](#shell) below.

To use the Python implementation, see [Python](#python) below.


## Shell
Generate primes up to `<number>`.
```shell
$ mkprime <number>
```

List primes from `<from>` to `<to>`.
```shell
$ lsprime <from> <to>
```

Check if `<number>` is prime.
```shell
$ isprime <number>
```


## Python
The implementation is in Python. `main.py` is the entry point. The Sieve of
Atkin is implemented in the `sieve_of_atkin.py` module.

For detailed usage, see the help message.
```shell
$ python3 main.py --help
```
