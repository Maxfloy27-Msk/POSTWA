import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MANUS_API_KEY = os.getenv("MANUS_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MANUS_BASE_URL = "https://api.manus.ai/v2"

SMM_PROJECT_ID = "RQy56XCErXS2CvWbTTPy8W"
AUTO_POST_PROJECT_ID = "T8DVneZso4SFxzoBrUZpVU"

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "600"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Fill .env based on .env.example")
if not MANUS_API_KEY:
    raise RuntimeError("MANUS_API_KEY is not set. Fill .env based on .env.example")
