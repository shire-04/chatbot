# Ensure your VertexAI credentials are configured

from langchain.chat_models import init_chat_model

model = init_chat_model("gemini-2.0-flash-001", model_provider="google_vertexai")
model.invoke("Hello, world!")