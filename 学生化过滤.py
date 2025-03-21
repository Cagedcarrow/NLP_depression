# -*- coding: utf-8 -*-
"""
调用API实现自动化分类
"""

import pandas as pd
from openai import OpenAI
import time
import os
import json

class DeepSeekClassifier:
    def __init__(self, api_key=None):
        self.client = OpenAI(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

        self.system_prompt = """你是一个心理分析专家，根据以下规则判断是否属于青少年（6-18岁）抑郁问题：
青少年抑郁判定专家规则（三步验证流程）
## 第一步：年龄特征验证（必须明确满足）
通过以下至少一种方式确认6-18岁年龄阶段：
① 直接出现年龄数字（如：12岁）
② 明确教育阶段表述（如：初一、高中生）
③ 学生特征词（学生/同学/老师/学校/家长会）
!排除情形：
- 出现"新生儿"、"幼儿园"、"大学生"等非适龄描述
- 诊断为明显非青少年疾病（如阿尔茨海默症）
## 第二步：核心症状判断（需满足至少1类）
|| 症状分类 || 典型表现示例 ||
|情绪症状|持续>2周的：抑郁心境/莫名哭泣/情绪麻木/兴趣丧失|
|行为症状|自残行为/自杀倾向/长期逃学/社交隔离/持续性自罪感|
|生理症状|持续失眠/暴食或厌食/不明原因疼痛/极端疲惫|
!注意：需排除感冒等普通生理疾病引起的症状
## 第三步：鉴别诊断（必须通过）
排除以下可能性：
□ 明确诊断为其他心理疾病（自闭症/多动症等）
□ 药物/毒品引发的症状
□ 正常发育阶段的短期情绪波动
## 输出规范
返回严格JSON格式：{
  "age_pass": bool（是否通过年龄验证）,
  "symptom_match": bool（症状是否符合）,
  "exclusion_pass": bool（鉴别诊断结果）,
  "is_depression": bool（最终结论）,
  "confidence": 根据以下规则计算的0-100分值：
    - 三个bool全True → 基础值80 + 症状严重度(0-20)
    - 任意一个False → 直接0,
  "reason": "判断依据简述（如：年龄不符/症状不足/确诊多动症等）"
}
## 典型病例示例
【应判为True】14岁女生连续两周逃学自残，诊断书记载"抑郁发作"
【应判为False】6岁儿童确诊自闭症出现的情绪异常
【应判为False】"大学生考研压力导致的失眠"

}"""

    def _call_api(self, text):
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text[:2000]}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result_str = response.choices[0].message.content
            try:
                return json.loads(result_str)
            except Exception as e:
                print(f"JSON解析失败: {str(e)} 原始返回：{result_str}")
                return {"is_depression": False, "confidence": 0, "reason": "解析错误"}

        except Exception as e:
            print(f"API调用错误: {str(e)}")
            return {"is_depression": False, "confidence": 0, "reason": "API错误"}

    def process_excel(self, input_path, output_path):
        try:
            df = pd.read_excel(input_path)

            question_col = df.columns[0]
            answer_col = df.columns[1]

            df.insert(2, 'is_depression', False)
            df.insert(3, 'confidence', 0)
            df.insert(4, 'reason', '')

            for index, row in df.iterrows():
                combined_text = f"问题描述：{row[question_col]}\n医师回答：{row[answer_col]}"

                result = self._call_api(combined_text)

                df.at[index, 'is_depression'] = result.get('is_depression', False)
                df.at[index, 'confidence'] = result.get('confidence', 0)
                df.at[index, 'reason'] = result.get('reason', 'error')[:20]

                if index % 3 == 0:
                    df.to_excel(output_path, index=False)
                    print(f"进度: {index+1}/{len(df)} | 当前置信度: {result['confidence']} | 理由: {result['reason']}")

                time.sleep(0.5)

        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
        finally:
            df.to_excel(output_path, index=False)
            print(f"最终结果已保存至: {output_path}")

        return df

if __name__ == "__main__":
    api_key = input("请在此粘贴您的DeepSeek API密钥（输入后回车）: ").strip()
    while not api_key:
        print("API密钥不能为空！")
        api_key = input("请重新输入DeepSeek API密钥: ").strip()

    classifier = DeepSeekClassifier(api_key=api_key)

    input_file = r"D:\统计建模\初步处理后的包含抑郁字样的数据\病例数据\儿科抑郁数据_filtered.xlsx"
    output_file = r"D:\统计建模\初步处理后的包含抑郁字样的数据\病例数据\儿科抑郁数据_学生阶段.xlsx"

    print("\n开始处理，请勿关闭程序...")
    classifier.process_excel(input_file, output_file)
    print("\n处理完成！建议人工校验前10条数据的分类结果")
