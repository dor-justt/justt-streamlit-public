import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or a .env file.")

# Agent Mode Configuration
MODE = os.getenv("MODE", "mock")  # Default to mock if not specified
if MODE not in ["mock", "prod"]:
    raise ValueError("MODE must be either 'mock' or 'prod'")

# Snowflake Configuration (only needed in prod mode)
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_PRIVATE_KEY = os.getenv("SNOWFLAKE_PRIVATE_KEY")
SNOWFLAKE_PASSPHRASE = os.getenv("SNOWFLAKE_PASSPHRASE")

# Validate Snowflake config if in prod mode
if MODE == "prod":
    missing_vars = []
    for var in ["SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT"]:
        if not globals()[var]:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required Snowflake configuration: {', '.join(missing_vars)}")