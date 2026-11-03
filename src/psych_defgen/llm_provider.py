
"""Common interface for generating responses using different LLM providers."""

from ollama import Client


def generate_llm_response(
    prompt,
    provider="ollama",
    model="qwen2.5:7b",
    api_key=None,
    base_url=None,
    json_mode=False,
    return_usage=False,
):
    """Generate an LLM response with optional token-usage metadata."""

    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt

    provider = provider.lower().strip()

    if provider == "ollama":
        client = Client(
            host=base_url or "http://localhost:11434",
            timeout=300.0,
        )

        response = client.chat(
            model=model,
            messages=messages,
            format="json" if json_mode else None,
            options={"temperature": 0},
        )

        content = (response.message.content or "").strip()

        input_tokens = response.prompt_eval_count
        output_tokens = response.eval_count

    elif provider == "openrouter":
        from openai import OpenAI

        if not api_key:
            raise ValueError(
                "OpenRouter API key is required. "
                "Provide your own API key to use OpenRouter."
            )

        client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1",
            timeout=300.0,
        )

        kwargs = {
            "model": model,
            "messages": messages,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        content = (response.choices[0].message.content or "").strip()

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None

    elif provider == "custom":
        from openai import OpenAI

        if not base_url:
            raise ValueError(
                "A custom LLM API endpoint is required."
            )

        if not model:
            raise ValueError(
                "A model identifier is required."
            )

        client = OpenAI(
            api_key=api_key or "not-required",
            base_url=base_url,
            timeout=300.0,
        )

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        content = (response.choices[0].message.content or "").strip()

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    if not return_usage:
        return content

    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )

    return {
        "text": content,
        "usage": {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        },
    }
