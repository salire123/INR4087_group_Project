import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Simple class to read environment variables."""
    
    @staticmethod
    def get(key, default=None):
        """Get an environment variable by key, with an optional default."""
        return os.getenv(key, default)
    
