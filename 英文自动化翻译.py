# -*- coding: utf-8 -*-
"""
批量翻译工具 - 带自动保存功能
功能：自动翻译指定Excel列，每100条保存一次进度
作者：DeepSeek
"""

import pandas as pd
import requests
import hashlib
import random
import time
import os
import warnings
from tqdm import tqdm
from functools import wraps

# ========== 用户配置 ==========
INPUT_FILE = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\文字类推断_excel\情绪分析.xlsx"
OUTPUT_FILE = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\文字类推断_excel\情绪分析_翻译结果.xlsx"
BACKUP_FILE = r"D:\统计建模\temp\translation_backup.xlsx"  # 进度备份文件
COLUMN_NAME = 'Comment'  # 需要翻译的列名
SAVE_INTERVAL = 100  # 每处理100条保存一次
MAX_RETRIES = 5  # 最大重试次数
REQUEST_INTERVAL = 2  # 请求间隔（秒）
# ============================

# 禁用SSL警告
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

def get_api_credentials():
    """安全获取API凭证"""
    print("请按提示输入百度翻译API凭证：")
    app_id = input("请输入APP ID: ").strip()
    while not app_id:
        print("APP ID不能为空！")
        app_id = input("请重新输入APP ID: ").strip()

    secret_key = input("请输入SECRET KEY: ").strip()
    while not secret_key:
        print("SECRET KEY不能为空！")
        secret_key = input("请重新输入SECRET KEY: ").strip()

    return app_id, secret_key

def retry_request(func):
    """请求重试装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                wait_time = 2 ** retries  # 指数退避
                print(f"网络错误: {str(e)}，{wait_time}秒后重试...")
                time.sleep(wait_time)
                retries += 1
        print("超过最大重试次数，跳过本条")
        return None
    return wrapper

@retry_request
def translate_text(text, appid, secret_key):
    """执行单次翻译"""
    try:
        salt = random.randint(100000, 999999)
        sign = hashlib.md5(
            (appid + text + str(salt) + secret_key).encode()
        ).hexdigest()

        with requests.Session() as session:
            session.verify = False  # 禁用SSL验证
            response = session.get(
                'https://fanyi-api.baidu.com/api/trans/vip/translate',
                params={
                    'q': text[:5000],  # 限制文本长度
                    'from': 'en',
                    'to': 'zh',
                    'appid': appid,
                    'salt': salt,
                    'sign': sign
                },
                timeout=50
            )

        result = response.json()
        if 'error_code' in result:
            print(f"API错误 [{result['error_code']}]: {result['error_msg']}")
            return None
        return result['trans_result'][0]['dst']

    except Exception as e:
        print(f"翻译异常: {str(e)}")
        raise

def process_with_autosave(appid, secret_key):
    """带自动保存的处理流程"""
    # 初始化数据
    if os.path.exists(BACKUP_FILE):
        df = pd.read_excel(BACKUP_FILE, engine='openpyxl')
        processed = df[df[COLUMN_NAME].notna()].index[-1] + 1
        print(f"检测到备份文件，从第{processed}条继续...")
    else:
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')
        df[COLUMN_NAME] = df[COLUMN_NAME].astype(str)
        processed = 0

    total = len(df)
    progress_bar = tqdm(total=total, initial=processed, desc="翻译进度")

    try:
        for index in range(processed, total):
            original_text = df.at[index, COLUMN_NAME]

            # 跳过空文本和已翻译文本
            if pd.isna(original_text) or original_text.startswith(("【翻译成功】", "【翻译失败】")):
                progress_bar.update(1)
                continue

            # 执行翻译
            try:
                translated = translate_text(original_text, appid, secret_key)
                if translated:
                    df.at[index, COLUMN_NAME] = f"【翻译成功】{translated}"
                else:
                    df.at[index, COLUMN_NAME] = f"【翻译失败】{original_text}"
            except:
                df.at[index, COLUMN_NAME] = f"【翻译失败】{original_text}"

            # 定期保存
            if (index + 1) % SAVE_INTERVAL == 0:
                df.to_excel(BACKUP_FILE, index=False, engine='openpyxl')
                df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
                print(f"\n已保存 {index+1}/{total} 条进度")

            progress_bar.update(1)
            time.sleep(REQUEST_INTERVAL + random.uniform(0, 1))  # 随机间隔

    finally:
        # 最终保存
        df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
        progress_bar.close()

if __name__ == '__main__':
    app_id, secret_key = get_api_credentials()
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)

    try:
        process_with_autosave(app_id, secret_key)
        print("\n处理完成！结果已保存至:", OUTPUT_FILE)
    except Exception as e:
        print("\n程序异常终止:", str(e))
        print("最新进度已备份在:", BACKUP_FILE)
    finally:
        input("按回车键退出...")