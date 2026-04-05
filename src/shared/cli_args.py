import argparse
from pathlib import Path

def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", "-c", type=Path, required=True)
    ap.add_argument("--loglevel", "-l",
                    choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"],
                    default=None)
    return ap