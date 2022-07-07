import argparse
from .processWatcher import init

def checkRequiredArguments(args):
    if not args.process:
        raise Exception("Process path is required")
    if not args.interval or not args.interval.isdigit() or int(args.interval) < 1:
        raise Exception("Interval is required and must be a number greater than 0")

def main():
    args = parse_cmd_line_arguments()
    checkRequiredArguments(args)
    print(args)
    init(args.process, int(args.interval))
    

def parse_cmd_line_arguments():
    parser = argparse.ArgumentParser(
        prog="processWatcher",
        description="A simple process watcher",
        epilog="Bye!",
    )
    parser.version = "1.0.0"
    parser.add_argument("-v", "--version", action="version")
    parser.add_argument("-i", "--interval",
                        help="interval after which process data is collected in seconds")
    parser.add_argument(
        "-p", "--process",
        help="absolute path to the executable file",
    )

    return parser.parse_args()