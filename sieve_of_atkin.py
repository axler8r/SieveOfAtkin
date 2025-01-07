"""Prime number generator and checker using a segmented sieve algorithm."""

import argparse
import math
import mmap
from bitarray import bitarray
import os
import concurrent.futures
import pathlib


class PrimeSieve:
    """PrimeSieve implements a segmented sieve algorithm to generate prime numbers up to a specified limit.

    It supports parallel processing to improve efficiency and can save the generated primes to a file for later use. The class also provides methods to check if a number is prime and to list all primes within a specified range.

    Methods:
        __init__(filename="primes.bin"):
            Initializes the PrimeSieve instance with the specified filename.

        _segment_sieve(segment_start, segment_size, sqrt_limit, base_primes):
            Initializes a segment of a given size and marks non-prime numbers within that segment.

        generate(limit, num_threads=os.cpu_count()):
            Generates prime numbers up to the specified limit using a segmented sieve approach.

        _open_mmap():
            Opens a memory-mapped file if it is not already open.

        _close_mmap():
            Closes the memory-mapped file if it is open.

        __enter__():
            Enters the runtime context related to this object.

        __exit__(exc_type, exc_val, exc_tb):
            Exits the runtime context related to this object.

        is_prime(number):
            Checks if the given number is prime by examining the appropriate bit in the memory-mapped file.

        list_primes(start, end):
            Lists all prime numbers within the specified range.

    """

    def __init__(self, filename="primes.bin") -> None:
        """Initialize SieveOfAtkin.

        Args:
            filename (str): The name of the file to store the primes. Defaults to "primes.bin".

        Attributes:
            filename (str): The name of the file to store the primes.
            _mmap: Memory-mapped file object, initially set to None.
            _file: File object, initially set to None.

        """
        self.filename: str = filename
        self._mmap = None
        self._file = None

    def _segment_sieve(
        self,
        segment_start: int,
        segment_size: int,
        base_primes: list[int],
    ) -> bitarray:
        """Initialize a segment of a given size.

        Mark non-prime numbers within that segment by crossing off multiples of the provided base primes.

        Args:
            segment_start (int): The starting index of the segment.
            segment_size (int): The size of the segment.
            base_primes (list[int]): A list of base primes used for crossing off multiples.

        Returns:
            bitarray: A bitarray where prime indices are set to 1 and non-prime indices are set to 0.

        """
        # Initialize segment
        segment = bitarray(segment_size)
        segment.setall(1)

        # Adjust for segment offset
        segment_end: int = segment_start + segment_size

        # Cross off multiples of base primes
        for prime in base_primes:
            # Find first multiple of prime in segment
            first_multiple: int = math.ceil(segment_start / prime) * prime
            # Cross off all multiples in segment
            for multiple in range(first_multiple, segment_end, prime):
                if multiple >= segment_start:
                    segment[multiple - segment_start] = 0

        return segment

    def generate(self, limit: int, num_threads: int = os.cpu_count()) -> None:
        """Generate prime numbers up to the specified limit.

        Args:
            limit (int): The upper limit up to which prime numbers are to be generated.
            num_threads (int, optional): The number of threads to use for parallel processing. Defaults to the number of CPU cores.

        Returns:
            None

        This method uses a two-step approach:
        1. Generate small primes up to sqrt(limit) using the basic Sieve of Eratosthenes.
        2. Process larger numbers in segments using a segmented sieve approach, with parallel processing to improve efficiency.

        The generated prime numbers are saved to a file specified by `self.filename`.

        Raises:
            Exception: If there is an error processing any segment.

        """
        print("Initializing...")

        # Step 1: Generate small primes up to sqrt(limit) using basic Sieve of Eratosthenes
        sqrt_limit = int(math.sqrt(limit))
        base_sieve = bitarray(sqrt_limit + 1)
        base_sieve.setall(1)
        for i in range(2, int(math.sqrt(sqrt_limit)) + 1):
            if base_sieve[i]:
                for j in range(i * i, sqrt_limit + 1, i):
                    base_sieve[j] = 0

        # Get list of base primes
        base_primes: list[int] = [i for i in range(2, sqrt_limit + 1) if base_sieve[i]]
        print(f"Generated {len(base_primes)} base primes up to {sqrt_limit}")

        # Step 2: Process larger numbers in segments
        # Choose segment size to balance memory usage and parallelization efficiency
        segment_size = 1_000_000  # 1M numbers per segment
        num_segments: int = (limit - sqrt_limit + segment_size - 1) // segment_size

        # Initialize final sieve
        final_sieve = bitarray(limit + 1)
        final_sieve.setall(0)

        # Copy base primes to final sieve
        for prime in base_primes:
            final_sieve[prime] = 1

        print(f"Processing {num_segments} segments using {num_threads} threads...")

        # Process segments in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures: list[tuple[int, concurrent.futures.Future[bitarray]]] = []

            for i in range(num_segments):
                segment_start: int = sqrt_limit + i * segment_size
                current_segment_size: int = min(segment_size, limit - segment_start + 1)

                future: concurrent.futures.Future[bitarray] = executor.submit(
                    self._segment_sieve,
                    segment_start,
                    current_segment_size,
                    sqrt_limit,
                    base_primes,
                )
                futures.append((segment_start, future))

            # Collect results
            for segment_start, future in futures:
                try:
                    segment: bitarray = future.result()
                    # Copy segment to final sieve
                    segment_size: int = len(segment)
                    final_sieve[segment_start : segment_start + segment_size] = segment
                    print(f"Processed segment starting at {segment_start}", end="\r")
                except Exception as e:
                    print(f"Error processing segment {segment_start}: {e}")

        print("\nSaving results...")

        # Save to file
        with pathlib.Path.open(self.filename, "wb") as f:
            f.write(limit.to_bytes(8, byteorder="big"))
            final_sieve.tofile(f)

        prime_count: int = final_sieve.count(1)
        print(f"Generated {prime_count} prime numbers up to {limit}")
        print(f"File size: {pathlib.Path.getsize(self.filename) / (1024*1024):.2f} MB")

    def _open_mmap(self) -> None:
        """Open a memory-mapped file if it is not already open.

        This method attempts to open a memory-mapped file for reading. If the file
        is not found, it raises a FileNotFoundError with a message indicating that
        the prime numbers file is not found and suggests running the generate mode
        first.

        Raises:
            FileNotFoundError: If the prime numbers file is not found.

        """
        try:
            if self._mmap is None:
                self._file: os.BufferedReader = pathlib.Path.open(self.filename, "rb")
                self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )

    def _close_mmap(self) -> None:
        """Close the memory-mapped file if it is open.

        This method checks if the memory-mapped file is currently open. If it is,
        the method closes both the memory-mapped file and the associated file,
        and then sets their references to None.
        """
        if self._mmap is not None:
            self._mmap.close()
            self._file.close()
            self._mmap = None
            self._file = None

    def __enter__(self) -> "PrimeSieve":
        """Enter the runtime context related to this object.

        This method is called when the execution flow enters the context of the
        `with` statement. It opens the memory-mapped file and returns the
        `PrimeSieve` instance.

        Returns:
            PrimeSieve: The instance of the PrimeSieve class.

        """
        self._open_mmap()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the runtime context related to this object.

        This method is called when the 'with' statement is used. It ensures that
        the memory-mapped file is properly closed when exiting the context.

        Args:
            exc_type (Optional[Type[BaseException]]): The exception type if an exception was raised, otherwise None.
            exc_val (Optional[BaseException]): The exception instance if an exception was raised, otherwise None.
            exc_tb (Optional[TracebackType]): The traceback object if an exception was raised, otherwise None.

        """
        self._close_mmap()

    def is_prime(self, number: int) -> bool:
        """Check if the given number is prime.

        Args:
            number (int): The number to check for primality.

        Returns:
            bool: True if the number is prime, False otherwise.

        Raises:
            ValueError: If the number is beyond the generated limit.
            FileNotFoundError: If the prime numbers file is not found.

        """
        try:
            self._open_mmap()

            # Read the limit
            limit: int = int.from_bytes(self._mmap[0:8], byteorder="big")

            if number > limit:
                raise ValueError(
                    f"Number {number} is beyond the generated limit of {limit}"
                )

            # Calculate byte and bit position
            byte_offset: int = 8 + number // 8
            bit_offset: int = number % 8

            # Read the byte and check the specific bit
            byte: int = self._mmap[byte_offset]
            return bool(byte & (1 << (7 - bit_offset)))

        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )

    def list_primes(self, start: int, end: int) -> list[int]:
        """List all prime numbers within the specified range.

        Args:
            start (int): The starting value of the range.
            end (int): The ending value of the range.

        Returns:
            list[int]: A list of prime numbers within the specified range.

        Raises:
            ValueError: If the end value is beyond the generated limit.
            FileNotFoundError: If the prime numbers file is not found.

        """
        try:
            self._open_mmap()

            # Read the limit
            limit: int = int.from_bytes(self._mmap[0:8], byteorder="big")

            if end > limit:
                raise ValueError(
                    f"End value {end} is beyond the generated limit of {limit}"
                )

            # Create a bitarray and read relevant portion from file
            byte_start: int = 8 + start // 8
            byte_end: int = 8 + (end // 8) + 1

            sieve = bitarray()
            self._mmap.seek(byte_start)
            sieve.frombytes(self._mmap[byte_start:byte_end])

            # Get all prime numbers in range
            return [i for i in range(max(2, start), end + 1) if self.is_prime(i)]

        except FileNotFoundError:
            raise FileNotFoundError(
                "Prime numbers file not found. Run generate mode first."
            )


def main() -> None:
    """Generate, check or list prime number(s)."""
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

    args: argparse.Namespace = parser.parse_args()

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
