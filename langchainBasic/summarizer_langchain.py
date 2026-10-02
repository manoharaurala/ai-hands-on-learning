from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from aiWebsiteSummarizer.webScraper import fetch_website_contents

load_dotenv()
prompt = ChatPromptTemplate.from_template(  # ①
    "Give a short, friendly summary of this website:\n\n{website}"
)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # ②

parser = StrOutputParser()  # ③

chain = prompt | model | parser  # ④


def summarize(url):
    return chain.invoke({"website": fetch_website_contents(url)})  # ⑤


print(summarize("https://anthropic.com"))
