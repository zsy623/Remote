# agents.py (修正版本)
from langgraph.graph import Graph
from typing import Dict, Any, List
import json
import re
from deepseek_adapter import DeepSeekAdapter
from prompt_templates import (
    ALL_OR_NOTHING_DESIGNER_PROMPT,
    GAME_CONTROLLER_PROMPT,
    CRITIC_PROMPT,
    HUMAN_SIMULATOR_PROMPT
)

class BaseAgent:
    def __init__(self):
        self.client = DeepSeekAdapter()
    
    def parse_response(self, text: str, pattern: str) -> Dict[str, Any]:
        """通用响应解析方法"""
        result = {}
        lines = text.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        
        return result

class GameDesignerAgent(BaseAgent):
    def run(self, state) -> Dict[str, Any]:
        prompt = ALL_OR_NOTHING_DESIGNER_PROMPT.format(
            type=state.game_type,
            topic=state.game_topic,
            self_report_scale=state.scale_json
        )
        
        response = self.client.call_llm(prompt)
        return self._parse_response(response)
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        try:
            # 提取名称
            name_match = re.search(r"Name:\s*(.+)", text)
            name = name_match.group(1).strip() if name_match else "未知游戏"
            
            # 提取思考
            thoughts_match = re.search(r"Thoughts:\s*(.+?)(?=Outline:)", text, re.DOTALL)
            thoughts = thoughts_match.group(1).strip() if thoughts_match else ""
            
            # 提取大纲
            outline_match = re.search(r"Outline:\s*(.+?)(?=Scale Questions in Order:)", text, re.DOTALL)
            outline = outline_match.group(1).strip() if outline_match else ""
            
            # 提取量表问题
            scale_match = re.search(r"Scale Questions in Order:\s*(.+)", text, re.DOTALL)
            scale_text = scale_match.group(1).strip() if scale_match else ""
            
            # 解析JSONL格式的量表
            redesigned_scale = []
            for line in scale_text.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        item = json.loads(line)
                        redesigned_scale.append(item)
                    except json.JSONDecodeError:
                        continue
            
            return {
                "title": name,
                "thoughts": thoughts,
                "outline": outline,
                "redesigned_scale": redesigned_scale
            }
        except Exception as e:
            print(f"解析游戏设计响应错误: {e}")
            return {
                "title": "默认游戏",
                "thoughts": "",
                "outline": "1. 开始冒险\n2. 遇到挑战\n3. 做出选择",
                "redesigned_scale": []
            }

class GameControllerAgent(BaseAgent):
    def run(self, state) -> Dict[str, Any]:
        if state.current_scale_index == 0:
            # 初始迭代
            prompt = self._create_initial_prompt(state)
        else:
            # 后续迭代
            prompt = self._create_subsequent_prompt(state)
        
        response = self.client.call_llm(prompt)
        return self._parse_response(response, state.current_scale_index == 0)
    
    def _create_initial_prompt(self, state) -> str:
        scale_item = json.dumps(state.redesigned_scale[0]) if state.redesigned_scale else "{}"
        return f"""
请作为游戏控制器开始游戏。

游戏标题: {state.title}
游戏大纲: {state.outline}
当前量表项目: {scale_item}

请生成游戏的前三个段落，并为第三个段落创建选择指令。
"""
    
    def _create_subsequent_prompt(self, state) -> str:
        scale_item = json.dumps(state.redesigned_scale[state.current_scale_index]) if state.redesigned_scale else "{}"
        return f"""
继续游戏控制。

游戏标题: {state.title}
游戏大纲: {state.outline}
当前进度: {state.progress:.0f}%
当前记忆: {state.memory}
上一段落: {state.prev_paragraph}
当前指令: {state.current_instruction}
当前量表项目: {scale_item}

请生成下一个段落、更新记忆和新的指令。
"""
    
    def _parse_response(self, text: str, is_initial: bool) -> Dict[str, Any]:
        if is_initial:
            return self._parse_initial_response(text)
        else:
            return self._parse_subsequent_response(text)
    
    def _parse_initial_response(self, text: str) -> Dict[str, Any]:
        # 简化解析逻辑
        paragraphs = re.findall(r"Paragraph \d+:\s*(.+)", text)
        instructions = re.findall(r"Instruction \d+:\s*(.+)", text)
        
        return {
            "paragraph": " ".join(paragraphs[-1:]) if paragraphs else "故事继续发展...",
            "memory": "游戏开始摘要",
            "instructions": instructions[:2] if len(instructions) >= 2 else ["继续探索", "谨慎行动"],
            "question": {"question": "默认问题", "options": {"选项1": 1, "选项2": 0}}
        }
    
    def _parse_subsequent_response(self, text: str) -> Dict[str, Any]:
        # 解析后续响应的逻辑
        paragraph_match = re.search(r"Output Paragraph:\s*(.+)", text)
        memory_match = re.search(r"Updated Memory:\s*(.+)", text)
        instructions = re.findall(r"Instruction \d+:\s*(.+)", text)
        
        return {
            "paragraph": paragraph_match.group(1) if paragraph_match else "故事进一步发展...",
            "memory": memory_match.group(1) if memory_match else "更新后的记忆",
            "instructions": instructions[:2] if len(instructions) >= 2 else ["积极前进", "保守选择"],
            "question": {"question": "当前情境问题", "options": {"积极行动": 1, "谨慎应对": 0}}
        }

class CriticAgent(BaseAgent):
    def run(self, state) -> Dict[str, Any]:
        prompt = CRITIC_PROMPT.format(
            short_memory=state.memory,
            previous_paragraph=state.prev_paragraph,
            current_instruction=state.current_instruction,
            current_question=json.dumps(state.current_question) if state.current_question else "{}",
            generated_paragraph=state.current_paragraph,
            next_instructions=state.next_instructions
        )
        
        response = self.client.call_llm(prompt)
        return self._parse_response(response)
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        refined_paragraph = self._extract_part(text, "For Generated Story Paragraph:")
        refined_memory = self._extract_part(text, "For Short Memory:")
        refined_instructions = self._extract_part(text, "For Next Instructions:")
        
        return {
            "paragraph": refined_paragraph if refined_paragraph != "OK" else None,
            "memory": refined_memory if refined_memory != "OK" else None,
            "instructions": self._parse_instructions(refined_instructions) if refined_instructions != "OK" else None
        }
    
    def _extract_part(self, text: str, part_name: str) -> str:
        pattern = f"{part_name}\\s*([^\\n]+)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else "OK"
    
    def _parse_instructions(self, instructions_text: str) -> List[str]:
        try:
            if instructions_text.startswith('[') and instructions_text.endswith(']'):
                return json.loads(instructions_text)
            return ["指令1", "指令2"]
        except:
            return ["优化后的指令1", "优化后的指令2"]

class HumanSimulatorAgent(BaseAgent):
    def run(self, state) -> Dict[str, Any]:
        prompt = HUMAN_SIMULATOR_PROMPT.format(
            trait=state.construct,
            memory=state.memory,
            previous_paragraph=state.prev_paragraph,
            new_paragraph=state.current_paragraph,
            instructions=state.next_instructions
        )
        
        response = self.client.call_llm(prompt)
        return self._parse_response(response, state.next_instructions)
    
    def _parse_response(self, text: str, next_instructions: List[str]) -> Dict[str, Any]:
        # 修正：使用传入的next_instructions参数而不是未定义的state
        selected_match = re.search(r"Selected Plan with number:\s*\d+\.\s*(.+)", text)
        if selected_match:
            selected_instruction = selected_match.group(1).strip()
            # 尝试确定选择的指令索引
            selected_index = 0
            for i, instruction in enumerate(next_instructions):
                if selected_instruction in instruction or instruction in selected_instruction:
                    selected_index = i
                    break
        else:
            # 如果没有匹配到，使用第一个指令作为默认
            selected_instruction = next_instructions[0] if next_instructions else "继续前进"
            selected_index = 0
        
        return {
            "selected_instruction": selected_instruction,
            "selected_index": selected_index
        }

class PsychometricEvaluator:
    def evaluate(self, scale_item: Dict, selected_instruction: str, selected_index: int) -> int:
        """评估选择对应的分数"""
        if scale_item and "options" in scale_item:
            options = list(scale_item["options"].values())
            if 0 <= selected_index < len(options):
                return options[selected_index]
        return 0