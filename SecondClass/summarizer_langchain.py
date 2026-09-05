from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from util.scraper import fetch_website_contents
from util.config import get_api_key

api_key = get_api_key("OPENAI_API_KEY")

prompt = ChatPromptTemplate.from_template(  # ①
    "Give a short, friendly summary of this website:\n\n{website}"
)

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=api_key,
)  # ②

parser = StrOutputParser()  # ③

chain = prompt | model | parser  # ④


def summarize(url):
    return chain.invoke({"website": fetch_website_contents(url)})  # ⑤


print(summarize("https://anthropic.com"))
