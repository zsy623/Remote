# state.py
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from config import DEEPSEEK_API_KEY, MAX_CRITIC_ITERATIONS, MAX_PLAYER_ITERATIONS

@dataclass
class GameState:
    # 初始输入
    construct: str
    scale_json: str
    game_type: str
    game_topic: str
    
    # 游戏设计阶段输出
    title: Optional[str] = None
    thoughts: Optional[str] = None
    outline: Optional[str] = None
    redesigned_scale: Optional[List[Dict]] = None
    
    # 游戏进行中的状态
    memory: str = ""
    prev_paragraph: str = ""
    current_instruction: str = ""
    current_question: Optional[Dict] = None
    current_paragraph: str = ""
    next_instructions: List[str] = None
    
    # 评估结果
    scores: List[int] = None
    current_scale_index: int = 0
    progress: float = 0.0
    
    # 批评家迭代计数
    critic_iteration: int = 0
    
    def __post_init__(self):
        if self.scores is None:
            self.scores = []
        if self.next_instructions is None:
            self.next_instructions = []