import retriever as retriever
from retriever import QueryDocumentRetriever, QueryQuestionRetriever,index_results_format
from constant import IntentType
from functools import partial
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableBranch, RunnableLambda
from llm_utils import Claude21
import re 
from prompt_template import INTENT_RECOGINITION_PROMPT_TEMPLATE_CLUADE21,INTENT_RECOGINITION_EXAMPLE_TEMPLATE
import os 
import json 
from random import Random
abs_file_dir = os.path.dirname(__file__)

intent_map = {
    "闲聊": IntentType.CHAT,
    "知识问答": IntentType.KNOWLEDGE_QA
}

def create_few_shot_example_string(examples):
    example_strs = []
    for example in examples:
        example_strs.append(
            INTENT_RECOGINITION_EXAMPLE_TEMPLATE.format(
                label=example['label'],
                query=example['query']
                )
        )
    return '\n'.join(example_strs)

def create_all_labels_string(labels):
    label_strs = []
    for i,label in enumerate(labels):
        label_strs.append(f"({i}): {label}")
    return "\n".join(label_strs)


def postprocess(output:str):
    output = f'<category>{output}'
    r = re.findall('<category>(.*?)</category>',output,re.S)
    assert r, output 
    r = [rr.strip() for rr in r]
    r = [rr for rr in r if rr]
    return r[0] 

def get_intent_with_claude(
        query,
        chit_chat_examples_path = os.path.join(abs_file_dir,"intent_examples/chit_chat.example"),
        knowledge_qa_examples_path = os.path.join(abs_file_dir,"intent_examples/chit_chat.example"),
        few_shot_num=5
        ):
        chit_chat_examples = [{"label":e['intention'], 'query': e['query']} for e in json.load(open(chit_chat_examples_path))]
        knowledge_qa_examples = [{"label":e['intention'], 'query': e['query']} for e in json.load(open(knowledge_qa_examples_path))]
        chit_chat_examples_fs = Random(42).choices(chit_chat_examples,k=few_shot_num)
        knowledge_qa_examples_fs = Random(42).choices(knowledge_qa_examples,k=few_shot_num)
        examples_fs = chit_chat_examples_fs + knowledge_qa_examples_fs 
        labels = list(set([e['label'] for e in examples_fs])) 
        prompt = INTENT_RECOGINITION_PROMPT_TEMPLATE_CLUADE21.format(
            few_shot_examples = create_few_shot_example_string(examples_fs),
            all_labels = create_all_labels_string(labels),
            query=query)
        
        r = Claude21.create_model(model_kwargs={'temprature':0.0}).predict(
            prompt
        )
        predict_label = postprocess(r)
        return intent_map[predict_label]

def get_intent(query,intent_type,qq_index=None):
    assert IntentType.has_value(intent_type),intent_type
    if intent_type != IntentType.AUTO:
        return intent_type 
    
    return get_intent_with_claude(query)


def auto_intention_recoginition_chain(index_q_q, q_q_match_threshold=0.9):
    """

    Args:
        index_q_q (_type_): _description_
        q_q_match_threshold (float, optional): _description_. Defaults to 0.9.
    """
    def get_custom_intent_type(x):
        assert IntentType.has_value(x["intent_type"]), x["intent_type"]
        return x["intent_type"]
    
    q_q_retriever = QueryQuestionRetriever(
        index=index_q_q, vector_field="vector_field", source_field="file_path", size=5)
     
    strict_q_q_chain = q_q_retriever | RunnableLambda(partial(index_results_format,threshold=q_q_match_threshold))
    
    intent_auto_recognition_chain = RunnableParallel({
        "query": lambda x: x['query'],
        "q_q_match_res": strict_q_q_chain
    }) | RunnableBranch(
        (lambda x: len(x['q_q_match_res']["answer"]) > 0, RunnableLambda(lambda x: IntentType.STRICT_QQ.value)),
        RunnableLambda(lambda x: get_intent_with_claude(x['query']))
    )

    chain = RunnableBranch(
        (lambda x:x["intent_type"] == IntentType.AUTO.value,intent_auto_recognition_chain),
        RunnableLambda(get_custom_intent_type)
    )

    return chain


    








