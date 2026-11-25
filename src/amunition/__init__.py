import os
from dotenv import load_dotenv, dotenv_values 
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

CONFIG = f"{Path.home()}/.amunition"
try:
    VERSION = version("amunition")
except PackageNotFoundError:
    VERSION = "dev"

load_dotenv(CONFIG) 
api_key = os.getenv("KEY_511")

if not api_key:
    print("KEY_511 not found in ~/.amunition, please set it using 'key <your-key>'.")