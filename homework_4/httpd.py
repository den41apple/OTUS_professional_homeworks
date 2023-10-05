from config import init_argument_parser, init_logging
from server import start_server

if __name__ == '__main__':
    init_argument_parser()
    init_logging()
    start_server()
