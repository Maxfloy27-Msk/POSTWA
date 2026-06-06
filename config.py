import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SMM_WINNI2_URL = os.getenv("SMM_WINNI2_URL", "")
AUTO_POST_WA_URL = os.getenv("AUTO_POST_WA_URL", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Fill .env based on .env.example")
