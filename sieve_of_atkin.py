import math
import argparse
from bitarray import bitarray
import os


class PrimeSieve:
    def __init__(self, filename="primes.bin"):
        self.filename = filename

    def generate(self, limit):
        """
        Generate prime numbers up to the specified limit using Sieve of Atkin
        and save them to a binary file using bit array.
        """
        # Initialize the sieve with bits (False = 0 = not prime)
        sieve = bitarray(limit + 1)
        sieve.setall(0)

        # Factor limit
        sqrt_limit = int(math.sqrt(limit))

        # Part 1: Mark potential prime numbers based on quadratic forms
        for x in range(1, sqrt_limit + 1):
            for y in range(1, sqrt_limit + 1):
                # First quadratic form: 4x² + y²
                n = 4 * x * x + y * y
                if n <= limit and n % 12 in (1, 5):
                    sieve[n] = not sieve[n]

                # Second quadratic form: 3x² + y²
                n = 3 * x * x + y * y
                if n <= limit and n % 12 == 7:
                    sieve[n] = not sieve[n]

                # Third quadratic form: 3x² - y²
                if x > y:
                    n = 3 * x * x - y * y
                    if n <= limit and n % 12 == 11:
                        sieve[n] = not sieve[n]

        # Mark all squares of primes and their multiples as non-prime
        for x in range(5, sqrt_limit + 1):
            if sieve[x]:
                for y in range(x * x, limit + 1, x * x):
                    sieve[y] = 0

        # Add 2 and 3 explicitly
        sieve[2] = 1
        sieve[3] = 1

        # Save the bit array directly to file
        with open(self.filename, "wb") as f:
            # Write the limit as 8-byte integer first
            f.write(limit.to_bytes(8, byteorder="big"))
            sieve.tofile(f)

        # Count primes for reporting
        prime_count = sieve.count(1)
        print(f"Generated {prime_count} prime numbers up to {limit}")
        print(f"File size: {os.path.getsize(self.filename) / (1024*1024):.2f} MB")

    def is_prime(self, number):
        """
        Check if a number is prime by looking it up in the generated file.
        """
        try:
            with open(self.filename, "rb") as f:
                # Read the limit first
                limit = int.from_bytes(f.read(8), byteorder="big")

                if number > limit:
                    raise ValueError(
                        f"Number {number} is beyond the generated limit of {limit}"
                    )

                # Create a bitarray and read from file
                sieve = bitarray()
                sieve.fromfile(f)

                return sieve[number]

        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )


def main():
    parser = argparse.ArgumentParser(description="Prime number generator and checker")
    parser.add_argument("mode", choices=["generate", "is"], help="Operation mode")
    parser.add_argument("--number", type=int, help="Number to check for primality")
    parser.add_argument(
        "--limit",
        type=int,
        default=10_000_000_000,
        help="Upper limit for prime generation",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="primes.bin",
        help="File to store/read prime numbers",
    )

    args = parser.parse_args()
    sieve = PrimeSieve(args.file)

    if args.mode == "generate":
        sieve.generate(args.limit)
    elif args.mode == "is":
        if args.number is None:
            print("Please provide a number to check with --number")
            return
        try:
            is_prime = sieve.is_prime(args.number)
            print(f"{args.number} is {'prime' if is_prime else 'not prime'}")
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
