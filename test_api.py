import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY 环境变量未设置！")

# 初始化模型
model = ChatOpenAI(
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="google/gemma-3-12b-it:free",
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "API Test"
    }
)

# 测试 API
try:
    response = model.invoke([HumanMessage(content="你好，请回复一个简单的测试消息。")])
    print("API 测试成功！")
    print("响应内容:", response.content)
except Exception as e:
    print("API 测试失败！")
    print("错误信息:", str(e)) 