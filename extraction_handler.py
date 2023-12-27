import os
import logging
import json
from typing import Optional
from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_openai_fn_runnable,
    create_structured_output_chain,
    create_structured_output_runnable,
)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import Sequence
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

from names_handler import NamesFileHandler
import time
import math


class VAT_DataModel(BaseModel):
    """Identifying information about a Value Added Tax."""
    percentage: int = Field(..., description="The percentage of the tax")
    amount_taxed: str = Field(..., description="The amount taxed")
    value_added: str = Field(..., description="The amount of VAT added")
    
class BillingValues_DataModel(BaseModel):
    """Identifying information about all the taxess."""
    date: str = Field(..., description="The date of the billing in the format YYYY-MM-DD")
    location_name: str = Field(..., description="The name of the location")
    address: str = Field(..., description="The address of the location including street, city, and zip code")
    taxes: Sequence[VAT_DataModel] = Field(..., description="The tax sets in the document")
    total_without_tip: str = Field(..., description="The total without tip")
    total_with_tip: str = Field(..., description="The total with tip")
    tip_amount: str = Field(..., description="The tip amount")


class ExtractionHandler():
    def __init__(self, logger=None, names_handler=NamesFileHandler):
        self.logger = logger or logging
        self.llm_model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, api_key=os.getenv("OPENAIKEY"))
        self.names_handler = names_handler
        self.texts = []
        self.conversation_chain = [self.get_structured_data, self.convert_to_json, self.clean_json, self.add_tip, self.add_names]
        self.extracted_text = None

    def _reset_texts(self):
        self.texts = []
        self.extracted_text = None

    """Gets structured data from the given text."""
    def get_structured_data(self, text: str):
        prompt = ChatPromptTemplate.from_messages(
            [(  "system",
                    "You are a world class algorithm for extracting information in structured formats.",
                ),(
                    "human",
                    "Use the given format to extract information from the following input: {input}",
                ),])
        structured_runnable = create_structured_output_runnable(BillingValues_DataModel, self.llm_model, prompt)
        structured_data = structured_runnable.invoke({"input": text})        
        return structured_data

    """ Modifier methods - these methods modify the original json string."""

    """Modifier: Converts the given structured data to json."""
    def convert_to_json(self, structured_data: str):
        prompt = ChatPromptTemplate.from_template("Format this structured data to json: {structured_data}")
        #@todo: is this the right output parser? is there a better one?
        output_parser = StrOutputParser()
        chain = prompt | self.llm_model | output_parser
        return chain.invoke({"structured_data": structured_data})
    
    """Modifier: cleans the given json."""
    def clean_json(self, json_string: str):
        #@todo: strip out only the relavant fields to prevent excessive token usage.
        prompt = ChatPromptTemplate.from_template("For the values: total_without_tip, total_with_tip, and tip_amount, replace commas with periods and remove any characters before or after the float value. For the 'date' field, ensure that it is formatted as YYYY-MM-DD. Very important: don't explain what you're doing, just modify the json - that's it!\n\n{json_string}")
        output_parser = StrOutputParser()
        chain = prompt | self.llm_model | output_parser
        return chain.invoke({"json_string": json_string})

    """Modifier: adds a tip to the given text."""
    def add_tip(self, text: str):
        #@todo: strip out only the relavant fields to prevent excessive token usage.
        prompt = ChatPromptTemplate.from_template("If the tip_amount is zero, calculate a new tip_amount value that is 10% of total_without_tip, then update total_with_tip and tip_amount. If a tip is already included, don't do anything! Very important: don't explain what you're doing, just modify the json - that's it!\n\n{json}")
        output_parser = StrOutputParser()
        chain = prompt | self.llm_model | output_parser
        return chain.invoke({"json": text})
    
    """Modifier: adds names to the given text."""
    def add_names(self, text: str):
        json_data = json.loads(text)
        total = math.floor(float(json_data["total_with_tip"]))
        name_count = math.floor(total / self.names_handler.get_billing_value_per_name(total))
        json_data["names"] = self.names_handler.get_names_billing_sub_set(name_count)
        return json.dumps(json_data)

    """Runs the extraction handler on the given text."""
    def run(self, text: str):
        self._reset_texts()
        self.extracted_text = text
         
        for step in self.conversation_chain:
            start_time = time.time()
            self.extracted_text = step(self.extracted_text)
            end_time = time.time()
            duration = end_time - start_time
            self.texts.append(str(self.extracted_text))
            self.logger.info(f"Step duration: {duration} seconds")
            self.logger.info(f"Current self.texts: {self.texts}")
    

        return json.dumps(self.texts)
    
if __name__ == "__main__":
    nh = NamesFileHandler(directory='/Users/loom23/Sites/ibt-scripts/test/IBT Essen Quittungen 2022')
    nh.run()
    ea = ExtractionHandler(logger, nh)
    text_path = "/Users/loom23/Sites/ibt-scripts/test/IBT Essen Quittungen 2022/page_4.txt"
    with open(text_path, "r") as text_file:
        text = text_file.read()
        start_time = time.time()
        response = ea.run(text)
        end_time = time.time()
        duration = end_time - start_time
        print(response)
        print(f"Duration: {duration} seconds")
