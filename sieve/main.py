"""Driver."""

import argparse
import os

from sieve_of_atkin import SieveOfAtkin


def main() -> None:
    """Generate, check or list prime number(s)."""
    parser = argparse.ArgumentParser(description="Prime number generator and checker")
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser] = (
        parser.add_subparsers(dest="mode", help="Sub-command help")
    )

    # Sub-parser for 'generate'
    parser_generate: argparse.ArgumentParser = subparsers.add_parser(
        "generate", help="Generate primes"
    )
    parser_generate.add_argument(
        "--limit",
        type=int,
        default=10_000_000_000,
        help="Upper limit for prime generation",
    )
    parser_generate.add_argument(
        "--threads",
        type=int,
        default=os.cpu_count(),
        help="Number of threads for generation",
    )
    parser_generate.add_argument(
        "--file",
        type=str,
        default="primes.bin",
        help="File to store/read prime numbers",
    )

    # Sub-parser for 'check'
    parser_check: argparse.ArgumentParser = subparsers.add_parser(
        "check", help="Check if a number is prime"
    )
    parser_check.add_argument(
        "--number", type=int, required=True, help="Number to check for primality"
    )
    parser_check.add_argument(
        "--file",
        type=str,
        default="primes.bin",
        help="File to store/read prime numbers",
    )

    # Sub-parser for 'list'
    parser_list: argparse.ArgumentParser = subparsers.add_parser(
        "list", help="List primes in a range"
    )
    parser_list.add_argument(
        "--start",
        type=int,
        required=True,
        help="First value of range for listing primes",
    )
    parser_list.add_argument(
        "--stop", type=int, required=True, help="Last value of range for listing primes"
    )
    parser_list.add_argument(
        "--file",
        type=str,
        default="primes.bin",
        help="File to store/read prime numbers",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.mode == "generate":
        sieve = SieveOfAtkin(args.file)
        sieve.generate(args.limit, args.threads)
    else:
        with SieveOfAtkin(args.file) as sieve:
            try:
                if args.mode == "check":
                    is_prime: bool = sieve.is_prime(args.number)
                    print(f"{args.number} is {'prime' if is_prime else 'not prime'}")
                elif args.mode == "list":
                    primes: list[int] = sieve.list_primes(args.start, args.stop)
                    print(f"Primes in range [{args.start}, {args.stop}]:")
                    print(primes)
                    print(f"Count: {len(primes)}")
            except ValueError as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
