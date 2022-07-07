import argparse
from .DirSyncer import DirSyncer
import os

def checkRequiredArguments(args):
    if args.source is None or os.path.isdir(args.source) is False:
        raise Exception("Source directory is required")
    if args.target is None or os.path.isdir(args.target) is False:
        raise Exception("Target directory is required")
    if args.interval is None or not args.interval.isdigit() or int(args.interval) < 1:
        raise Exception("Interval is required and must be a number greater than 0")
    if args.log is None:
        raise Exception("Log file is required")

def main():
    args = parse_cmd_line_arguments()
    checkRequiredArguments(args)
    print(args)
    ds = DirSyncer(args.source, args.target, int(args.interval), args.log)
    ds.startSync()
    
    

def parse_cmd_line_arguments():
    parser = argparse.ArgumentParser(
        prog="DirSyncer",
        description="One way directory synchronization",
        epilog="Bye!",
    )
    parser.version = "1.0.0"
    parser.add_argument("-v", "--version", action="version")
    parser.add_argument("-s", "--source",
                        help="Path to the source directory")
    parser.add_argument(
        "-t", "--target",
        help="Path to the target directory",
    )

    parser.add_argument(
        "-i", "--interval",
        help="interval after which directories are synchronized in seconds",
    )

    parser.add_argument(
    "-l", "--log",
    help="Path to the log file",
)

    return parser.parse_args()