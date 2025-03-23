# -*- coding: utf-8 -*-
"""
真实校园抑郁数据生成工具 - 终极修复版
文件名: depression_data_generator_final.py
功能：稳定生成抑郁问诊数据并保存为Excel
"""

import pandas as pd
from openai import OpenAI
import os
import time
import json
from tqdm import tqdm

class DepressionDataGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        self.system_prompt = """请你按照以下规则帮我生成数据
{
"生成规则":{
"格式要求":"严格JSON数组，每次生成3条数据",
"字段规范":{
"question":"家长口述（含年龄性别+事件+症状），例：'儿子14岁被家委会批评后绝食'≤25字",
"answer":"医师建议（类型提示+数据+方案），例：'疑似反应性抑郁，35%重点校有此现象，建议设立家庭情绪角'≤40字",
"reason":"触发关键词+年龄阶段，例：'家委会施压|离异家庭|青春期早期'"
},
"内容规则":{
"患者特征":{
"年龄":"12-14岁/15-16岁/17-18岁",
"背景":"重点中学+随机家庭类型（高知/离异/留守/控制型）",
"症状组合":[
"学业压力：成绩暴跌/作业拖延/逃学",
"人际问题：被孤立/恋爱困扰/社交恐惧",
"躯体症状：自残/暴食/失眠/疼痛",
"家庭冲突：监控/冷战/财产纠纷"
]
},
"医师回应":{
"数据基准":"重点中学抑郁率24.8%|监控家庭41%|实验班焦虑率32%",
"干预方案":[
"家庭：拆除监控/每日倾听20分钟/暂停课外班",
"学校：心理教师介入/课业减压期/建立同伴支持"
]
},
"关键词系统":{
"学业触发":["实验班淘汰","月考排名","家委会施压"],
"家庭触发":["监控社交","遗产纠纷","留学争执"],
"年龄标签":["青春期早期(12-14)","叛逆高峰期(15-16)","成年过渡期(17-18)"]
}
},
"示例":[
{"question":"女儿15岁发现房间摄像头后，用剪刀剪床单","answer":"典型控制型家庭抑郁，监控引发问题占41%，建议立即拆除并设立孩子决策日","reason":"监控社交|实验班淘汰|叛逆高峰期"},
{"question":"儿子13岁被踢出奥数组后，每天洗手20次","answer":"这像学业压力型焦虑，重点班28%有强迫行为，建议暂停竞赛参加陶艺课","reason":"实验班淘汰|高知家庭|青春期早期"},
{"question":"侄女17岁因遗产失眠，整夜画黑色图案","answer":"需警惕创伤性抑郁，财产纠纷引发问题占19%，建议法律心理双介入","reason":"遗产纠纷|重点中学|成年过渡期"}
]
}
}"""



    def _generate_single_case(self):
        """生成单条数据（带超时和重试）"""
        for _ in range(3):  # 最大重试3次
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": "生成案例"}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"},
                    timeout=30  # 增加超时设置
                )
                result = json.loads(response.choices[0].message.content)
                if all(key in result for key in ['question', 'answer', 'reason']):
                    return result
            except Exception as e:
                print(f"\nAPI异常: {str(e)}")
                time.sleep(2)
        return None

    def generate_data(self, num_records=10, output_path="data.xlsx"):
        """稳健数据生成流程"""
        # 路径处理
        output_path = os.path.abspath(output_path.strip('"'))
        if not output_path.endswith('.xlsx'):
            output_path += '.xlsx'

        # 初始化进度条
        progress = tqdm(total=num_records, desc="生成进度")
        data = []
        retry_count = 0

        try:
            while len(data) < num_records and retry_count < 5:
                record = self._generate_single_case()
                if record:
                    data.append({
                        "问题描述": record["question"],
                        "医生回复": record["answer"],
                        "核心症状": record["reason"]
                    })
                    progress.update(1)
                    retry_count = 0  # 成功时重置重试计数
                else:
                    retry_count += 1
                    time.sleep(3)  # 失败时延长等待
                time.sleep(1)  # 基础间隔
        except KeyboardInterrupt:
            print("\n用户中断操作...")

        # 安全保存
        if data:
            try:
                temp_path = output_path.replace(".xlsx", "_temp.xlsx")
                pd.DataFrame(data).to_excel(temp_path, index=False, engine='openpyxl')

                if os.path.exists(output_path):
                    os.replace(temp_path, output_path)
                else:
                    os.rename(temp_path, output_path)

                print(f"\n✅ 成功保存 {len(data)} 条数据到:\n{output_path}")
            except Exception as e:
                print(f"保存失败: {str(e)}")

if __name__ == "__main__":
    api_key = input("DeepSeek API密钥：").strip()
    while not api_key:
        api_key = input("密钥必填：").strip()

    num = 10
    while True:
        try:
            num = int(input("生成数量（1-100）: ").strip() or "10")
            if 1 <= num <= 100: break
            print("请输入1-100之间的数字！")
        except ValueError:
            print("请输入有效数字！")

    path = input("保存路径（默认：桌面）: ").strip() or os.path.join(os.path.expanduser("~"), "Desktop", "抑郁数据.xlsx")

    generator = DepressionDataGenerator(api_key)
    generator.generate_data(num, path)
    input("按回车键退出...")