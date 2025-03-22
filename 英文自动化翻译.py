import pandas as pd
import requests
import hashlib
import time
import random
import warnings
from tqdm import tqdm

# ========== 用户配置区域 ==========
INPUT_FILE = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\文字类推断_excel\情绪分析.xlsx"
OUTPUT_FILE = r"D:\统计建模\初步处理后的包含抑郁字样的数据\数字数据\文字类推断_excel\情绪分析_翻译结果.xlsx"
COLUMN_NAME = 'Comment'
MAX_TEXT_LENGTH = 5000  # 百度API单次最大支持6000字节
# ================================

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

def generate_sign(appid, query, salt, secret_key):
    """生成加密签名"""
    sign_str = appid + query + str(salt) + secret_key
    return hashlib.md5(sign_str.encode()).hexdigest()

def translate_text(text, appid, secret_key):
    """执行单次翻译（添加SSL错误处理）"""
    try:
        # 新增SSL验证设置
        session = requests.Session()
        session.verify = False  # 临时关闭SSL验证
        warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

        # 参数验证
        if len(text.encode('utf-8')) > MAX_TEXT_LENGTH:
            print(f"文本过长: {len(text)}字节 (最大支持{MAX_TEXT_LENGTH}字节)")
            return text

        # 动态生成salt
        salt = random.randint(100000, 999999)
        sign = generate_sign(appid, text, salt, secret_key)

        params = {
            'q': text,
            'from': 'en',
            'to': 'zh',
            'appid': appid,
            'salt': salt,
            'sign': sign
        }

        response = session.get('https://fanyi-api.baidu.com/api/trans/vip/translate',
                             params=params,
                             timeout=10)  # 添加超时设置
        result = response.json()

        # 错误处理
        if 'error_code' in result:
            error_map = {
                52003: '认证失败，请检查APP ID/密钥',
                54001: '请求超限，请检查账户余额',
                54003: '访问频率过高，请降低请求速度',
                58000: 'IP地址未绑定'
            }
            msg = error_map.get(result['error_code'], f"未知错误: {result}")
            print(f"API错误: {msg}")
            return text

        return result['trans_result'][0]['dst']

    except requests.exceptions.SSLError:
        print("SSL连接异常，尝试使用备用方案...")
        return translate_text(text, appid, secret_key)  # 自动重试
    except Exception as e:
        print(f"翻译失败: {str(e)}")
        return text

def process_excel(appid, secret_key):
    df = pd.read_excel(INPUT_FILE, engine='openpyxl')

    if COLUMN_NAME not in df.columns:
        raise ValueError(f"列'{COLUMN_NAME}'不存在")

    # 添加进度说明
    print(f"\n开始处理 {len(df)} 条数据，预计需要 {len(df)*1.5//60} 分钟...")

    for index in tqdm(df.index, desc='翻译进度'):
        original_text = str(df.at[index, COLUMN_NAME])[:MAX_TEXT_LENGTH//4]  # 安全截断

        if not original_text.strip():
            continue

        translated = translate_text(original_text, appid, secret_key)
        df.at[index, COLUMN_NAME] = translated

        # 速率控制
        time.sleep(1.5)  # 免费版QPS=1

    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')

if __name__ == '__main__':
    app_id, secret_key = get_api_credentials()
    try:
        process_excel(app_id, secret_key)
        print(f"\n处理完成！结果已保存至: {OUTPUT_FILE}")
    except Exception as e:
        print(f"\n致命错误: {str(e)}")
    finally:
        input("按任意键退出...")