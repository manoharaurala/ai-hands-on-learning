from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a friendly tutor."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
parser = StrOutputParser()

chain1 = prompt | model
chain2 = chain1 | parser

history = [HumanMessage("My pet cat name is Ruby."), AIMessage("Hello Ruby cat.")]

response = chain1.invoke({"input": "Do I have pet", "history": history})
response2 = chain2.invoke({"input": "How many pets I have", "history": history})

print("--------------------")
print(response)
print("--------------------")
print(response2)
print("--------------------")
