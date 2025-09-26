# main.py
import json
from workflow import PsychoGATWorkflow
from config import DEEPSEEK_API_KEY

def main():
    # 初始化工作流
    psychogat = PsychoGATWorkflow()
    
    # 读取量表和提示词
    with open("self_report_scales.json", "r") as file:
        self_report_scales = json.load(file)
    
    # 选择认知扭曲量表
    self_report_scale = self_report_scales["cognitive_distortions_scale"]["all_or_nothing"]
    
    # 运行评估
    total_score, item_scores = psychogat.run_assessment(
        construct="all_or_nothing",
        scale_json=json.dumps(self_report_scale),
        game_type="Fantasy",
        game_topic="Adventure"
    )
    
    print(f"总得分: {total_score}")
    print(f"各项目得分: {item_scores}")

if __name__ == "__main__":
    main()