# hyde  
import json 
import os
import re
import sys
from random import Random
from functools import lru_cache

from .llm_chain_base import LLMChain
from ...constant import HYDE_TYPE
from ..llm_models import Model as LLM_Model

from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableBranch, RunnableLambda
from .chat_chain import Iternlm2Chat7BChatChain
from ..llm_chains import LLMChain





WEB_SEARCH_TEMPLATE = """Please write a passage to answer the question 
Question: {query}
Passage:"""
hyde_web_search_template = PromptTemplate(template=WEB_SEARCH_TEMPLATE, input_variables=["query"])


class Claude2HydeChain(LLMChain):
    model_id = 'anthropic.claude-v2'
    intent_type = HYDE_TYPE

    default_model_kwargs = {
      "temperature": 0.5,
      "max_tokens_to_sample": 1000,
      "stop_sequences": [
        "\n\nHuman:"
      ]
    }

    @classmethod
    def create_chain(cls, model_id, model_kwargs=None, **kwargs):
        query_key = kwargs.pop('query_key','query')
        model_kwargs = model_kwargs or {}
        model_kwargs = {**cls.default_model_kwargs,**model_kwargs}

        llm = LLM_Model.get_model(
        model_id=model_id,
          model_kwargs=model_kwargs,
          return_chat_model=False
        )
        chain = RunnablePassthrough.assign(
            hyde_doc = RunnableLambda(lambda x: hyde_web_search_template.invoke({"query": x[query_key]})) | llm
        )
        return chain

class Claude21HydeChain(Claude2HydeChain):
    model_id = 'anthropic.claude-v2:1'


class ClaudeInstanceHydeChain(Claude2HydeChain):
    model_id = 'anthropic.claude-instant-v1'



internlm2_meta_instruction = "You are a helpful AI Assistant."

class Iternlm2Chat7BHydeChain(Iternlm2Chat7BChatChain):
    model_id = "internlm2-chat-7b"
    intent_type = HYDE_TYPE

    default_model_kwargs = {
        "temperature":0.1,
        "max_new_tokens": 200
    }

    @classmethod
    def create_prompt(cls,x):
        query = f"""Please write a brief passage to answer the question. \nQuestion: {prompt}"""
        prompt = cls.build_prompt(
            query = query,
            meta_instruction=internlm2_meta_instruction,
        ) + "Passage: "
        return prompt

class Iternlm2Chat20BHydeChain(Iternlm2Chat7BHydeChain):
    model_id = "internlm2-chat-20b"
    intent_type = HYDE_TYPE


    









