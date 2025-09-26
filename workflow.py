# workflow.py
from langgraph.graph import StateGraph, END
from agents import (
    GameDesignerAgent, GameControllerAgent, 
    CriticAgent, HumanSimulatorAgent, PsychometricEvaluator
)
from state import GameState
from config import DEEPSEEK_API_KEY, MAX_CRITIC_ITERATIONS, MAX_PLAYER_ITERATIONS

class PsychoGATWorkflow:
    def __init__(self):
        self.designer = GameDesignerAgent()
        self.controller = GameControllerAgent()
        self.critic = CriticAgent()
        self.simulator = HumanSimulatorAgent()
        self.evaluator = PsychometricEvaluator()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GameState)
        
        # 定义节点
        workflow.add_node("designer", self.design_phase)
        workflow.add_node("controller", self.controller_phase)
        workflow.add_node("critic", self.critic_phase)
        workflow.add_node("simulator", self.simulator_phase)
        workflow.add_node("evaluator", self.evaluation_phase)
        workflow.add_node("progress_check", self.progress_check)
        
        # 定义边
        workflow.set_entry_point("designer")
        workflow.add_edge("designer", "controller")
        workflow.add_conditional_edges(
            "controller",
            self.should_criticize,
            {
                "criticize": "critic",
                "continue": "simulator"
            }
        )
        workflow.add_edge("critic", "controller")  # 回到控制器重新生成
        workflow.add_edge("simulator", "evaluator")
        workflow.add_edge("evaluator", "progress_check")
        workflow.add_conditional_edges(
            "progress_check",
            self.should_continue,
            {
                "continue": "controller",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def design_phase(self, state: GameState) -> GameState:
        """游戏设计阶段"""
        print("=== 游戏设计阶段 ===")
        design_output = self.designer.run(state)
        
        state.title = design_output["title"]
        state.thoughts = design_output["thoughts"]
        state.outline = design_output["outline"]
        state.redesigned_scale = design_output["redesigned_scale"]
        
        print(f"游戏标题: {state.title}")
        print(f"游戏大纲: {state.outline[:100]}...")
        print(f"重新设计的量表项目数: {len(state.redesigned_scale)}")
        
        return state
    
    def controller_phase(self, state: GameState) -> GameState:
        """游戏控制阶段"""
        print(f"=== 游戏控制阶段 (第{state.current_scale_index + 1}个项目) ===")
        controller_output = self.controller.run(state)
        
        state.current_paragraph = controller_output["paragraph"]
        state.memory = controller_output["memory"]
        state.next_instructions = controller_output["instructions"]
        state.current_question = controller_output["question"]
        
        print(f"生成段落: {state.current_paragraph[:50]}...")
        print(f"可用指令: {state.next_instructions}")
        
        return state
    
    def critic_phase(self, state: GameState) -> GameState:
        """评论家优化阶段"""
        print("=== 评论家优化阶段 ===")
        critic_output = self.critic.run(state)
        
        # 应用优化
        if critic_output["paragraph"]:
            state.current_paragraph = critic_output["paragraph"]
        if critic_output["memory"]:
            state.memory = critic_output["memory"]
        if critic_output["instructions"]:
            state.next_instructions = critic_output["instructions"]
        
        state.critic_iteration += 1
        print(f"批评家迭代: {state.critic_iteration}")
        
        return state
    
    def simulator_phase(self, state: GameState) -> GameState:
        """人类模拟器阶段"""
        print("=== 人类模拟器选择 ===")
        simulator_output = self.simulator.run(state)
        
        state.current_instruction = simulator_output["selected_instruction"]
        state.selected_index = simulator_output["selected_index"]
        
        print(f"选择的指令: {state.current_instruction}")
        
        return state
    
    def evaluation_phase(self, state: GameState) -> GameState:
        """心理测量评估阶段"""
        print("=== 心理测量评估 ===")
        current_scale_item = state.redesigned_scale[state.current_scale_index] if state.redesigned_scale else {}
        score = self.evaluator.evaluate(current_scale_item, state.current_instruction, state.selected_index)
        
        state.scores.append(score)
        print(f"当前得分: {score}")
        print(f"累计得分: {sum(state.scores)}")
        
        return state
    
    def progress_check(self, state: GameState) -> GameState:
        """进度检查"""
        state.current_scale_index += 1
        total_items = len(state.redesigned_scale) if state.redesigned_scale else MAX_PLAYER_ITERATIONS
        state.progress = (state.current_scale_index / total_items) * 100
        
        print(f"进度: {state.progress:.1f}% ({state.current_scale_index}/{total_items})")
        
        # 更新状态为下一轮准备
        state.prev_paragraph = state.current_paragraph
        state.critic_iteration = 0
        
        return state
    
    def should_criticize(self, state: GameState) -> str:
        """判断是否需要批评家优化"""
        # 简化逻辑：前两次迭代或当批评家迭代次数未达到最大值时进行优化
        if state.critic_iteration < MAX_CRITIC_ITERATIONS and state.critic_iteration < 2:
            return "criticize"
        return "continue"
    
    def should_continue(self, state: GameState) -> str:
        """判断是否继续游戏"""
        total_items = len(state.redesigned_scale) if state.redesigned_scale else MAX_PLAYER_ITERATIONS
        if (state.current_scale_index < total_items and 
            state.current_scale_index < MAX_PLAYER_ITERATIONS):
            return "continue"
        return "end"
    
    def run(self, construct: str, scale_json: str, game_type: str, game_topic: str) -> tuple:
        """运行完整的评估流程"""
        initial_state = GameState(
            construct=construct,
            scale_json=scale_json,
            game_type=game_type,
            game_topic=game_topic
        )
        
        print("开始PsychoGAT评估流程...")
        final_state = self.graph.invoke(initial_state)
        
        total_score = sum(final_state.scores)
        item_scores = final_state.scores
        
        print(f"\n=== 评估完成 ===")
        print(f"总得分: {total_score}")
        print(f"各项目得分: {item_scores}")
        
        return total_score, item_scores