import os
import pandas as pd


def csv_to_excel(input_folder, output_folder):
    """
    将指定文件夹中的所有CSV文件转换为Excel文件并保存到新文件夹
    :param input_folder: CSV文件所在文件夹路径
    :param output_folder: Excel输出文件夹路径
    """
    # 创建输出文件夹（如果不存在）
    os.makedirs(output_folder, exist_ok=True)

    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(input_folder)
                 if f.lower().endswith('.csv') and os.path.isfile(os.path.join(input_folder, f))]

    # 检查是否有CSV文件
    if not csv_files:
        print(f"在文件夹 {input_folder} 中未找到CSV文件")
        return

    # 转换计数器
    converted_count = 0

    # 处理每个CSV文件
    for csv_file in csv_files:
        try:
            # 构建完整文件路径
            csv_path = os.path.join(input_folder, csv_file)
            excel_file = os.path.splitext(csv_file)[0] + '.xlsx'
            excel_path = os.path.join(output_folder, excel_file)

            # 读取CSV文件
            df = pd.read_csv(csv_path)

            # 保存为Excel文件
            df.to_excel(excel_path, index=False, engine='openpyxl')

            print(f"已转换: {csv_file} -> {excel_file}")
            converted_count += 1

        except Exception as e:
            print(f"转换失败: {csv_file} - 错误信息: {str(e)}")

    # 输出汇总结果
    print(f"\n转换完成！成功转换 {converted_count}/{len(csv_files)} 个文件")
    print(f"输出目录: {os.path.abspath(output_folder)}")


if __name__ == "__main__":
    # 配置路径（根据实际需求修改）
    input_folder = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\数据集_赵\The Depression Dataset（抑郁数据）\condition"  # CSV文件所在目录
    output_folder = r"D:\统计建模\初步处理后的包含抑郁字样的数据\CSV转化"  # Excel输出目录

    # 执行转换
    csv_to_excel(input_folder, output_folder)
