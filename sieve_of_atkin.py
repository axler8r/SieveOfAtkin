import argparse
import math
import mmap
from bitarray import bitarray
import os
import concurrent.futures
from typing import List

class PrimeSieve:
    def __init__(self, filename="primes.bin"):
        self.filename = filename
        self._mmap = None
        self._file = None

    def _segment_sieve(self, segment_start: int, segment_size: int, sqrt_limit: int, base_primes: List[int]) -> bitarray:
        """
        Generate primes in a segment using base primes for crossing off.
        This is the key to efficient parallelization - each segment can be processed independently
        once we have the base primes up to sqrt(limit).
        """
        # Initialize segment
        segment = bitarray(segment_size)
        segment.setall(1)
        
        # Adjust for segment offset
        segment_end = segment_start + segment_size
        
        # Cross off multiples of base primes
        for prime in base_primes:
            # Find first multiple of prime in segment
            first_multiple = math.ceil(segment_start / prime) * prime
            # Cross off all multiples in segment
            for multiple in range(first_multiple, segment_end, prime):
                if multiple >= segment_start:
                    segment[multiple - segment_start] = 0
                    
        return segment

    def generate(self, limit: int, num_threads: int = os.cpu_count()):
        """
        Generate prime numbers up to the specified limit using segmented sieve approach.
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
        base_primes = [i for i in range(2, sqrt_limit + 1) if base_sieve[i]]
        print(f"Generated {len(base_primes)} base primes up to {sqrt_limit}")
        
        # Step 2: Process larger numbers in segments
        # Choose segment size to balance memory usage and parallelization efficiency
        segment_size = 1_000_000  # 1M numbers per segment
        num_segments = (limit - sqrt_limit + segment_size - 1) // segment_size
        
        # Initialize final sieve
        final_sieve = bitarray(limit + 1)
        final_sieve.setall(0)
        
        # Copy base primes to final sieve
        for prime in base_primes:
            final_sieve[prime] = 1
            
        print(f"Processing {num_segments} segments using {num_threads} threads...")
        
        # Process segments in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            for i in range(num_segments):
                segment_start = sqrt_limit + i * segment_size
                current_segment_size = min(segment_size, limit - segment_start + 1)
                
                future = executor.submit(
                    self._segment_sieve,
                    segment_start,
                    current_segment_size,
                    sqrt_limit,
                    base_primes
                )
                futures.append((segment_start, future))
                
            # Collect results
            for segment_start, future in futures:
                try:
                    segment = future.result()
                    # Copy segment to final sieve
                    segment_size = len(segment)
                    final_sieve[segment_start:segment_start + segment_size] = segment
                    print(f"Processed segment starting at {segment_start}", end='\r')
                except Exception as e:
                    print(f"Error processing segment {segment_start}: {e}")
                    
        print("\nSaving results...")
        
        # Save to file
        with open(self.filename, 'wb') as f:
            f.write(limit.to_bytes(8, byteorder='big'))
            final_sieve.tofile(f)
            
        prime_count = final_sieve.count(1)
        print(f"Generated {prime_count} prime numbers up to {limit}")
        print(f"File size: {os.path.getsize(self.filename) / (1024*1024):.2f} MB")

    # [Rest of the code remains unchanged: _open_mmap, _close_mmap, __enter__, __exit__,
    #  is_prime, list_primes, and main() function stay the same]

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
