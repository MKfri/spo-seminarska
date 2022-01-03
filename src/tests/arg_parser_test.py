import sys

sys.path.append("..")

from utils.arg_parser import ArgParser

arg_parser = ArgParser(sys.argv)

if not arg_parser.success:
    arg_parser.print_help()
    exit(1)

BLOCK_SIZE = arg_parser.get_block_size()
ROLLING_SIZE = arg_parser.get_rolling_size()
PORT = arg_parser.get_port()
FILE_NAME = arg_parser.get_file_name()
SANITIZED_FILE_NAME = arg_parser.get_sanitized_file_name()

print(BLOCK_SIZE, ROLLING_SIZE, PORT, FILE_NAME, SANITIZED_FILE_NAME)

