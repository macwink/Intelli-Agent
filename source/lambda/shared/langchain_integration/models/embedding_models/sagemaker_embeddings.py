import json
import os
from typing import Dict, List

import boto3
from shared.constant import ModelProvider
from shared.utils.logger_utils import get_logger
from langchain_community.embeddings import SagemakerEndpointEmbeddings
from langchain_community.embeddings.sagemaker_endpoint import (
    EmbeddingsContentHandler,
)

from ..model_config import BCE_EMBEDDING_CONFIGS
from . import EmbeddingModel

logger = get_logger("sagemaker_embedding_model")


class SageMakerEmbeddingBaseModel(EmbeddingModel):
    model_provider = ModelProvider.SAGEMAKER

    @classmethod
    def create_content_handler(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def create_model(cls, **kwargs):
        credentials_profile_name = (
            kwargs.get("credentials_profile_name", None)
            or os.environ.get("AWS_PROFILE", None)
            or None
        )
        region_name = (
            kwargs.get("region_name", None)
            or os.environ.get("AWS_REGION", None)
            or None
        )
        aws_access_key_id = os.environ.get("SAGEMAKER_AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.environ.get(
            "SAGEMAKER_AWS_SECRET_ACCESS_KEY", ""
        )
        default_model_kwargs = cls.default_model_kwargs or {}

        content_handler = cls.create_content_handler(**kwargs)

        client = None
        if aws_access_key_id != "" and aws_secret_access_key != "":
            logger.info(
                f"Bedrock Using AWS AKSK from environment variables. Key ID: {aws_access_key_id}"
            )

            client = boto3.client(
                "sagemaker-runtime",
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        model_kwargs = {
            **default_model_kwargs,
            **kwargs.get("model_kwargs", {}),
        }
        model_kwargs = model_kwargs or None
        logger.info("Model kwargs: ")
        logger.info(kwargs)
        target_model = kwargs.get("sagemaker_target_model")
        model_id = kwargs.get("sagemaker_endpoint_name")

        endpoint_kwargs = {}
        if target_model:
            endpoint_kwargs["TargetModel"] = target_model

        endpoint_kwargs = endpoint_kwargs or None

        embedding_model = SagemakerEndpointEmbeddings(
            # model_kwargs=model_kwargs,
            endpoint_kwargs=endpoint_kwargs,
            client=client,
            credentials_profile_name=credentials_profile_name,
            region_name=region_name,
            endpoint_name=model_id,
            content_handler=content_handler,
        )
        return embedding_model


class BceContentHandler(EmbeddingsContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, inputs: List[str], model_kwargs: Dict) -> bytes:
        input_str = json.dumps({"inputs": inputs, **model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> List[List[float]]:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json["sentence_embeddings"]


class SageMakerEmbeddingBCEBaseModel(SageMakerEmbeddingBaseModel):
    @classmethod
    def create_content_handler(cls, **kwargs):
        return BceContentHandler()


SageMakerEmbeddingBCEBaseModel.create_for_models(BCE_EMBEDDING_CONFIGS)
