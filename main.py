# main.py
"""主程序入口模块 - 启动和运行PsychoGAT心理评估系统"""

import sys
import json  # JSON数据处理
from workflow import PsychoGATWorkflow  # 主要工作流类
from deepseek_adapter import DeepSeekAdapter

def main():
    """主函数 - 程序执行的入口点"""
    # 初始化PsychoGAT工作流
    with open('evaluation_process.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f

        # model = DeepSeekAdapter()
        # print(model.call_llm("你好"))
        psychogat = PsychoGATWorkflow()
        
        # 读取自评量表数据文件
        with open("self_report_scales.json", "r") as file:
            self_report_scales = json.load(file)
        
        # 选择特定的认知扭曲量表（全有或全无思维）
        self_report_scale = self_report_scales["cognitive_distortions_scale"]["all_or_nothing"]
        
        # 运行完整的心理评估流程
        total_score, item_scores = psychogat.run_assessment(
            construct="all_or_nothing",  # 评估的心理构念
            scale_json=json.dumps(self_report_scale),  # 量表数据（转换为JSON字符串）
            game_type="Fantasy",  # 游戏类型：奇幻
            game_topic="Adventure"  # 游戏主题：冒险
        )
        
        # 输出最终评估结果
        print(f"总得分: {total_score}")
        print(f"各项目得分: {item_scores}")

# Python标准的主程序入口检查
if __name__ == "__main__":

    main()  # 执行主函数