from typing import Any
from shared.constant import LLMTaskType
from ..models.model_config import ModelConfig

class LLMChainMeta(type):
    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)
        if name == "LLMChain" or name.endswith("BaseChain") \
            or name.lower().endswith("basechain"):
            return new_cls
        new_cls.model_map[new_cls.get_chain_id()] = new_cls
        return new_cls


class LLMChain(metaclass=LLMChainMeta):
    model_map = {}

    @classmethod
    def get_chain_id(cls):
        return cls._get_chain_id(cls.model_id, cls.intent_type)

    @staticmethod
    def _get_chain_id(model_id, intent_type):
        return f"{model_id}__{intent_type}"

    @classmethod
    def get_chain(cls, model_id, intent_type, model_kwargs=None, **kwargs):
        # dynamic import
        _load_module(intent_type)
        return cls.model_map[cls._get_chain_id(model_id, intent_type)].create_chain(
            model_kwargs=model_kwargs, **kwargs
        )

    @classmethod
    def model_id_to_class_name(cls, model_id: str, intent_type: str) -> str:
        """Convert model ID to a valid Python class name.
        
        Examples:
            anthropic.claude-3-haiku-20240307-v1:0 -> Claude3Haiku20240307V1{IntentType}Chain
        """
        # Remove version numbers and vendor prefixes
        name = str(model_id).split(':')[0]
        name = name.split('.')[-1]
        parts = name.replace('_', '-').split('-')

        cleaned_parts = []
        for part in parts:
            if any(c.isdigit() for c in part):
                cleaned = ''.join(c.upper() if i == 0 or part[i-1] in '- ' else c
                                  for i, c in enumerate(part))
            else:
                cleaned = part.capitalize()
            cleaned_parts.append(cleaned)

        return ''.join(cleaned_parts) + intent_type.capitalize() + "Chain"

    @classmethod
    def create_for_chain(cls, model_config: ModelConfig, intent_type: str):
        """Factory method to create a chain for a specific model"""
        # config = MODEL_CONFIGS[model_id]
        config = model_config
        model_id = model_config.model_id

        # Create a new class dynamically
        chain_class = type(
            f"{cls.model_id_to_class_name(model_id, intent_type)}",
            (cls,),
            {
                "intent_type": intent_type,
                "model_id": config.model_id,
                "default_model_kwargs": config.default_model_kwargs,
            }
        )
        return chain_class
    
    
    @classmethod
    def create_for_chains(cls, model_configs: list[ModelConfig], intent_type: str):
        for config in model_configs:
            cls.create_for_chain(config,intent_type=intent_type)



def _import_conversation_summary_chain():
    from . import conversation_summary_chain
    # from .conversation_summary_chain import (
    #     Internlm2Chat7BConversationSummaryChain,
    #     Internlm2Chat20BConversationSummaryChain,
    # )


def _import_rag_chain():
    from . import rag_chain
    


def _import_chat_chain():
    from . import chat_chain


def _import_tool_calling_chain_api():
    from . import tool_calling_chain_api


def _load_module(intent_type):
    assert intent_type in CHAIN_MODULE_LOAD_FN_MAP, (
        intent_type, CHAIN_MODULE_LOAD_FN_MAP)
    CHAIN_MODULE_LOAD_FN_MAP[intent_type]()


CHAIN_MODULE_LOAD_FN_MAP = {
    LLMTaskType.CHAT: _import_chat_chain,
    LLMTaskType.CONVERSATION_SUMMARY_TYPE: _import_conversation_summary_chain,
    # LLMTaskType.INTENT_RECOGNITION_TYPE: _import_intention_chain,
    LLMTaskType.RAG: _import_rag_chain,
    # LLMTaskType.QUERY_TRANSLATE_TYPE: _import_translate_chain,
    # LLMTaskType.MKT_CONVERSATION_SUMMARY_TYPE: _import_mkt_conversation_summary_chains,
    # LLMTaskType.MTK_RAG: _import_mkt_rag_chain,
    # LLMTaskType.STEPBACK_PROMPTING_TYPE: _import_stepback_chain,
    # LLMTaskType.HYDE_TYPE: _import_hyde_chain,
    # LLMTaskType.QUERY_REWRITE_TYPE: _import_query_rewrite_chain,
    # LLMTaskType.TOOL_CALLING_XML: _import_tool_calling_chain_claude_xml,
    LLMTaskType.TOOL_CALLING_API: _import_tool_calling_chain_api,
    # LLMTaskType.RETAIL_CONVERSATION_SUMMARY_TYPE: _import_retail_conversation_summary_chain,
    # LLMTaskType.RETAIL_TOOL_CALLING: _import_retail_tool_calling_chain_claude_xml,
    # LLMTaskType.AUTO_EVALUATION: _import_auto_evaluation_chain
}
