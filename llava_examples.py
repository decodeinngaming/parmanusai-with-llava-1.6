#!/usr/bin/env python3
"""
LLaVA 1.6 Usage Example
This example demonstrates how to use your LLaVA 1.6 model for both text and vision tasks.
"""

import asyncio
import base64
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.llm import LLMOptimized
from app.logger import logger


async def text_conversation_example():
    """Example of text-only conversation with LLaVA 1.6."""
    print("💬 Text Conversation Example")
    print("-" * 30)

    llm = LLMOptimized()

    # Example conversation
    messages = [
        {
            "role": "system",
            "content": "You are LLaVA 1.6, a helpful multimodal AI assistant.",
        },
        {"role": "user", "content": "What are your capabilities as an AI assistant?"},
    ]

    print("User: What are your capabilities as an AI assistant?")
    response = await llm.ask(messages)
    print(f"LLaVA 1.6: {response}")

    # Continue conversation
    messages.append({"role": "assistant", "content": response})
    messages.append({"role": "user", "content": "Can you help me with coding tasks?"})

    print("\nUser: Can you help me with coding tasks?")
    response = await llm.ask(messages)
    print(f"LLaVA 1.6: {response}")


async def vision_conversation_example():
    """Example of vision conversation with LLaVA 1.6."""
    print("\n👁️ Vision Conversation Example")
    print("-" * 30)

    llm = LLMOptimized()

    if not llm.vision_enabled:
        print("❌ Vision capabilities are not enabled")
        return

    # Example with a simple 1x1 pixel image (base64 encoded)
    # In practice, you would use a real image
    tiny_image_b64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I'm testing your vision capabilities. What would you typically expect to see in an office environment?",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{tiny_image_b64}"},
                },
            ],
        }
    ]

    print(
        "User: I'm testing your vision capabilities. What would you typically expect to see in an office environment? [Image attached]"
    )
    response = await llm.ask(messages)
    print(f"LLaVA 1.6: {response}")


async def streaming_example():
    """Example of streaming response with LLaVA 1.6."""
    print("\n🌊 Streaming Response Example")
    print("-" * 30)

    llm = LLMOptimized()

    messages = [
        {
            "role": "user",
            "content": "Write a short story about a robot discovering emotions. Keep it under 100 words.",
        }
    ]

    print(
        "User: Write a short story about a robot discovering emotions. Keep it under 100 words."
    )
    print("LLaVA 1.6 (streaming): ", end="", flush=True)

    # Stream the response
    response_generator = await llm.ask(messages, stream=True)
    full_response = ""

    if hasattr(response_generator, "__call__"):
        # It's a generator function, call it to get the actual generator
        response_generator = response_generator()

    try:
        for chunk in response_generator:
            print(chunk, end="", flush=True)
            full_response += chunk
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")

    print("\n")  # New line after streaming


async def multimodal_analysis_example():
    """Example of analyzing multimodal content."""
    print("\n🔍 Multimodal Analysis Example")
    print("-" * 30)

    llm = LLMOptimized()

    # Example of analyzing text with image context
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze the relationship between visual design and user experience in modern applications.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                    },
                },
            ],
        }
    ]

    print(
        "User: Analyze the relationship between visual design and user experience in modern applications. [UI mockup image attached]"
    )

    # Count tokens for multimodal message
    token_count = llm.count_message_tokens(messages)
    print(
        f"📊 Estimated tokens: {token_count} (including {llm.LLAVA_VISION_TOKENS} vision tokens)"
    )

    response = await llm.ask(messages)
    print(f"LLaVA 1.6: {response}")


async def model_info_example():
    """Display model information and capabilities."""
    print("\n📋 Model Information")
    print("-" * 30)

    llm = LLMOptimized()

    print(f"Model: {llm.model}")
    print(f"Model Path: {llm.model_path}")
    print(f"LLaVA Model Detected: {llm.is_llava_model}")
    print(f"Vision Enabled: {llm.vision_enabled}")
    print(f"Max Tokens: {llm.max_tokens}")
    print(f"Temperature: {llm.temperature}")
    print(f"CUDA Available: {llm.gpu_manager.cuda_available}")

    if llm.is_llava_model:
        print(f"LLaVA Image Tag: {llm.LLAVA_IMAGE_TAG}")
        print(f"LLaVA Vision Tokens: {llm.LLAVA_VISION_TOKENS}")

    # Get memory statistics
    memory_stats = llm.get_memory_stats()
    print(f"Memory Stats: {memory_stats}")


async def main():
    """Main example function."""
    print("🤖 LLaVA 1.6 Usage Examples")
    print("=" * 40)

    try:
        # Show model information
        await model_info_example()

        # Text conversation example
        await text_conversation_example()

        # Vision conversation example
        await vision_conversation_example()

        # Streaming example
        await streaming_example()

        # Multimodal analysis example
        await multimodal_analysis_example()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
