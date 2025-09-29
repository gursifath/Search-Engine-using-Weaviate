import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from models import (
    StartChatRequest, StartChatResponse, SendMessageRequest,
    SendMessageResponse, SearchRequest, SearchResponse, Product
)
from helpers import process_chat_start, process_chat_message, validate_session_request

logger = logging.getLogger(__name__)

router = APIRouter()
chat_sessions: Dict = {}

@router.get("/")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"message": "Search Engine Chat API is running", "status": "healthy"}

@router.post("/chat/start", response_model=StartChatResponse)
async def start_chat(request: StartChatRequest):
    """
    Start a new chat session with an initial search query and perform product search
    """
    try:
        logger.info(f"Starting new chat session for query: '{request.query}' with filters - Brand: {request.brand_filter}, Color: {request.color_filter}")

        # Perform product search first
        from weaviate_client import weaviate_client

        search_results = weaviate_client.semantic_search(
            query=request.query,
            limit=10,
            brand_filter=request.brand_filter,
            color_filter=request.color_filter
        )

        products = [Product(**result) for result in search_results]
        logger.info(f"Found {len(products)} products for chat context")

        if products:
            logger.info(f"Sample products found: {[p.title for p in products[:3]]}")
        else:
            logger.warning("NO PRODUCTS FOUND in search results - this will cause 'no products' response!")

        # Create products context string for system prompt
        products_context = ""
        if products:
            # Add filter information to the context if filters were applied
            filter_info = ""
            if request.brand_filter or request.color_filter:
                filter_parts = []
                if request.brand_filter:
                    filter_parts.append(f"Brand: {request.brand_filter}")
                if request.color_filter:
                    filter_parts.append(f"Color: {request.color_filter}")
                filter_info = f" (FILTERED BY: {', '.join(filter_parts)})"

            products_context = f"SEARCH RESULTS FOR: '{request.query}'{filter_info}\n\n" + "\n".join([
                f"- {product.title} by {product.brand}"
                + (f" (Color: {product.color})" if product.color else "")
                + (f"\n  Description: {product.description[:150]}..." if product.description else "")
                + (f"\n  Key Features: {product.bullet_points[:100]}..." if product.bullet_points else "")
                for product in products[:5]  # Limit to first 5 for context
            ])
            logger.info(f"Products context created with filters: {products_context[:200]}...")
        else:
            logger.error("Products context is EMPTY - this will cause AI to say 'no products found'")

        result = await process_chat_start(request.query, request.user_id, products_context)
        session = result["session"]

        # Add search query and products to session
        session.search_query = request.query
        session.products = products

        chat_sessions[session.session_id] = session

        logger.info(f"Chat session {session.session_id} stored successfully with {len(products)} products")

        return StartChatResponse(
            session_id=session.session_id,
            initial_message=session.messages[-1],
            response_id=result["response_id"],
            status="success"
        )

    except ValueError as e:
        logger.error(f"Validation error starting chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")

@router.post("/chat/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send a message in an existing chat session with fresh search on every message
    """
    try:
        logger.info(f"Sending message to session {request.session_id}: '{request.message}' with filters - Brand: {request.brand_filter}, Color: {request.color_filter}")

        session = validate_session_request(request.session_id, chat_sessions)

        # Process chat message with filters - this will perform a fresh search
        result = await process_chat_message(
            session,
            request.message,
            request.user_id,
            request.brand_filter,
            request.color_filter
        )

        chat_sessions[request.session_id] = session

        logger.info(f"Message processed successfully with search query: '{result.get('search_query_used')}', found {result.get('products_found')} products")

        return SendMessageResponse(
            session_id=request.session_id,
            user_message=result["user_message"],
            assistant_response=result["assistant_response"],
            status="success"
        )

    except ValueError as e:
        logger.error(f"Validation error sending message: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/chat/{session_id}")
async def get_chat_session(session_id: str):
    """
    Get chat session details and message history
    """
    try:
        logger.info(f"Retrieving chat session: {session_id}")

        session = validate_session_request(session_id, chat_sessions)

        logger.info(f"Chat session {session_id} retrieved successfully")
        return session

    except ValueError as e:
        logger.error(f"Error retrieving chat session: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session
    """
    try:
        logger.info(f"Deleting chat session: {session_id}")

        validate_session_request(session_id, chat_sessions)
        del chat_sessions[session_id]

        logger.info(f"Chat session {session_id} deleted successfully")
        return {"message": "Chat session deleted successfully", "status": "success"}

    except ValueError as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/chat/sessions/list")
async def list_chat_sessions(user_id: Optional[str] = None):
    """
    List all chat sessions, optionally filtered by user_id
    """
    try:
        logger.info(f"Listing chat sessions (user_id: {user_id})")

        if user_id:
            filtered_sessions = {
                sid: session for sid, session in chat_sessions.items()
                if session.user_id == user_id
            }
            logger.info(f"Found {len(filtered_sessions)} sessions for user {user_id}")
            return {"sessions": filtered_sessions, "count": len(filtered_sessions)}

        logger.info(f"Returning all {len(chat_sessions)} sessions")
        return {"sessions": chat_sessions, "count": len(chat_sessions)}

    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.get("/chat/{session_id}/responses")
async def get_conversation_responses(session_id: str):
    """
    Get all responses for a conversation using OpenAI Responses API
    """
    try:
        logger.info(f"Getting conversation responses for session: {session_id}")

        session = validate_session_request(session_id, chat_sessions)

        if hasattr(session, 'conversation_id') and session.conversation_id:
            from client import openai_client
            responses = await openai_client.list_conversation_responses(
                conversation_id=session.conversation_id
            )
            logger.info(f"Retrieved {len(responses)} responses from OpenAI")
            return {"responses": responses, "count": len(responses)}
        else:
            logger.warning(f"No conversation_id found for session {session_id}")
            return {"responses": [], "count": 0, "message": "No conversation ID available"}

    except ValueError as e:
        logger.error(f"Error getting conversation responses: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting conversation responses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get responses: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """
    Search for products using Weaviate semantic search
    """
    try:
        logger.info(f"Searching for products: '{request.query}'")

        from weaviate_client import weaviate_client

        results = weaviate_client.semantic_search(
            query=request.query,
            limit=request.limit,
            brand_filter=request.brand_filter,
            color_filter=request.color_filter
        )

        products = [Product(**result) for result in results]

        logger.info(f"Search completed: found {len(products)} products")

        return SearchResponse(
            products=products,
            total_results=len(products),
            status="success"
        )

    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/brands")
async def get_available_brands():
    """
    Get list of available product brands
    """
    try:
        logger.info("Fetching available brands")

        from weaviate_client import weaviate_client
        brands = weaviate_client.get_available_brands()

        logger.info(f"Found {len(brands)} brands")
        return {"brands": brands, "count": len(brands), "status": "success"}

    except Exception as e:
        logger.error(f"Error fetching brands: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch brands: {str(e)}")

@router.get("/search/colors")
async def get_available_colors():
    """
    Get list of available product colors
    """
    try:
        logger.info("Fetching available colors")

        from weaviate_client import weaviate_client
        colors = weaviate_client.get_available_colors()

        logger.info(f"Found {len(colors)} colors")
        return {"colors": colors, "count": len(colors), "status": "success"}

    except Exception as e:
        logger.error(f"Error fetching colors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch colors: {str(e)}")

@router.get("/chat/{session_id}/products", response_model=SearchResponse)
async def get_session_products(session_id: str):
    """
    Get products associated with a chat session
    """
    try:
        logger.info(f"Getting products for session: {session_id}")

        session = validate_session_request(session_id, chat_sessions)

        products = session.products if hasattr(session, 'products') and session.products else []

        logger.info(f"Found {len(products)} products for session {session_id}")
        return SearchResponse(
            products=products,
            total_results=len(products),
            status="success"
        )

    except ValueError as e:
        logger.error(f"Error getting session products: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session products: {str(e)}")