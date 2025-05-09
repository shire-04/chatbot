import streamlit as st
from typing import TypedDict, Annotated, Sequence, List, Union
from langgraph.graph import Graph, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
from langchain_tavily import TavilySearch
import math
from datetime import datetime
import re
from sympy import sympify, solve
import os
from dotenv import load_dotenv
import requests
import base64
from PIL import Image
import io

# 加载环境变量
load_dotenv()

# 打印环境变量（调试用）
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY 环境变量未设置！请确保.env文件存在并包含正确的API密钥。")

# 定义状态类型
class AgentState(TypedDict):
    # 由humanMessage和AIMessage组成的序列
    messages: Annotated[Sequence[HumanMessage | AIMessage], "对话历史"]
    # str类型，表示下一步操作
    next: Annotated[str, "下一步操作"]
    # dict类型，表示上下文信息
    context: Annotated[dict, "上下文信息"]
    # 可选的图片数据
    image: Annotated[Union[str, None], "图片数据"]

# 初始化模型和 Tavily 搜索
model = ChatOpenAI(
    openai_api_key=api_key,  # 修改参数名称
    openai_api_base="https://openrouter.ai/api/v1",  # 修改参数名称
    model_name="google/gemma-3-12b-it:free",
    # default_headers={
    #     "HTTP-Referer": "http://localhost:8501",  # 您的应用URL
    #     "X-Title": "Advanced Chatbot",  # 您的应用名称
    # }
)

# 初始化 Tavily 搜索
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY 环境变量未设置！请确保.env文件存在并包含正确的API密钥。")

tavily_search_tool = TavilySearch(
    tavily_api_key=tavily_api_key,
    max_results=5,
    topic="general"
)

# 定义节点函数
def analyze_intent(state: AgentState) -> AgentState:
    """分析用户意图"""
    messages = state["messages"]
    system_prompt = """你是一个意图分析助手。请分析用户的输入，并返回一个JSON格式的响应。
必须严格按照以下JSON格式返回，不要添加任何其他内容：
{
    "intent": "chat|search|travily_search|calculate|date|end|image_analysis",
    "confidence": 0.0-1.0,
    "reason": "解释为什么选择这个意图"
}

意图判断规则：
1. chat: 一般性对话，不需要搜索或计算
2. search: 基于知识库的搜索，适用于历史性、概念性、理论性的问题
3. travily_search: 需要实时信息的搜索，适用于：
   - 新闻、时事
   - 天气、股票等实时数据
   - 最新的技术发展
   - 当前的热门话题
   - 需要最新信息的任何查询（不包括日期查询）
4. calculate: 需要进行数学计算的问题
5. date: 涉及当前日期或星期几的查询，例如"今天的日期是什么"或"今天是星期几"
6. image_analysis: 当输入包含图片时，用于分析图片内容
7. end: 结束对话

请仔细分析用户的问题，判断是否涉及当前日期或星期几。如果是，选择 date 意图。
如果输入包含图片，选择 image_analysis 意图。
记住：必须返回有效的JSON格式，不要添加任何其他内容。"""
    
    # 检查是否包含图片
    last_message = messages[-1]
    if isinstance(last_message.content, list) and any(item.get("type") == "image_url" for item in last_message.content):
        state["next"] = "image_analysis"
        state["context"]["intent"] = {
            "intent": "image_analysis",
            "confidence": 1.0,
            "reason": "输入包含图片，需要进行图片分析"
        }
        return state
    
    analysis = model.invoke([
        SystemMessage(content=system_prompt),
        messages[-1]
    ])
    
    # 打印原始响应以便调试
    print(f"模型原始响应: {analysis.content}")
    
    try:
        # 尝试清理响应内容，只保留JSON部分
        content = analysis.content.strip()
        # 如果响应包含markdown代码块，提取其中的JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        intent_data = json.loads(content)
        state["context"]["intent"] = intent_data
        state["next"] = intent_data["intent"]
        print(f"成功解析意图: {intent_data}")
    except Exception as e:
        print(f"意图分析错误: {str(e)}")
        print(f"尝试解析的内容: {content}")
        # 如果解析失败，默认使用 chat
        state["next"] = "chat"
        state["context"]["intent"] = {
            "intent": "chat",
            "confidence": 0.8,
            "reason": "意图分析失败，默认使用chat"
        }
    
    return state

def chat(state: AgentState) -> AgentState:
    """处理普通对话"""
    messages = state["messages"]
    response = model.invoke(messages)
    state["messages"].append(response)
    state["next"] = "end"
    return state

def date_query(state: AgentState) -> AgentState:
    """处理日期相关查询"""
    messages = state["messages"]
    query = messages[-1].content.lower()

    try:
        today = datetime.now()
        if "星期" in query or "week" in query:
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = weekdays[today.weekday()]
            response_text = f"今天是{weekday}。"
        elif "日期" in query or "date" in query:
            response_text = f"今天是{today.strftime('%Y年%m月%d日')}。"
        else:
            response_text = "无法识别的日期查询，请明确询问日期或星期几。"
        
        response = AIMessage(content=response_text)
        state["messages"].append(response)
    except Exception as e:
        error_response = AIMessage(content=f"处理日期时发生错误：{str(e)}")
        state["messages"].append(error_response)
    
    state["next"] = "end"
    return state

def search(state: AgentState) -> AgentState:
    """处理基于知识库的搜索请求"""
    messages = state["messages"]
    system_prompt = """你是一个知识库搜索助手。请基于你的训练数据回答用户的问题。
    如果问题涉及需要实时信息的内容，请明确告知用户使用 tavily_search 功能。"""
    response = model.invoke([
        SystemMessage(content=system_prompt),
        messages[-1]
    ])
    state["messages"].append(response)
    state["next"] = "end"
    return state

def travily_search(state: AgentState) -> AgentState:
    messages = state["messages"]
    query = messages[-1].content
    
    # 预处理日期相关查询
    if "今天" in query and ("星期" in query or "date" in query):
        query = f"当前日期 {datetime.now().strftime('%Y')} {query}"
    
    try:
        print(f"开始 Tavily 搜索，查询: {query}")
        search_results = tavily_search_tool.invoke({
            "query": query,
            "include_domains": None,
            "exclude_domains": None,
            "search_depth": "advanced"
        })
        
        # 添加调试信息
        print(f"Tavily 搜索结果: {search_results}")
        
        if isinstance(search_results, dict) and "results" in search_results:
            # 准备搜索结果供模型总结
            results_text = ""
            for idx, result in enumerate(search_results["results"][:3], 1):
                title = result.get("title", "无标题")
                content = result.get("content", "无内容")
                url = result.get("url", "无链接")
                results_text += f"来源{idx}：{title}\n内容：{content}\n链接：{url}\n\n"
            
            # 使用模型总结搜索结果
            summary_prompt = f"""请根据以下搜索结果，生成一个准确、简洁的回答。
            要求：
            1. 只使用搜索结果中明确提供的信息，不要推测或假设
            2. 如果信息不完整或不确定，请明确说明
            3. 对于日期、星期几或天气等实时信息，必须确保信息是最新的
            4. 如果不同来源的信息有冲突，请分别列出不同来源的说法
            5. 在回答末尾列出所有使用的信息来源
            6. 如果用户询问当前日期或星期几，优先提取相关信息

            搜索结果：
            {results_text}

            用户问题：{query}

            请特别注意：
            - 不要使用搜索结果中没有明确提供的信息
            - 不要生成或推测未来的信息
            - 如果信息不完整，请明确说明"根据搜索结果，无法提供完整信息"
            """
            
            summary_response = model.invoke([
                SystemMessage(content=summary_prompt)
            ])
            
            response = AIMessage(content=summary_response.content)
        else:
            response = AIMessage(content="抱歉，未能找到相关信息。")
            
        state["messages"].append(response)
    except Exception as e:
        print(f"Tavily 搜索错误: {str(e)}")
        error_response = AIMessage(content=f"搜索时发生错误：{str(e)}\n\n请尝试使用其他搜索方式。")
        state["messages"].append(error_response)
    
    state["next"] = "end"
    return state

def calculate(state: AgentState) -> AgentState:
    """处理数学计算请求"""
    messages = state["messages"]
    query = messages[-1].content
    
    try:
        # 提取数学表达式
        expression = re.search(r'计算|求解|等于|=\s*(.*)', query)
        if expression:
            expr = expression.group(1).strip()
            try:
                # 尝试使用 sympy 进行符号计算
                result = sympify(expr)
                if isinstance(result, (int, float)):
                    response_text = f"计算结果：{result}"
                else:
                    response_text = f"表达式：{expr}\n结果：{result}"
            except:
                # 如果符号计算失败，使用 eval 进行基础计算
                try:
                    result = eval(expr)
                    response_text = f"计算结果：{result}"
                except:
                    response_text = "无法解析或计算该表达式，请确保表达式格式正确。"
        else:
            # 如果没有找到明确的表达式，使用语言模型解释
            system_prompt = """你是一个数学计算助手。请帮助用户解决数学问题。
            如果问题涉及复杂的数学概念，请提供详细的解释。"""
            response = model.invoke([
                SystemMessage(content=system_prompt),
                messages[-1]
            ])
            response_text = response.content
            
        response = AIMessage(content=response_text)
        state["messages"].append(response)
    except Exception as e:
        error_response = AIMessage(content=f"计算过程中发生错误：{str(e)}")
        state["messages"].append(error_response)
    
    state["next"] = "end"
    return state

def end(state: AgentState) -> AgentState:
    """结束节点"""
    return state

def image_analysis(state: AgentState) -> AgentState:
    """处理图片分析请求"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 提取图片和文本
    text_content = ""
    image_url = None
    for item in last_message.content:
        if item["type"] == "text":
            text_content = item["text"]
        elif item["type"] == "image_url":
            image_url = item["image_url"]["url"]
    
    # 构建系统提示词
    system_prompt = """你是一个图片分析助手。请根据用户的问题和图片内容，提供详细的分析。
    分析要求：
    1. 描述图片的主要内容
    2. 回答用户的具体问题
    3. 如果图片中包含文字，请识别并解释
    4. 如果图片涉及特定领域（如医学、建筑等），请提供专业分析
    5. 如果图片质量不佳或内容不清晰，请说明限制
    
    请确保回答准确、专业且易于理解。"""
    
    # 调用模型进行分析
    response = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message.content)
    ])
    
    state["messages"].append(response)
    state["next"] = "end"
    return state

# 创建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("analyze_intent", analyze_intent)
workflow.add_node("chat", chat)
workflow.add_node("search", search)
workflow.add_node("travily_search", travily_search)
workflow.add_node("calculate", calculate)
workflow.add_node("end", end)  # 添加结束节点
workflow.add_node("date_query", date_query)
workflow.add_node("image_analysis", image_analysis)
# 设置入口节点
workflow.set_entry_point("analyze_intent")

# 设置边
workflow.add_conditional_edges(
    "analyze_intent",
    lambda x: x["next"],
    {
        "chat": "chat",
        "search": "search",
        "travily_search": "travily_search",
        "calculate": "calculate",
        "date": "date_query",
        "image_analysis": "image_analysis",
        "end": "end"
    }
)

# 添加其他节点的边
workflow.add_edge("chat", "end")
workflow.add_edge("search", "end")
workflow.add_edge("travily_search", "end")
workflow.add_edge("calculate", "end")
workflow.add_edge("date_query", "end")
workflow.add_edge("image_analysis", "end")

# 编译图
app = workflow.compile()


# Streamlit界面
def main():
    st.title("智能聊天机器人")
    
    # 添加侧边栏配置
    with st.sidebar:
        st.header("设置")
        model_name = st.selectbox("选择模型", ["deepseek-chat", "gpt-4", "claude"])
        temperature = st.slider("温度", 0.0, 1.0, 0.7)
        max_tokens = st.number_input("最大token数", 100, 2000, 500)
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "image" not in st.session_state:
        st.session_state.image = None
    
    # 显示聊天历史
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            st.chat_message("user").write(message.content)
        else:
            st.chat_message("assistant").write(message.content)
    
    # 图片上传
    uploaded_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        # 读取图片
        image = Image.open(uploaded_file)
        # 转换为base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        st.session_state.image = img_str
        # 显示图片
        st.image(image, caption="上传的图片", use_column_width=True)
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题"):
        # 添加用户消息
        if st.session_state.image:
            # 如果有图片，创建多模态消息
            message_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{st.session_state.image}"
                    }
                }
            ]
            st.session_state.messages.append(HumanMessage(content=message_content))
            # 清除图片
            st.session_state.image = None
        else:
            st.session_state.messages.append(HumanMessage(content=prompt))
        
        st.chat_message("user").write(prompt)
        
        # 运行图
        result = app.invoke({
            "messages": st.session_state.messages,
            "next": "analyze_intent",
            "context": {},
            "image": st.session_state.image
        })
        
        # 更新会话状态
        st.session_state.messages = result["messages"]
        
        # 显示AI回复
        st.chat_message("assistant").write(result["messages"][-1].content)
        
        # 显示意图分析结果
        if "intent" in result["context"]:
            st.sidebar.json(result["context"]["intent"])

if __name__ == "__main__":
    main() 