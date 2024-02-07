import os
import logging
import json

from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.openai_functions import (
    create_structured_output_runnable,
)
from langchain.globals import set_debug, set_verbose

import data_models


class Chains:
    def __init__(self, logger=None):
        load_dotenv()
        set_debug(True)
        set_verbose(True)
        self.logger = logger or logging
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo", temperature=0, openai_api_key=os.getenv("OPENAIKEY"))
        self.encode = data_models.Encoder().encode

    class BillingDataJson:
        def __init__(self):
            pass
        """Chain: Gets structured data from the given text."""

        def structured_data(self):
            prompt = PromptTemplate.from_template(
                """Extract information from the following text: {raw_text}"""
            )
            return create_structured_output_runnable(data_models.BillingValues, Chains().llm, prompt)

        def run(self, text: str):
            chain = self.structured_data()
            structured_data = chain.invoke({"raw_text": text})
            string = Chains().encode(structured_data)
            return json.loads(string)


if __name__ == "__main__":
    pass
    # text_path = "/Users/loom23/Sites/ibt-scripts/essen/IBT/page_2.txt"
    # with open(text_path, "r") as text_file:
    #     text = text_file.read()
    #     start_time = time.time()

    #     response = Chains.BillingDataJson().run(text)

    #     end_time = time.time()
    #     duration = end_time - start_time
    #     print(response)
    #     print(f"Duration: {duration} seconds")
