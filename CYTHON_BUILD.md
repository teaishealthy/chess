# Building with Cython for Better Performance

The bitboard implementation can be compiled with Cython for improved performance.

## Prerequisites

```bash
pip install cython setuptools
```

## Building

From the repository root:

```bash
python setup.py build_ext --inplace
```

This will compile the following modules to C extensions:
- `chess/bitboard.py` → `chess/bitboard.so`
- `chess/attacks.py` → `chess/attacks.so`
- `chess/bitboard_board.py` → `chess/bitboard_board.so`
- `chess/bitboard_movegen.py` → `chess/bitboard_movegen.so`

Python will automatically use the compiled `.so` files instead of the `.py` files when they are available.

## Performance

With Cython compilation:
- **perft(2)**: ~10.3ms (vs 12.4ms pure Python) - **16% faster**
- **perft(4)**: ~4.9s (vs 5.8s pure Python) - **15% faster**

Note: The baseline array-based implementation is still faster (~2.1s for perft(4)) due to Python's highly optimized C-based list access. Further improvements would require:
- More aggressive type annotations with Cython's `cdef`
- Rewriting hot paths as pure Cython (`.pyx` files)
- Using PyPy JIT compilation
- Implementing magic bitboards for sliding piece attacks

## Cleaning Build Artifacts

```bash
rm -rf build/ chess/*.so chess/*.c
```

## Testing

After building, run the test suite to verify correctness:

```bash
pytest tests/
```

The compiled modules are backward compatible and pass all tests.
