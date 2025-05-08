# 智能聊天机器人

这是一个基于 Streamlit 和 LangChain 构建的智能聊天机器人，支持文本对话和图片分析功能。

## 功能特点

- 多模态对话：支持文本和图片输入
- 智能意图识别：自动识别用户意图并选择合适的处理方式
- 实时搜索：支持通过 Tavily 进行实时信息搜索
- 数学计算：支持基础数学计算
- 日期查询：支持日期和星期查询
- 图片分析：支持图片内容分析和识别

## 本地运行

1. 克隆仓库：
```bash
git clone [您的仓库地址]
cd [仓库目录]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件并设置环境变量：
```
OPENROUTER_API_KEY=您的OpenRouter API密钥
TAVILY_API_KEY=您的Tavily API密钥
```

4. 运行应用：
```bash
streamlit run advanced_chatbot.py
```

## 在线演示

访问 [Streamlit Cloud 部署地址] 体验在线演示。

## 技术栈

- Streamlit：Web界面框架
- LangChain：LLM应用框架
- OpenRouter：模型API服务
- Tavily：搜索API服务

## 许可证

MIT License 