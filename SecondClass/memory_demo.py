from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from util.config import get_api_key

api_key = get_api_key("OPENAI_API_KEY")


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a friendly tutor."),  # ① personality, like Class 1
        MessagesPlaceholder("history"),  # ② past turns park here
        ("human", "{question}"),  # ③ the new question
    ]
)

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=api_key,
)
parser = StrOutputParser()

chain = prompt | model | parser

history = [HumanMessage("My name is Ruby 420."), AIMessage("Hi Ruby 420!")]
print(chain.invoke({"history": history, "question": "What's my name?"}))
