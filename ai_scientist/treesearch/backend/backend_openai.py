import json
import logging
import time
import os

from .utils import FunctionSpec, OutputType, opt_messages_to_list, backoff_create
from funcy import notnone, once, select_values
import openai
from rich import print

logger = logging.getLogger("ai-scientist")

_client: openai.OpenAI = None  # type: ignore
_current_model: str = None  # track current model to recreate client if needed

OPENAI_TIMEOUT_EXCEPTIONS = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.InternalServerError,
)


def _setup_openai_client(model: str = None):
    """Setup OpenAI client based on the model being used"""
    global _client, _current_model
    
    # Only recreate client if model has changed or client doesn't exist
    if _client is None or model != _current_model:
        if model and ("deepseek" in model):
            # Use DeepSeek API
            deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not deepseek_api_key:
                raise ValueError(
                    "DEEPSEEK_API_KEY environment variable is required for DeepSeek models. "
                    "Please set it with: export DEEPSEEK_API_KEY='your_api_key_here'"
                )
            _client = openai.OpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com",
                max_retries=0
            )
            logger.info(f"Setup DeepSeek client for model: {model}")
        else:
            # Use default OpenAI API
            _client = openai.OpenAI(max_retries=0)
            logger.info(f"Setup OpenAI client for model: {model}")
        
        _current_model = model


def query(
    system_message: str | None,
    user_message: str | None,
    func_spec: FunctionSpec | None = None,
    **model_kwargs,
) -> tuple[OutputType, float, int, int, dict]:
    model = model_kwargs.get("model", "")
    _setup_openai_client(model)
    filtered_kwargs: dict = select_values(notnone, model_kwargs)  # type: ignore

    messages = opt_messages_to_list(system_message, user_message)

    if func_spec is not None:
        filtered_kwargs["tools"] = [func_spec.as_openai_tool_dict]
        # force the model to use the function
        filtered_kwargs["tool_choice"] = func_spec.openai_tool_choice_dict

    t0 = time.time()
    completion = backoff_create(
        _client.chat.completions.create,
        OPENAI_TIMEOUT_EXCEPTIONS,
        messages=messages,
        **filtered_kwargs,
    )
    req_time = time.time() - t0

    choice = completion.choices[0]

    if func_spec is None:
        output = choice.message.content
    else:
        assert (
            choice.message.tool_calls
        ), f"function_call is empty, it is not a function call: {choice.message}"
        assert (
            choice.message.tool_calls[0].function.name == func_spec.name
        ), "Function name mismatch"
        try:
            print(f"[cyan]Raw func call response: {choice}[/cyan]")
            output = json.loads(choice.message.tool_calls[0].function.arguments)
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding the function arguments: {choice.message.tool_calls[0].function.arguments}"
            )
            raise e

    in_tokens = completion.usage.prompt_tokens
    out_tokens = completion.usage.completion_tokens

    info = {
        "system_fingerprint": completion.system_fingerprint,
        "model": completion.model,
        "created": completion.created,
    }

    return output, req_time, in_tokens, out_tokens, info
