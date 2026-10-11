"""Compute kernel — parallel map over index range (matrix row operations)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


def row_kernel(matrix: list[list[float]], row: int) -> float:
    """Simulate a row-wise compute kernel: sum of squares for one row."""
    return sum(value * value for value in matrix[row])


def parallel_row_sums(matrix: list[list[float]], workers: int = 4) -> list[float]:
    """Apply the same kernel to each row index in parallel."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(row_kernel, matrix, row) for row in range(len(matrix))]
        return [future.result() for future in futures]


def main() -> None:
    matrix = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
        [2.0, 0.0, 2.0],
    ]

    row_sums = parallel_row_sums(matrix)
    for index, total in enumerate(row_sums):
        print(f"Row {index}: sum-of-squares = {total:.1f}")

    print(f"Grand total: {sum(row_sums):.1f}")


if __name__ == "__main__":
    main()
