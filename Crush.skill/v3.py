"""Shared v3 adapter, usable from both source and installed skill packages."""
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root if (root/'crush_core').is_dir() else root.parent))
from crush_core.__main__ import main

if __name__=='__main__':
    raise SystemExit(main())
