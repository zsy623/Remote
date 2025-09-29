# agents.py
"""Agent实现模块 - 包含PsychoGAT系统中所有智能体的具体实现"""

import json
import re
from typing import Dict, Any, List
from deepseek_adapter import DeepSeekAdapter  # DeepSeek API适配器
from prompt_templates import (  # 导入所有提示词模板
    ALL_OR_NOTHING_DESIGNER_PROMPT,
    GAME_CONTROLLER_INITIAL_PROMPT, 
    GAME_CONTROLLER_SUBSQUENT_PROMPT, 
    CRITIC_PROMPT,
    HUMAN_SIMULATOR_PROMPT
)

class BaseAgent:
    """基础Agent类 - 所有具体Agent的基类"""
    
    def __init__(self):
        """初始化基础Agent，创建DeepSeek客户端"""
        self.client = DeepSeekAdapter()  # 创建API客户端实例
    
    def parse_response(self, text: str, pattern: str) -> Dict[str, Any]:

        result = {}  # 存储解析结果的字典
        lines = text.split('\n')  # 按行分割文本
        
        # 遍历每一行，提取键值对
        for line in lines:
            if ':' in line:  # 检查是否包含分隔符
                key, value = line.split(':', 1)  # 以第一个冒号分割
                result[key.strip()] = value.strip()  # 去除空白字符后存储
        
        return result

class GameDesignerAgent(BaseAgent):
    """游戏设计师Agent - 负责设计游戏框架和重设计量表"""
    
    def run(self, state) -> Dict[str, Any]:

        # 格式化提示词，插入游戏类型、主题和量表数据
        prompt = ALL_OR_NOTHING_DESIGNER_PROMPT.format(
            type=state.game_type,
            topic=state.game_topic, 
            self_report_scale=state.scale_json
        )
        
        # 调用大语言模型生成响应
        response = self.client.call_llm(prompt)
        # 解析并返回结果
        return self._parse_response(response)
    
    def _parse_response(self, text: str) -> Dict[str, Any]:

        try:
            # 使用正则表达式提取游戏名称
            name_match = re.search(r"Name:\s*(.+)", text)
            name = name_match.group(1).strip() if name_match else "未知游戏"
            
            # 提取设计师的思考过程（使用非贪婪匹配）
            thoughts_match = re.search(r"Thoughts:\s*(.+?)(?=Outline:)", text, re.DOTALL)
            thoughts = thoughts_match.group(1).strip() if thoughts_match else ""
            
            # 提取游戏大纲
            outline_match = re.search(r"Outline:\s*(.+?)(?=Scale Questions in Order:)", text, re.DOTALL)
            outline = outline_match.group(1).strip() if outline_match else ""
            
            # 提取量表问题部分
            scale_match = re.search(r"Scale Questions in Order:\s*(.+)", text, re.DOTALL)
            scale_text = scale_match.group(1).strip() if scale_match else ""
            
            # 解析JSONL格式的量表问题
            redesigned_scale = []
            for line in scale_text.split('\n'):
                line = line.strip()
                # 只处理以{开头的JSON行
                if line and line.startswith('{'):
                    try:
                        item = json.loads(line)  # 解析JSON
                        redesigned_scale.append(item)
                    except json.JSONDecodeError:
                        # 忽略解析错误的行
                        continue
            
            # 返回结构化结果
            return {
                "title": name,
                "thoughts": thoughts, 
                "outline": outline,
                "redesigned_scale": redesigned_scale
            }
        except Exception as e:
            # 解析出错时返回默认值
            print(f"解析游戏设计响应错误: {e}")
            return {
                "title": "designer title error !!!",
                "thoughts": "designer thoughts error !!!",
                "outline": "1. designer outline error !!!", 
                "redesigned_scale": []
            }

class GameControllerAgent(BaseAgent):
    """游戏控制器Agent - 负责生成游戏内容和叙事发展"""
    
    def run(self, state) -> Dict[str, Any]:

        # 根据是否为首个迭代选择不同的提示词模板
        if state.current_scale_index == 0:
            prompt = self._create_initial_prompt(state)  # 初始迭代提示词
        else:
            prompt = self._create_subsequent_prompt(state)  # 后续迭代提示词
        
        # 调用大语言模型生成响应
        response = self.client.call_llm(prompt)
        # 解析响应并根据迭代类型选择不同的解析方法
        return self._parse_response(response, state.current_scale_index == 0)
    
    def _create_initial_prompt(self, state) -> str:

        # 获取第一个量表项目，确保JSON格式正确
        scale_item = json.dumps(state.redesigned_scale[0]) if state.redesigned_scale else "{}"
        prompt = GAME_CONTROLLER_INITIAL_PROMPT.format(
            title=state.title,
            outline=state.outline,
            scale_item=scale_item
        )
        return prompt
    
    def _create_subsequent_prompt(self, state) -> str:

        # 获取当前量表项目
        scale_item = json.dumps(state.redesigned_scale[state.current_scale_index]) if state.redesigned_scale else "{}"
        prompt = GAME_CONTROLLER_SUBSQUENT_PROMPT.format(
            title=state.title,
            outline=state.outline,
            progress=state.progress,
            short_memory=state.memory,
            input_paragraph=state.prev_paragraph,
            input_instruction=state.current_instruction,
            scale_item=scale_item
        )
        return prompt
    
    def _parse_response(self, text: str, is_initial: bool) -> Dict[str, Any]:

        # 根据迭代类型选择不同的解析方法
        if is_initial:
            return self._parse_initial_response(text)
        else:
            return self._parse_subsequent_response(text)
    
    def _parse_initial_response(self, text: str) -> Dict[str, Any]:

        # 使用正则表达式提取所有段落
        paragraphs = re.findall(r"Paragraph \d+:\s*(.+)", text)
        # 提取记忆
        memory = re.findall(r"Summary:\s*(.+)", text)
        question_and_its_options = re.findall(r"Question and its Options:\s*(.+)", text)
        instructions = re.findall(r"Instruction \d+:\s*(.+)", text)
        
        # 返回解析结果，使用最后一个段落作为当前段落
        return {
            "prev_paragraph": paragraphs[-2] if len(paragraphs) >= 2 else "initial previous paragraph parse error !!!",
            "current_paragraph": paragraphs[-1] if paragraphs else "initial current paragraph parse error !!! ",
            "memory": memory if memory else ["initial memory error !!!"],
            "instructions": instructions if len(instructions) == 2 else ["initial instructions parse error !!!"],
            "question": question_and_its_options if question_and_its_options else ["initial question and its options parse error !!!"]
        }
    
    def _parse_subsequent_response(self, text: str) -> Dict[str, Any]:
        
        # 提取输出段落
        paragraph = re.findall(r"Output Paragraph:\s*\n\s*(.+)", text)
        # 提取更新后的记忆
        memory = re.findall(r"Updated Memory:\s(.+)", text)
        # 提取所有指令
        instructions = re.findall(r"Instruction \d+:\s*(.+)", text)
        
        return {
            "prev_paragraph": "Subsequent previous paragraph parse error.",
            "current_paragraph": paragraph if paragraph else "subsequent current paragraph parse error !!!",
            "memory": memory if memory else "subsequent memory parse error !!!",
            "instructions": instructions[:2] if len(instructions) >= 2 else ["subsequent instructions 1 parsed error", "subsequent instructions 2 parsed error !!!"],
            "question": {"question": "subsequent question parsed error !!!", "options": {"subsequent option 1 error !!!": 1, "subsequent option 2 error !!!": 0}}
        }

class CriticAgent(BaseAgent):
    """评论家Agent - 负责优化生成内容的质量和心理测量有效性"""
    
    def run(self, state) -> Dict[str, Any]:
        """
        运行评论家Agent的主要逻辑
        
        Args:
            state: 包含需要优化内容的状态对象
            
        Returns:
            Dict[str, Any]: 包含优化建议的结果字典
        """
        # 格式化评论家提示词，插入所有相关上下文
        prompt = CRITIC_PROMPT.format(
            short_memory=state.memory,
            previous_paragraph=state.prev_paragraph,
            current_instruction=state.current_instruction,
            current_question=json.dumps(state.current_question) if state.current_question else "{}",
            generated_paragraph=state.current_paragraph,
            next_instructions=state.next_instructions
        )
        
        # 调用大语言模型生成优化建议
        response = self.client.call_llm(prompt)
        # 解析并返回优化结果
        return self._parse_response(response)
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """
        解析评论家的响应文本
        
        Args:
            text (str): 模型生成的原始响应文本
            
        Returns:
            Dict[str, Any]: 包含各部分优化建议的结果字典
        """
        # 提取各部分的优化建议
        refined_paragraph = self._extract_part(text, "For Generated Story Paragraph:")
        refined_memory = self._extract_part(text, "For Short Memory:")
        refined_instructions = self._extract_part(text, "For Next Instructions:")
        
        # 返回优化结果，如果某部分为"OK"则表示无需优化
        return {
            "paragraph": refined_paragraph if refined_paragraph != "OK" else None,
            "memory": refined_memory if refined_memory != "OK" else None,
            "instructions": self._parse_instructions(refined_instructions) if refined_instructions != "OK" else None
        }
    
    def _extract_part(self, text: str, part_name: str) -> str:
        """
        从响应文本中提取特定部分的内容
        
        Args:
            text (str): 完整的响应文本
            part_name (str): 要提取的部分名称
            
        Returns:
            str: 提取的内容，如果未找到则返回"OK"
        """
        # 构建正则表达式模式匹配特定部分
        pattern = f"{part_name}\\s*([^\\n]+)"
        match = re.search(pattern, text)
        # 返回匹配内容或默认值
        return match.group(1).strip() if match else "OK"
    
    def _parse_instructions(self, instructions_text: str) -> List[str]:
        """
        解析指令优化建议
        
        Args:
            instructions_text (str): 包含指令优化建议的文本
            
        Returns:
            List[str]: 解析后的指令列表
        """
        try:
            # 尝试解析JSON格式的指令
            if instructions_text.startswith('[') and instructions_text.endswith(']'):
                return json.loads(instructions_text)
            # 如果解析失败，返回默认指令
            return ["指令1", "指令2"]
        except:
            # 出错时返回优化后的默认指令
            return ["优化后的指令1", "优化后的指令2"]

class HumanSimulatorAgent(BaseAgent):
    """人类模拟器Agent - 模拟具有特定心理特质的玩家行为"""
    
    def run(self, state) -> Dict[str, Any]:
        """
        运行人类模拟器Agent的主要逻辑
        
        Args:
            state: 包含游戏状态和选择上下文的状态对象
            
        Returns:
            Dict[str, Any]: 包含选择结果和索引的字典
        """
        # 格式化人类模拟器提示词，插入所有相关上下文
        prompt = HUMAN_SIMULATOR_PROMPT.format(
            trait=state.construct,
            memory=state.memory,
            previous_paragraph=state.prev_paragraph,
            new_paragraph=state.current_paragraph,
            instructions=state.next_instructions
        )
        
        # 调用大语言模型模拟玩家选择
        response = self.client.call_llm(prompt)
        # 解析并返回选择结果
        return self._parse_response(response, state.next_instructions)
    
    def _parse_response(self, text: str, next_instructions: List[str]) -> Dict[str, Any]:
        """
        解析人类模拟器的响应文本
        
        Args:
            text (str): 模型生成的原始响应文本
            next_instructions (List[str]): 可用的指令选项列表
            
        Returns:
            Dict[str, Any]: 包含选择结果和索引的字典
        """
        # 使用正则表达式匹配选择的指令
        selected_match = re.search(r"Selected Plan with number:\s*\d+\.\s*(.+)", text)
        
        if selected_match:
            # 提取选择的指令文本
            selected_instruction = selected_match.group(1).strip()
            # 确定选择的指令在列表中的索引
            selected_index = 0
            for i, instruction in enumerate(next_instructions):
                # 使用包含关系匹配指令
                if selected_instruction in instruction or instruction in selected_instruction:
                    selected_index = i
                    break
        else:
            # 如果没有匹配到，使用第一个指令作为默认选择
            selected_instruction = next_instructions[0] if next_instructions else "继续前进"
            selected_index = 0
        
        return {
            "selected_instruction": selected_instruction,
            "selected_index": selected_index
        }

class PsychometricEvaluator:
    """心理测量评估器 - 负责根据玩家选择计算心理测量得分"""
    
    def evaluate(self, scale_item: Dict, selected_instruction: str, selected_index: int) -> int:
        """
        评估玩家选择对应的心理测量得分
        
        Args:
            scale_item (Dict): 当前量表项目，包含问题和选项
            selected_instruction (str): 玩家选择的指令文本
            selected_index (int): 选择指令在选项列表中的索引
            
        Returns:
            int: 对应的心理测量得分（0或1）
        """
        # 检查量表项目是否有效且包含选项
        if scale_item and "options" in scale_item:
            # 获取选项值列表
            options = list(scale_item["options"].values())
            # 确保索引在有效范围内
            if 0 <= selected_index < len(options):
                return options[selected_index]  # 返回对应选项的得分
        # 默认返回0分
        return 0