# LangChain Integration

> **Purpose**: ChatOpenRouter class and LCEL streaming patterns for LangChain applications
> **MCP Validated**: 2026-01-28

## When to Use

- Building LangChain applications with multiple LLM providers
- Creating chains and agents that need provider flexibility
- Implementing LCEL (LangChain Expression Language) pipelines
- Adding tool calling through OpenRouter's unified API

## Implementation

```python
import os
from typing import Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# =============================================================================
# Custom ChatOpenRouter Class
# =============================================================================

class ChatOpenRouter(ChatOpenAI):
    """LangChain ChatModel for OpenRouter API."""

    def __init__(
        self,
        model: str = "anthropic/claude-4-sonnet",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "https://localhost"),
                "X-Title": os.getenv("APP_NAME", "LangChain App")
            },
            **kwargs
        )


# =============================================================================
# Basic Usage
# =============================================================================

def basic_chat():
    """Simple chat using ChatOpenRouter."""
    llm = ChatOpenRouter(model="anthropic/claude-4-sonnet")

    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Explain quantum computing briefly.")
    ]

    response = llm.invoke(messages)
    return response.content


# =============================================================================
# LCEL Chain with Streaming
# =============================================================================

def streaming_chain():
    """LCEL chain with streaming output."""
    llm = ChatOpenRouter(
        model="anthropic/claude-4-sonnet",
        streaming=True
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical writer."),
        ("user", "{input}")
    ])

    chain = prompt | llm | StrOutputParser()

    # Stream response
    for chunk in chain.stream({"input": "Explain REST APIs"}):
        print(chunk, end="", flush=True)


# =============================================================================
# Multi-Model Comparison
# =============================================================================

def compare_models(question: str) -> dict:
    """Compare responses from multiple models."""
    models = [
        "anthropic/claude-4-sonnet",
        "openai/gpt-4o",
        "google/gemini-2.0-flash"
    ]

    results = {}

    for model_name in models:
        llm = ChatOpenRouter(model=model_name, temperature=0.0)
        response = llm.invoke([HumanMessage(content=question)])
        results[model_name] = response.content

    return results


# =============================================================================
# Tool Calling Support
# =============================================================================

def tool_calling_example():
    """Example with tool/function calling."""
    from langchain_core.tools import tool

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Weather in {city}: 72F, sunny"

    llm = ChatOpenRouter(model="openai/gpt-4o")
    llm_with_tools = llm.bind_tools([get_weather])

    response = llm_with_tools.invoke(
        [HumanMessage(content="What's the weather in Tokyo?")]
    )
    return response
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `model` | claude-4-sonnet | Model identifier with provider |
| `temperature` | 0.7 | Response randomness |
| `streaming` | false | Enable streaming mode |
| `OPENROUTER_API_KEY` | Required | Environment variable |

## Example Usage

```python
# Basic usage
response = basic_chat()
print(response)

# Streaming chain
streaming_chain()

# Model comparison
results = compare_models("What is machine learning?")
for model, answer in results.items():
    print(f"\n{model}:\n{answer[:200]}...")

# With cost optimization
llm = ChatOpenRouter(
    model="openai/gpt-4o:floor",  # Cheapest provider
    temperature=0.0
)

# With provider routing
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="openai/gpt-4o",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_kwargs={
        "provider": {
            "sort": "throughput",
            "order": ["OpenAI", "Anthropic"]
        }
    }
)
```

## See Also

- [python-sdk-integration.md](../patterns/python-sdk-integration.md)
- [streaming.md](../concepts/streaming.md)
- [model-selection.md](../concepts/model-selection.md)
