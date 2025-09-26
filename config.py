# config.py
"""配置文件模块"""

# DeepSeek API 配置
DEEPSEEK_API_KEY = "<muted>"  # 替换为您的API密钥
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0.5
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 系统运行参数
MAX_CRITIC_ITERATIONS = 3
MAX_PLAYER_ITERATIONS = 10

# 游戏类型配置
GAME_TYPES = ["Fantasy", "Romance", "Science Fiction", "Slice of Life", "Horror"]

# 游戏主题配置
GAME_TOPICS = {
    "Fantasy": ["Adventure", "Magic"],
    "Romance": ["Love", "Marriage"],
    "Science Fiction": ["Space Exploration", "Time Travel"],
    "Slice of Life": ["Family", "School"],
    "Horror": ["Haunted House", "Paranormal Investigation"]
}

# 心理构念类型
PSYCHOLOGICAL_CONSTRUCTS = [
    "extroversion",
    "depression", 
    "all_or_nothing",
    "mind_reading",
    "should_statements"
]