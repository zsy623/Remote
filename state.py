# state.py
"""状态管理模块 - 定义和管理PsychoGAT系统的运行时状态"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class GameState:
    """游戏状态类 - 存储PsychoGAT评估过程中的所有状态信息"""
    
    # === 初始输入参数 ===
    construct: str  # 要评估的心理构念类型（如"all_or_nothing"）
    scale_json: str  # 原始量表JSON数据
    game_type: str  # 选择的游戏类型（如"Fantasy"）
    game_topic: str  # 选择的游戏主题（如"Adventure"）
    
    # === 游戏设计阶段输出 ===
    title: Optional[str] = None  # 游戏设计师生成的游戏标题
    thoughts: Optional[str] = None  # 设计师的思考过程
    outline: Optional[str] = None  # 游戏故事大纲
    redesigned_scale: Optional[List[Dict]] = None  # 重设计后的量表项目列表
    
    # === 游戏运行状态 ===
    memory: str = ""  # 游戏记忆摘要，用于跟踪长上下文
    prev_paragraph: str = ""  # 上一个生成的游戏段落
    current_instruction: str = ""  # 当前玩家选择的指令
    current_question: Optional[Dict] = None  # 当前量表问题及其选项
    current_paragraph: str = ""  # 当前生成的游戏段落
    next_instructions: List[str] = field(default_factory=list)  # 下个回合的指令选项
    
    # === 评估和进度状态 ===
    scores: List[int] = field(default_factory=list)  # 每个项目的得分记录
    current_scale_index: int = 0  # 当前处理的量表项目索引
    progress: float = 0.0  # 整体进度百分比
    selected_index: int = 0  # 玩家选择的指令索引
    
    # === 评论家优化状态 ===
    critic_iteration: int = 0  # 当前评论家优化迭代次数
    
    def __post_init__(self):
        """后初始化方法 - 确保列表类型字段正确初始化"""
        # 如果scores为None，初始化为空列表
        if self.scores is None:
            self.scores = []
        # 如果next_instructions为None，初始化为空列表
        if self.next_instructions is None:
            self.next_instructions = []