# MiniMax API 配置
# 请在 .env 文件中设置 MINIMAX_API_KEY

import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MODEL_NAME = "MiniMax-M2.7"

# Flask 配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
