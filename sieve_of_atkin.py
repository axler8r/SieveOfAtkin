import math
import argparse
from bitarray import bitarray
import os
import concurrent.futures
import mmap
from typing import List, Tuple


class PrimeSieve:
    def __init__(self, filename="primes.bin"):
        self.filename = filename
        self._mmap = None
        self._file = None

    def _estimate_primes_in_range(self, x1: int, x2: int) -> int:
        """
        Use the prime number theorem to estimate the number of primes
        in range [x1, x2]. The theorem states that π(x) ≈ x/ln(x).
        """
        if x1 < 2:
            x1 = 2
        return int(x2 / math.log(x2) - x1 / math.log(x1))

    def _generate_range(self, start: int, end: int, sieve: bitarray) -> None:
        """
        Generate prime numbers in the given range using Sieve of Atkin.
        Updates the provided bitarray in-place.
        """
        sqrt_end = int(math.sqrt(end))

        for x in range(1, sqrt_end + 1):
            for y in range(1, sqrt_end + 1):
                # First quadratic form: 4x² + y²
                n = 4 * x * x + y * y
                if start <= n <= end and n % 12 in (1, 5):
                    sieve[n] = not sieve[n]

                # Second quadratic form: 3x² + y²
                n = 3 * x * x + y * y
                if start <= n <= end and n % 12 == 7:
                    sieve[n] = not sieve[n]

                # Third quadratic form: 3x² - y²
                if x > y:
                    n = 3 * x * x - y * y
                    if start <= n <= end and n % 12 == 11:
                        sieve[n] = not sieve[n]

        # Mark squares and multiples as non-prime
        for x in range(5, sqrt_end + 1):
            if sieve[x]:
                for y in range(max(x * x, (start + x - 1) // x * x), end + 1, x * x):
                    sieve[y] = 0

    def _divide_work(self, limit: int, num_threads: int) -> List[Tuple[int, int]]:
        """
        Divide work among threads trying to ensure each thread processes
        approximately the same number of primes based on the prime number theorem.
        """
        total_primes = self._estimate_primes_in_range(2, limit)
        primes_per_thread = total_primes // num_threads

        ranges = []
        start = 2
        for i in range(num_threads - 1):
            # Binary search to find end point that gives desired number of primes
            left, right = start, limit
            while left < right:
                mid = (left + right) // 2
                primes_in_range = self._estimate_primes_in_range(start, mid)
                if primes_in_range < primes_per_thread:
                    left = mid + 1
                else:
                    right = mid
            ranges.append((start, right))
            start = right + 1

        ranges.append((start, limit))
        return ranges

    def generate(self, limit: int, num_threads: int = os.cpu_count()):
        """
        Generate prime numbers up to the specified limit using multiple threads.
        """
        # Initialize the sieve
        sieve = bitarray(limit + 1)
        sieve.setall(0)

        # Add 2 and 3 explicitly
        sieve[2] = 1
        sieve[3] = 1

        # Divide work among threads
        ranges = self._divide_work(limit, num_threads)

        # Process ranges concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self._generate_range, start, end, sieve)
                for start, end in ranges
            ]
            # Wait for all threads to complete
            concurrent.futures.wait(futures)

        # Save to file
        with open(self.filename, "wb") as f:
            # Write limit as 8-byte integer
            f.write(limit.to_bytes(8, byteorder="big"))
            sieve.tofile(f)

        prime_count = sieve.count(1)
        print(f"Generated {prime_count} prime numbers up to {limit}")
        print(f"File size: {os.path.getsize(self.filename) / (1024*1024):.2f} MB")

    def _open_mmap(self):
        """Open memory-mapped file if not already open."""
        if self._mmap is None:
            self._file = open(self.filename, "rb")
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)

    def _close_mmap(self):
        """Close memory-mapped file if open."""
        if self._mmap is not None:
            self._mmap.close()
            self._file.close()
            self._mmap = None
            self._file = None

    def __enter__(self):
        self._open_mmap()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_mmap()

    def is_prime(self, number: int) -> bool:
        """
        Check if a number is prime using memory-mapped file access.
        """
        try:
            self._open_mmap()

            # Read the limit
            limit = int.from_bytes(self._mmap[0:8], byteorder="big")

            if number > limit:
                raise ValueError(
                    f"Number {number} is beyond the generated limit of {limit}"
                )

            # Calculate byte and bit position
            byte_offset = 8 + number // 8
            bit_offset = number % 8

            # Read the byte and check the specific bit
            byte = self._mmap[byte_offset]
            return bool(byte & (1 << (7 - bit_offset)))

        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )

    def list_primes(self, start: int, end: int) -> List[int]:
        """
        List all prime numbers in the given range [start, end].
        """
        try:
            self._open_mmap()

            # Read the limit
            limit = int.from_bytes(self._mmap[0:8], byteorder="big")

            if end > limit:
                raise ValueError(
                    f"End value {end} is beyond the generated limit of {limit}"
                )

            # Create a bitarray and read relevant portion from file
            byte_start = 8 + start // 8
            byte_end = 8 + (end // 8) + 1

            sieve = bitarray()
            self._mmap.seek(byte_start)
            sieve.frombytes(self._mmap[byte_start:byte_end])

            # Get all prime numbers in range
            return [i for i in range(max(2, start), end + 1) if self.is_prime(i)]

        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )


def main():
    parser = argparse.ArgumentParser(description="Prime number generator and checker")
    parser.add_argument(
        "mode",
        choices=["generate", "is", "list"],
        help="Operation mode: generate primes, check if prime, or list primes",
    )
    parser.add_argument("--number", type=int, help="Number to check for primality")
    parser.add_argument("--start", type=int, help="Start of range for listing primes")
    parser.add_argument("--end", type=int, help="End of range for listing primes")
    parser.add_argument(
        "--limit",
        type=int,
        default=10_000_000_000,
        help="Upper limit for prime generation",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=os.cpu_count(),
        help="Number of threads for generation",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="primes.bin",
        help="File to store/read prime numbers",
    )

    args = parser.parse_args()

    with PrimeSieve(args.file) as sieve:
        try:
            if args.mode == "generate":
                sieve.generate(args.limit, args.threads)
            elif args.mode == "is":
                if args.number is None:
                    print("Please provide a number to check with --number")
                    return
                is_prime = sieve.is_prime(args.number)
                print(f"{args.number} is {'prime' if is_prime else 'not prime'}")
            elif args.mode == "list":
                if args.start is None or args.end is None:
                    print("Please provide both --start and --end for listing primes")
                    return
                primes = sieve.list_primes(args.start, args.end)
                print(f"Primes in range [{args.start}, {args.end}]:")
                print(primes)
                print(f"Count: {len(primes)}")

        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
