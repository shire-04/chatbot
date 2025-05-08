from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

LANGSMITH_TRACING=True
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="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"
LANGSMITH_PROJECT="pr-diligent-whelp-86"
OPENAI_API_KEY="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"

model = ChatOpenAI(
openai_api_key="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",
openai_api_base="https://openrouter.ai/api/v1",
model_name = "deepseek/deepseek-chat-v3-0324:free"
)
# # assistant和user交替进行，以user结尾
# messages = [
#     {
#         "role": "system",
#         "content": "你是一个数学计算助手，可以使用计算器函数"
#     },
#     {
#         "role": "user",
#         "content": "请计算 25 的平方根"
#     },
#     {
#         "role": "assistant",
#         "content": "让我使用计算器函数来帮您计算"
#     },
#     {
#         "role": "user",
#         "content": "那16的平方根呢？"
#     }
# ]
# response =model.invoke(messages)
# print(response.content)

prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
# chain，使用|连接多个组件
gen_chain = prompt | model | StrOutputParser()
analysis_prompt = ChatPromptTemplate.from_template("is this a funny joke? {joke}")
analysis_chain =  analysis_prompt | model | StrOutputParser()
def union(input):
    print("\n*****start****")
    print(input)
    print("******end****")
    return {"joke":input}
 #chain = gen_chain | (lambda input: {"joke": input}) | analysis_chain
chain = gen_chain | (union) | analysis_chain
result = chain.invoke({"topic": "bears"})
print(result)