import os
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 
api_key = os.getenv("KEY_511")
if not api_key:
    raise ValueError("KEY_511 not found in .env file")