from dotenv import load_dotenv
import os

load_dotenv()


REMOTE_TOPOLOGY_DIRECTORY = os.getenv("REMOTE_TOPOLOGY_DIRECTORY")
REMOTE_HOST = os.getenv("REMOTE_HOST")
REMOTE_USERNAME = os.getenv("REMOTE_USERNAME")
REMOTE_PASSWORD = os.getenv("REMOTE_PASSWORD")
REMOTE_PORT = os.getenv("REMOTE_PORT")
