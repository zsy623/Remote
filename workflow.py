# workflow.py
"""工作流定义模块 - 使用LangGraph框架构建PsychoGAT的多Agent工作流"""
import sys
from langgraph.graph import StateGraph, END  # LangGraph的核心组件
from agents import (  # 导入所有Agent类
    GameDesignerAgent, GameControllerAgent, 
    CriticAgent, HumanSimulatorAgent, PsychometricEvaluator
)
from state import GameState  # 状态管理类
from config import MAX_CRITIC_ITERATIONS, MAX_PLAYER_ITERATIONS  # 系统配置参数

class PsychoGATWorkflow:
    """PsychoGAT工作流类 - 管理和执行多Agent协作流程"""
    
    def __init__(self):
        """初始化工作流，创建所有Agent实例并构建图结构"""
        # 初始化所有Agent实例
        self.designer = GameDesignerAgent()  # 游戏设计师
        self.controller = GameControllerAgent()  # 游戏控制器
        self.critic = CriticAgent()  # 评论家
        self.simulator = HumanSimulatorAgent()  # 人类模拟器
        self.evaluator = PsychometricEvaluator()  # 心理测量评估器
        
        # 构建并编译工作流图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph状态图，定义工作流节点和边"""
        # 创建状态图实例，使用GameState作为状态类型
        workflow = StateGraph(GameState)
        
        # === 添加所有工作流节点 ===
        workflow.add_node("designer", self.design_phase)  # 游戏设计阶段
        workflow.add_node("controller", self.controller_phase)  # 游戏控制阶段
        workflow.add_node("critic", self.critic_phase)  # 评论家优化阶段
        workflow.add_node("simulator", self.simulator_phase)  # 人类模拟阶段
        workflow.add_node("evaluator", self.evaluation_phase)  # 心理评估阶段
        workflow.add_node("progress_check", self.progress_check)  # 进度检查阶段
        
        # === 定义工作流边和条件路由 ===
        workflow.set_entry_point("designer")  # 设置设计阶段为入口点
        workflow.add_edge("designer", "controller")  # 设计完成后进入控制阶段
        
        # 添加条件边：根据是否需要优化决定下一步
        workflow.add_conditional_edges(
            "controller",  # 源节点
            self.should_criticize,  # 条件判断函数
            {
                "criticize": "critic",  # 需要优化时进入评论家阶段
                "continue": "simulator"  # 不需要时直接进入模拟器阶段
            }
        )
        
        workflow.add_edge("critic", "controller")  # 优化后回到控制器重新生成
        workflow.add_edge("simulator", "evaluator")  # 模拟后进入评估阶段
        workflow.add_edge("evaluator", "progress_check")  # 评估后检查进度
        
        # 添加条件边：根据是否完成决定继续或结束
        workflow.add_conditional_edges(
            "progress_check",  # 源节点
            self.should_continue,  # 条件判断函数
            {
                "continue": "controller",  # 继续下一个迭代
                "end": END  # 完成评估，结束工作流
            }
        )
        
        # 编译并返回可执行的工作流图
        return workflow.compile()
    
    def design_phase(self, state: GameState) -> GameState:
        """游戏设计阶段 - 由游戏设计师Agent执行"""
        print("=== 游戏设计阶段 ===")
        # 运行游戏设计师Agent获取设计结果
        design_output = self.designer.run(state)
        
        # 更新状态中的设计信息
        state.title = design_output["title"]
        state.thoughts = design_output["thoughts"]
        state.outline = design_output["outline"]
        state.redesigned_scale = design_output["redesigned_scale"]
        
        # 打印设计结果摘要
        print(f"Title: {state.title}")
        print(f"Outline: {state.outline}")
        print(f"Len of Redesigned Scale: {len(state.redesigned_scale)}")
        print(f"Redesigned Scale:\n")
        for item in state.redesigned_scale:
            print(f"- {item}\n")

        return state
    
    def controller_phase(self, state: GameState) -> GameState:
        """游戏控制阶段 - 由游戏控制器Agent执行"""
        print(f"=== 游戏控制阶段 (第{state.current_scale_index + 1}个项目) ===")
        # 运行游戏控制器Agent生成游戏内容
        controller_output = self.controller.run(state)
        
        # 更新状态中的游戏内容
        if state.current_scale_index == 0:
            state.prev_paragraph = controller_output["prev_paragraph"]
            state.current_question = controller_output["question"]
        state.current_paragraph = controller_output["current_paragraph"]
        state.memory = controller_output["memory"]
        state.next_instructions = controller_output["instructions"]
        
        # 打印生成内容摘要
        print(f"current paragraph: {state.current_paragraph}\n")
        print(f"memory: {state.memory}\n")
        print(f"next instructions: {state.next_instructions}\n")
        print(f"current question and its question: {state.current_question}\n")
        
        return state
    
    def critic_phase(self, state: GameState) -> GameState:
        """评论家优化阶段 - 由评论家Agent执行"""
        print("=== 评论家优化阶段 ===")
        # 运行评论家Agent获取优化建议
        critic_output = self.critic.run(state)
        
        # 应用优化建议（如果不为None）
        if critic_output["paragraph"]:
            state.current_paragraph = critic_output["paragraph"]
        if critic_output["memory"]:
            state.memory = critic_output["memory"]
        if critic_output["instructions"]:
            state.next_instructions = critic_output["instructions"]
        
        # 更新优化迭代计数
        state.critic_iteration += 1
        print(f"批评家迭代: {state.critic_iteration}")
        
        return state
    
    def simulator_phase(self, state: GameState) -> GameState:
        """人类模拟器阶段 - 由人类模拟器Agent执行"""
        print("=== 人类模拟器选择 ===")
        # 运行人类模拟器Agent模拟玩家选择
        simulator_output = self.simulator.run(state)
        
        # 更新选择结果
        state.current_instruction = simulator_output["selected_instruction"]
        state.selected_index = simulator_output["selected_index"]
        
        print(f"选择的指令: {state.current_instruction}")
        
        return state
    
    def evaluation_phase(self, state: GameState) -> GameState:
        """心理测量评估阶段 - 由心理测量评估器执行"""
        print("=== 心理测量评估 ===")
        # 获取当前量表项目
        current_scale_item = state.redesigned_scale[state.current_scale_index] if state.redesigned_scale else {}
        # 计算当前选择的得分
        score = self.evaluator.evaluate(current_scale_item, state.current_instruction, state.selected_index)
        
        # 记录得分
        state.scores.append(score)
        print(f"当前得分: {score}")
        print(f"累计得分: {sum(state.scores)}")
        
        return state
    
    def progress_check(self, state: GameState) -> GameState:
        """进度检查阶段 - 更新进度并准备下一轮迭代"""
        # 更新量表项目索引
        state.current_scale_index += 1
        # 计算总项目数和当前进度
        total_items = len(state.redesigned_scale) if state.redesigned_scale else MAX_PLAYER_ITERATIONS
        state.progress = (state.current_scale_index / total_items) * 100
        
        # 打印进度信息
        print(f"进度: {state.progress:.1f}% ({state.current_scale_index}/{total_items})")
        
        # 为下一轮迭代重置状态
        state.prev_paragraph = state.current_paragraph  # 当前段落变为上一段落
        state.critic_iteration = 0  # 重置评论家迭代计数
        
        return state
    
    def should_criticize(self, state: GameState) -> str:
        """
        判断是否需要进入评论家优化阶段
        
        Args:
            state (GameState): 当前状态对象
            
        Returns:
            str: 决策结果 - "criticize"或"continue"
        """
        # 简化逻辑：前两次迭代或当批评家迭代次数未达到最大值时进行优化
        if state.critic_iteration < MAX_CRITIC_ITERATIONS and state.critic_iteration < 2:
            return "criticize"  # 需要优化
        return "continue"  # 继续下一步
    
    def should_continue(self, state: GameState) -> str:
        """
        判断是否继续下一个迭代或结束评估
        
        Args:
            state (GameState): 当前状态对象
            
        Returns:
            str: 决策结果 - "continue"或"end"
        """
        # 计算总项目数
        total_items = len(state.redesigned_scale) if state.redesigned_scale else MAX_PLAYER_ITERATIONS
        # 检查是否还有剩余项目且未超过最大迭代次数
        if (state.current_scale_index < total_items and 
            state.current_scale_index < MAX_PLAYER_ITERATIONS):
            return "continue"  # 继续下一个迭代
        return "end"  # 结束评估
    
    def run_assessment(self, construct: str, scale_json: str, game_type: str, game_topic: str) -> tuple:
        """
        运行完整的PsychoGAT评估流程
        
        Args:
            construct (str): 心理构念类型
            scale_json (str): 原始量表JSON数据
            game_type (str): 游戏类型
            game_topic (str): 游戏主题
            
        Returns:
            tuple: (总得分, 各项目得分列表)
        """
        # 创建初始状态对象
        initial_state = GameState(
            construct=construct,
            scale_json=scale_json,
            game_type=game_type,
            game_topic=game_topic
        )
        
        print("开始PsychoGAT评估流程...")
        # 执行工作流图
        final_state = self.graph.invoke(initial_state)
        
        # 计算最终得分
        total_score = sum(final_state.scores)
        item_scores = final_state.scores
        
        # 打印最终结果
        print(f"\n=== 评估完成 ===")
        print(f"总得分: {total_score}")
        print(f"各项目得分: {item_scores}")
        
        return total_score, item_scores