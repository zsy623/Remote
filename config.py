# config.py
"""配置文件模块 - 存储系统常量、API配置和游戏参数"""

# DeepSeek API 配置 - 用于连接大语言模型服务
DEEPSEEK_API_KEY = "sk-6acd4ca5d18d44838b4c1a5199176e2e"  # API密钥，实际使用时替换为真实密钥
DEEPSEEK_MODEL = "deepseek-chat"  # 使用的DeepSeek模型名称
DEEPSEEK_TEMPERATURE = 0.5  # 模型生成温度，控制输出的随机性（0-1之间）
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"  # DeepSeek API基础URL

# 系统运行参数 - 控制系统的迭代次数和运行限制
MAX_CRITIC_ITERATIONS = 3  # 评论家Agent最大优化迭代次数
MAX_PLAYER_ITERATIONS = 10  # 玩家交互最大迭代次数（游戏回合数）

# 游戏类型配置 - 支持的交互式小说游戏类型
GAME_TYPES = ["Fantasy", "Romance", "Science Fiction", "Slice of Life", "Horror"]

# 游戏主题配置 - 每种游戏类型对应的具体主题列表
GAME_TOPICS = {
    "Fantasy": ["Adventure", "Magic"],  # 奇幻类：冒险、魔法主题
    "Romance": ["Love", "Marriage"],  # 浪漫类：爱情、婚姻主题
    "Science Fiction": ["Space Exploration", "Time Travel"],  # 科幻类：太空探索、时间旅行
    "Slice of Life": ["Family", "School"],  # 生活类：家庭、学校主题
    "Horror": ["Haunted House", "Paranormal Investigation"]  # 恐怖类：鬼屋、超自然调查
}

# 心理构念类型 - 系统支持评估的心理特质类型
PSYCHOLOGICAL_CONSTRUCTS = [
    "extroversion",  # 外向性人格特质
    "depression",  # 抑郁程度
    "all_or_nothing",  # 全有或全无认知扭曲（当前实现重点）
    "mind_reading",  # 读心术认知扭曲
    "should_statements"  # 应该陈述认知扭曲
]