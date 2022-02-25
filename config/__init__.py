import sys

from config.local_config import *

# Load dev config if requested
if '-dev' in sys.argv:
    print("loading dev config")
    from private.dev_config import *
