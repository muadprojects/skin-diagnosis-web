
import os
import sys

try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")
except ImportError:
    print("TensorFlow not found")

try:
    from flask import Flask
    print("Flask found")
except ImportError:
    print("Flask not found")

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
