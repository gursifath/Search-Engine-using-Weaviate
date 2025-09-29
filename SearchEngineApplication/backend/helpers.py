import uuid
import logging
from datetime import datetime
from typing import Dict, List
from models import ChatMessage, ChatSession, Product
from client import openai_client

logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """Generate a unique session ID"""
    session_id = str(uuid.uuid4())
    logger.debug(f"Generated new session ID: {session_id}")
    return session_id

async def generate_search_query_from_history(messages: List[Dict], new_message: str) -> str:
    """
    Generate a semantic search query using OpenAI based on chat history and new message
    """
    try:
        # Get the last few user messages and assistant responses for context
        conversation_context = []
        for msg in messages[-6:]:  # Last 6 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            # Clean any filter information from display
            if "(with filters:" in content and msg["role"] == "user":
                content = content.split("(with filters:")[0].strip()
            conversation_context.append(f"{role}: {content}")

        # Create the prompt for OpenAI to generate the search query
        prompt = f"""Based on this conversation history and the new user message, generate a concise, effective search query for a product search engine.

Conversation History:
{chr(10).join(conversation_context)}

New User Message: {new_message}

Generate a search query that captures the user's current intent. The query should be:
- Concise (2-6 words typically)
- Focused on products the user is looking for
- Consider the context from previous messages
- Don't include filter information (brand/color) in the query itself

Return only the search query, nothing else."""

        # Make OpenAI call to generate the search query using completions API
        response_data = await openai_client.create_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.3
        )

        generated_query = response_data.get("content", "").strip().strip('"').strip("'")

        if not generated_query:
            # Fallback to new message if OpenAI response is empty
            fallback_query = new_message
            if "(with filters:" in fallback_query:
                fallback_query = fallback_query.split("(with filters:")[0].strip()
            logger.warning(f"Empty OpenAI response, using fallback: '{fallback_query}'")
            return fallback_query

        logger.info(f"Generated search query from conversation: '{generated_query}'")
        return generated_query

    except Exception as e:
        logger.error(f"Error generating search query from history: {str(e)}")
        # Fallback to just the new message (cleaned)
        fallback_query = new_message
        if "(with filters:" in fallback_query:
            fallback_query = fallback_query.split("(with filters:")[0].strip()
        logger.info(f"Using fallback search query: '{fallback_query}'")
        return fallback_query

def create_system_prompt(products_context: str = None) -> str:
    """Create the system prompt for the search engine chatbot"""
    base_prompt = """You are an intelligent search engine assistant. Your role is to:

1. Summarize search results in a concise, helpful way
2. Provide brief overviews of what was found
3. Help users understand their search results at a glance
4. Answer follow-up questions about the search results
5. Be conversational and helpful, but concise

IMPORTANT: When a user searches for something, I will provide you with the ACTUAL PRODUCTS that were found in our database. Always reference these specific products in your responses."""

    if products_context:
        logger.info(f"Creating system prompt with products_context: {products_context[:500]}...")
        return f"""{base_prompt}

🔍 CURRENT SEARCH RESULTS:
The user can see these specific products in their search results:
{products_context}

CRITICAL: These are REAL products that exist in our database and are currently displayed to the user. When responding:
- Always acknowledge what was actually found with a brief summary
- If filters were applied, acknowledge the filtered results (don't refer to the original unfiltered query)
- Mention the number of products found and key categories/brands represented
- Keep your response concise (2-3 sentences max for initial search)
- Don't list all product details - users can see those in the UI
- Be enthusiastic about successful searches
- If few results, suggest the user might want to try different search terms or adjust filters"""
    else:
        logger.warning("Creating system prompt WITHOUT products_context")

    return base_prompt

async def process_chat_start(query: str, user_id: str = None, products_context: str = None) -> Dict:
    """
    Process the initial chat start request
    """
    try:
        logger.info(f"Processing chat start for query: '{query}' (user: {user_id})")

        session_id = generate_session_id()
        system_prompt = create_system_prompt(products_context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"I want to search for: {query}"}
        ]

        response_data = await openai_client.create_response(messages)

        initial_message = ChatMessage(
            role="assistant",
            content=response_data["content"],
            timestamp=datetime.now(),
            response_id=response_data["response_id"]
        )

        user_message = ChatMessage(
            role="user",
            content=query,
            timestamp=datetime.now()
        )

        chat_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            messages=[user_message, initial_message],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

        logger.info(f"Chat session created successfully: {session_id}")
        logger.debug(f"Initial response length: {len(response_data['content'])}")

        return {
            "session": chat_session,
            "response_id": response_data["response_id"],
            "usage": response_data.get("usage")
        }

    except Exception as e:
        logger.error(f"Error processing chat start: {str(e)}")
        raise

async def process_chat_message(
    session: ChatSession,
    message: str,
    user_id: str = None,
    brand_filter: str = None,
    color_filter: str = None
) -> Dict:
    """
    Process a new message in an existing chat session with search on every message
    """
    try:
        logger.info(f"Processing message in session {session.session_id}: '{message}' with filters - Brand: {brand_filter}, Color: {color_filter}")

        # Step 1: Generate semantic search query from conversation history + new message
        messages_for_context = [{"role": msg.role, "content": msg.content} for msg in session.messages]
        search_query = await generate_search_query_from_history(messages_for_context, message)
        logger.info(f"Generated search query: '{search_query}'")

        # Step 2: Perform Weaviate search with generated query and filters
        from weaviate_client import weaviate_client

        search_results = weaviate_client.semantic_search(
            query=search_query,
            limit=10,
            brand_filter=brand_filter,
            color_filter=color_filter
        )

        products = [Product(**result) for result in search_results]
        logger.info(f"Found {len(products)} products for generated query: '{search_query}' with filters: brand={brand_filter}, color={color_filter}")

        # Step 3: Build products context with filter information
        products_context = ""
        if products:
            filter_info = ""
            if brand_filter or color_filter:
                filter_parts = []
                if brand_filter:
                    filter_parts.append(f"Brand: {brand_filter}")
                if color_filter:
                    filter_parts.append(f"Color: {color_filter}")
                filter_info = f" (FILTERED BY: {', '.join(filter_parts)})"

            products_context = f"SEARCH RESULTS FOR: '{search_query}'{filter_info}\n\n" + "\n".join([
                f"- {product.title} by {product.brand}"
                + (f" (Color: {product.color})" if product.color else "")
                + (f"\n  Description: {product.description[:150]}..." if product.description else "")
                + (f"\n  Key Features: {product.bullet_points[:100]}..." if product.bullet_points else "")
                for product in products[:5]  # Limit to first 5 for context
            ])
            logger.info(f"Products context created: {products_context[:200]}...")
        else:
            logger.warning(f"No products found for query: '{search_query}' with filters: brand={brand_filter}, color={color_filter}")

        # Step 4: Create user message
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.now()
        )

        # Step 5: Build OpenAI messages with system prompt including new search results
        system_prompt = create_system_prompt(products_context)
        openai_messages = [{"role": "system", "content": system_prompt}]

        # Include recent conversation history for context
        recent_messages = session.messages[-8:] if len(session.messages) > 8 else session.messages
        logger.debug(f"Using {len(recent_messages)} recent messages for conversation context")

        for msg in recent_messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        openai_messages.append({
            "role": "user",
            "content": message
        })

        # Step 6: Get previous response ID for response chaining
        previous_response_id = None
        if session.messages:
            last_assistant_message = next(
                (msg for msg in reversed(session.messages) if msg.role == "assistant"),
                None
            )
            if last_assistant_message and last_assistant_message.response_id:
                previous_response_id = last_assistant_message.response_id

        # Step 7: Generate assistant response using Responses API
        response_data = await openai_client.create_response(
            openai_messages,
            previous_response_id=previous_response_id
        )

        assistant_response = ChatMessage(
            role="assistant",
            content=response_data["content"],
            timestamp=datetime.now(),
            response_id=response_data["response_id"],
            previous_response_id=previous_response_id
        )

        # Step 8: Update session with new messages and products
        session.messages.extend([user_message, assistant_response])
        session.products = products  # Update with new search results
        session.last_updated = datetime.now()

        logger.info(f"Message processed successfully with {len(products)} products found")
        logger.debug(f"Assistant response length: {len(response_data['content'])}")

        return {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "search_query_used": search_query,
            "products_found": len(products),
            "usage": response_data.get("usage")
        }

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise

def validate_session_request(session_id: str, chat_sessions: Dict) -> ChatSession:
    """
    Validate and retrieve a chat session
    """
    if not session_id:
        logger.warning("Session ID not provided")
        raise ValueError("Session ID is required")

    if session_id not in chat_sessions:
        logger.warning(f"Session not found: {session_id}")
        raise ValueError(f"Chat session {session_id} not found")

    logger.debug(f"Session {session_id} validated successfully")
    return chat_sessions[session_id]