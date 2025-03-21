import pandas as pd

def filter_depression_data(input_path):

    df = pd.read_excel(input_path)

    # 将可能存在的空值转换为空字符串
    df['question'] = df['question'].fillna('').astype(str)
    df['answer'] = df['answer'].fillna('').astype(str)

    # 筛选包含"抑郁"的行
    filtered_df = df[
        df['question'].str.contains('抑郁') |
        df['answer'].str.contains('抑郁')
        ]

    # 保存结果到新文件
    output_path = input_path.replace(".xlsx", "_filtered.xlsx")
    filtered_df.to_excel(output_path, index=False)
    print(f"筛选完成！共保留 {len(filtered_df)} 条数据，已保存至: {output_path}")


# 文件路径配置
file_path = r"D:\统计建模\cMedQA-master\answers.csv\QA1.xlsx"

# 执行筛选
filter_depression_data(file_path)

