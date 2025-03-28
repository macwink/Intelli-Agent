# tool calling chain
import json
from collections import defaultdict
from typing import Any, Dict, List

from langchain.prompts import ChatPromptTemplate
from langchain.tools.base import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from shared.constant import LLMModelType, LLMTaskType, MessageType

from ...utils.prompt_utils import get_prompt_template
from ...utils.time_utils import get_china_now
from ..models import ChatModel
from ..models.model_config import (
    BEDROCK_MODEL_CONFIGS,
    OPENAI_MODEL_CONFIGS,
    QWEN25_MODEL_CONFIGS,
    SILICONFLOW_DEEPSEEK_MODEL_CONFIGS,
)
from . import LLMChain
from langchain_core.documents import Document

class ToolCallingBaseChain(LLMChain):
    
    intent_type = LLMTaskType.TOOL_CALLING_API
    default_model_kwargs = {
        "max_tokens": 2000,
        "temperature": 0.1,
        "top_p": 0.9
    }

    @classmethod
    def create_chat_history(cls, x):
        chat_history = x['chat_history'] + \
            [{"role": MessageType.HUMAN_MESSAGE_TYPE, "content": x['query']}] + \
            x['agent_tool_history']
        return chat_history

    @classmethod
    def get_common_system_prompt(cls, system_prompt_template: str, all_knowledge_retrieved_list=None):
        all_knowledge_retrieved_list:List[Document] = all_knowledge_retrieved_list or []
        all_knowledge_retrieved = "\n\n".join(doc.page_content for doc in all_knowledge_retrieved_list)
        now = get_china_now()
        date_str = now.strftime("%Y年%m月%d日")
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[now.weekday()]
        system_prompt = system_prompt_template.format(
            date=date_str, weekday=weekday, context=all_knowledge_retrieved)
        return system_prompt

    @classmethod
    def bind_tools(cls, llm: BaseChatModel, tools: List[BaseTool], fewshot_examples=None, fewshot_template=None):
        tools = [tool.model_copy() for tool in tools]
        if not fewshot_examples:
            if getattr(llm, "enable_any_tool_choice", False):
                return llm.bind_tools(tools, tool_choice=llm.any_tool_choice_value )
            return llm.bind_tools(tools)

        # add fewshot examples to tool description
        tools_map = {tool.name: tool for tool in tools}

        # group fewshot examples
        fewshot_examples_grouped = defaultdict(list)
        for example in fewshot_examples:
            fewshot_examples_grouped[example['name']].append(example)

        for tool_name, examples in fewshot_examples_grouped.items():
            tool = tools_map[tool_name]
            tool.description += "\n\nHere are some examples where this tool are called:\n"
            examples_strs = []
            for example in examples:
                params_str = json.dumps(example['kwargs'], ensure_ascii=False)
                examples_strs.append(
                    fewshot_template.format(
                        query=example['query'],
                        args=params_str
                    )
                )

            tool.description += "\n\n".join(examples_strs)

        if getattr(llm, "enable_any_tool_choice", False):
            return llm.bind_tools(tools, tool_choice=llm.any_tool_choice_value)
        return llm.bind_tools(tools)

    @classmethod
    def create_chain(cls, model_kwargs=None, **kwargs):
        model_kwargs = model_kwargs or {}
        tools: list = kwargs['tools']
        assert all(isinstance(tool, BaseTool) for tool in tools), tools
        fewshot_examples = kwargs.get('fewshot_examples', [])
        agent_system_prompt = get_prompt_template(
            model_id=cls.model_id,
            task_type=cls.intent_type,
            prompt_name="agent_system_prompt"
        ).prompt_template

        agent_system_prompt = kwargs.get(
            "agent_system_prompt", None) or agent_system_prompt

        all_knowledge_retrieved_list = kwargs.get(
            'all_knowledge_retrieved_list', [])
        agent_system_prompt = cls.get_common_system_prompt(
            agent_system_prompt, all_knowledge_retrieved_list
        )

        # tool fewshot prompt
        tool_fewshot_prompt = get_prompt_template(
            model_id=cls.model_id,
            task_type=cls.intent_type,
            prompt_name="tool_fewshot_prompt"
        ).prompt_template
        tool_fewshot_prompt = kwargs.get(
            'tool_fewshot_prompt', None) or tool_fewshot_prompt

        model_kwargs = {**cls.default_model_kwargs, **model_kwargs}

        llm = ChatModel.get_model(
            model_id=cls.model_id,
            model_kwargs=model_kwargs,
            **kwargs
        )

        llm = cls.bind_tools(llm, tools, fewshot_examples,
                             fewshot_template=tool_fewshot_prompt)

        tool_calling_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=agent_system_prompt),
                ("placeholder", "{chat_history}"),
                ("human", "{query}"),
                ("placeholder", "{agent_tool_history}"),

            ]
        )
        chain = tool_calling_template | llm
        return chain


ToolCallingBaseChain.create_for_chains(BEDROCK_MODEL_CONFIGS, LLMTaskType.TOOL_CALLING_API)
ToolCallingBaseChain.create_for_chains(OPENAI_MODEL_CONFIGS, LLMTaskType.TOOL_CALLING_API)
ToolCallingBaseChain.create_for_chains(QWEN25_MODEL_CONFIGS, LLMTaskType.TOOL_CALLING_API)
ToolCallingBaseChain.create_for_chains(SILICONFLOW_DEEPSEEK_MODEL_CONFIGS, LLMTaskType.TOOL_CALLING_API)


# class ChatGPT35ToolCallingChain(ToolCallingBaseChain):
#     model_id = LLMModelType.GPT3D5TURBO0125

