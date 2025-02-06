import sys
import os

src_path = '../src'

if src_path not in sys.path:
   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), src_path)))