import os
import pandas as pd
from tqdm import tqdm

def convert_all_csv(input_root, output_root):
    """
    递归转换指定目录及其子目录下所有CSV文件为Excel文件
    :param input_root: 输入根目录路径
    :param output_root: 输出根目录路径
    """
    # 统计计数器
    total_files = 0
    success_count = 0
    error_count = 0
    skipped_count = 0

    # 遍历所有子目录
    for root, dirs, files in os.walk(input_root):
        # 筛选CSV文件
        csv_files = [f for f in files if f.lower().endswith('.csv')]
        total_files += len(csv_files)

        # 创建进度条
        with tqdm(csv_files, desc=f"处理目录: {os.path.basename(root)}", leave=False) as pbar:
            for file in csv_files:
                try:
                    # 构建完整路径
                    input_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, input_root)
                    output_dir = os.path.join(output_root, relative_path)

                    # 创建输出目录
                    os.makedirs(output_dir, exist_ok=True)

                    # 生成输出路径
                    output_file = os.path.splitext(file)[0] + '.xlsx'
                    output_path = os.path.join(output_dir, output_file)

                    # 跳过已存在的Excel文件
                    if os.path.exists(output_path):
                        skipped_count += 1
                        pbar.update(1)
                        continue

                    # 尝试不同编码读取CSV
                    encodings = ['utf-8', 'gbk', 'latin1', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(input_path, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        raise UnicodeDecodeError("无法解码文件: 尝试了所有编码")

                    # 保存为Excel
                    df.to_excel(output_path, index=False, engine='openpyxl')
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"\n错误文件: {input_path}")
                    print(f"错误信息: {str(e)}")
                finally:
                    pbar.update(1)

    # 输出统计信息
    print(f"\n转换完成！")
    print(f"总文件数: {total_files}")
    print(f"成功转换: {success_count}")
    print(f"跳过已存在: {skipped_count}")
    print(f"转换失败: {error_count}")
    print(f"输出根目录: {os.path.abspath(output_root)}")

if __name__ == "__main__":
    # 配置路径
    input_root = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\数据集_赵"
    output_root = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\数据集_赵\EXCEL转换结果"

    # 执行转换
    convert_all_csv(input_root, output_root)