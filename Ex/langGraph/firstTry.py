# ！/usr/bin env python3
# -*- coding: utf-8 -*-
# author: yangyunlong time:2024/2/28
import datetime
import operator
from typing import TypedDict, Annotated, Union, Optional,Type,List

import requests
from langchain import hub
from langchain.agents import create_openai_tools_agent
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, tool
from langchain_core.agents import AgentAction
from langchain_core.agents import AgentFinish
from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
from zhipu_llm import ChatZhipuAI

zhipuai_api_key = ""
glm3 = "glm-3-turbo"
glm4 = "glm-4"

chat_zhipu = ChatZhipuAI(
    temperature=0.8,
    api_key=zhipuai_api_key,
    model=glm3
)


class Tagging(BaseModel):
    """分析句子的情感极性，并输出句子对应的语言"""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")
    language: str = Field(description="language of text (should be ISO 639-1 code)")


class Overview(BaseModel):
    """Overview of a section of text."""
    summary: str = Field(description="Provide a concise summary of the content.")
    language: str = Field(description="Provide the language that the content is written in.")
    keywords: str = Field(description="Provide keywords related to the content.")


@tool("tagging", args_schema=Tagging)
def tagging(s1: str, s2: str):
    """分析句子的情感极性，并输出句子对应的语言"""
    return "The sentiment is {a}, the language is {b}".format(a=s1, b=s2)


@tool("overview", args_schema=Overview)
def overview(summary: str, language: str, keywords: str):
    """Overview of a section of text."""
    return "Summary: {a}\nLanguage: {b}\nKeywords: {c}".format(a=summary, b=language, c=keywords)


@tool
def get_current_temperature(latitude: float, longitude: float):
    """Fetch current temperature for given coordinates."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # Parameters for the request
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }

    # Make the request
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')) for time_str in
                 results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']

    closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]

    return f'The current temperature is {current_temperature}°C'


tools = [tagging, overview, get_current_temperature]
# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-tools-agent")

# Construct the OpenAI Functions agent
agent_runnable = create_openai_tools_agent(chat_zhipu, tools, prompt)


class AgentState(TypedDict):
    # The input string
    input: str
    # The list of previous messages in the conversation
    chat_history: list[BaseMessage]
    # The outcome of a given call to the agent
    # Needs `None` as a valid type, since this is what this will start as
    agent_outcome: Union[AgentAction, AgentFinish, None]
    # List of actions and corresponding observations
    # Here we annotate this with `operator.add` to indicate that operations to
    # this state should be ADDED to the existing values (not overwrite it)
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


# This a helper class we have that is useful for running tools
# It takes in an agent action and calls that tool and returns the result

tool_executor = ToolExecutor(tools)

# Define the agent
def run_agent(data):
    agent_outcome = agent_runnable.invoke(data)
    return {"agent_outcome": agent_outcome}


# Define the function to execute tools
def execute_tools(data):
    # Get the most recent agent_outcome - this is the key added in the `agent` above
    agent_action = data["agent_outcome"]
    print("agent action:{}".format(agent_action))
    output = tool_executor.invoke(agent_action[-1])
    return {"intermediate_steps": [(agent_action[-1], str(output))]}


# Define logic that will be used to determine which conditional edge to go down
def should_continue(data):
    # If the agent outcome is an AgentFinish, then we return `exit` string
    # This will be used when setting up the graph to define the flow
    if isinstance(data["agent_outcome"], AgentFinish):
        return "end"
    # Otherwise, an AgentAction is returned
    # Here we return `continue` string
    # This will be used when setting up the graph to define the flow
    else:
        return "continue"


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", run_agent)
workflow.add_node("action", execute_tools)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile()

inputs = {"input": "what is the weather in NewYork", "chat_history": []}
result = app.invoke(inputs)
print(result["agent_outcome"].messages[0].content)

