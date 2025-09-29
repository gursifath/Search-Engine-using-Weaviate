import logging
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from config import config

logger = logging.getLogger(__name__)

class OpenAIClientSingleton:
    _instance: Optional['OpenAIClientSingleton'] = None
    _client: Optional[AsyncOpenAI] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Creating new OpenAI client singleton instance")
        return cls._instance

    def __init__(self):
        # Only initialize once, even if __init__ is called multiple times
        if not self._initialized:
            if not config.OPENAI_API_KEY:
                logger.error("OpenAI API key not found in environment variables")
                raise ValueError("OpenAI API key not configured")

            self._client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            self._initialized = True
            logger.info("OpenAI async client initialized successfully")

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            logger.error("OpenAI client not initialized")
            raise RuntimeError("OpenAI client not initialized")
        return self._client

    async def create_response(
        self,
        messages: List[Dict],
        previous_response_id: Optional[str] = None,
        max_tokens: int = 800
    ) -> Dict:
        """
        Create a response using OpenAI Responses API
        """
        try:
            logger.info(f"Creating OpenAI response with {len(messages)} messages")
            logger.debug(f"Messages: {[msg['role'] for msg in messages]}")

            # Convert messages to the format expected by Responses API
            # The last user message becomes the input
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            system_messages = [msg for msg in messages if msg['role'] == 'system']

            if not user_messages:
                raise ValueError("No user messages found")

            # Use the last user message as input
            input_text = user_messages[-1]['content']

            # Use system message as instructions if available
            instructions = system_messages[0]['content'] if system_messages else None

            request_params = {
                "model": "gpt-4o",  # Use gpt-4o as it's more commonly available for Responses API
                "input": input_text,
                "max_output_tokens": max_tokens,
                "temperature": 0.7
            }

            if instructions:
                request_params["instructions"] = instructions

            if previous_response_id:
                request_params["previous_response_id"] = previous_response_id
                logger.debug(f"Including previous_response_id: {previous_response_id}")

            response = await self.client.responses.create(**request_params)

            logger.info(f"OpenAI response created successfully with ID: {response.id}")

            # Extract content from the response
            content = ""
            if hasattr(response, 'output') and response.output:
                # Responses API typically returns output as a list of messages
                if isinstance(response.output, list) and response.output:
                    # Extract text content from the first output message
                    first_output = response.output[0]
                    if hasattr(first_output, 'content'):
                        if isinstance(first_output.content, list) and first_output.content:
                            # Content is a list of content blocks
                            for content_block in first_output.content:
                                if hasattr(content_block, 'text'):
                                    content += content_block.text
                                elif hasattr(content_block, 'content'):
                                    content += str(content_block.content)
                        else:
                            content = str(first_output.content)
                    else:
                        content = str(first_output)
                else:
                    content = str(response.output)
            elif hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content.strip()
            elif hasattr(response, 'content'):
                content = response.content.strip() if isinstance(response.content, str) else str(response.content)
            else:
                # Fallback: convert response to string and extract meaningful content
                response_str = str(response)
                # Try to extract text content from the string representation
                if 'text=' in response_str:
                    import re
                    text_match = re.search(r"text='([^']*)'", response_str)
                    if text_match:
                        content = text_match.group(1)
                    else:
                        content = response_str
                else:
                    content = response_str

            logger.debug(f"Response content length: {len(content)}")

            return {
                "content": content,
                "response_id": response.id,
                "model": getattr(response, 'model', 'gpt-4o'),
                "usage": getattr(response, 'usage', None)
            }

        except Exception as e:
            logger.error(f"Error creating OpenAI response: {str(e)}")
            raise

    async def create_completion(
        self,
        messages: List[Dict],
        max_tokens: int = 50,
        temperature: float = 0.3,
        model: str = "gpt-4o"
    ) -> Dict:
        """
        Create a simple completion using the standard Chat Completions API
        """
        try:
            logger.debug(f"Creating completion with {len(messages)} messages")

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            content = response.choices[0].message.content.strip()
            logger.debug(f"Completion content: '{content}'")

            return {
                "content": content,
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None
            }

        except Exception as e:
            logger.error(f"Error creating completion: {str(e)}")
            raise

    async def list_conversation_responses(
        self,
        conversation_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List conversation items using the input_items API
        """
        try:
            logger.info(f"Listing conversation items for conversation_id: {conversation_id}")

            # Use input_items.list() to get conversation history
            params = {"limit": limit}
            if conversation_id:
                params["conversation_id"] = conversation_id

            responses = await self.client.responses.input_items.list(**params)

            logger.info(f"Retrieved conversation items")
            return [item.model_dump() for item in responses.data] if hasattr(responses, 'data') else []

        except Exception as e:
            logger.error(f"Error listing conversation items: {str(e)}")
            raise

openai_client = OpenAIClientSingleton()