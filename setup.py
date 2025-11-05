"""Setup script for compiling chess module with Cython."""

from setuptools import setup
from Cython.Build import cythonize

# Compile the hottest modules for performance
# Cython will compile .py files directly
modules_to_compile = [
    "chess/bitboard.py",
    "chess/attacks.py",
    "chess/magic_bitboards.py",
    "chess/bitboard_board.py",
    "chess/bitboard_movegen.py",
]

setup(
    name="chess",
    packages=["chess"],
    ext_modules=cythonize(
        modules_to_compile,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
            "nonecheck": False,
            "cdivision": True,
            "infer_types": True,
        },
        build_dir="build",
    ),
)
