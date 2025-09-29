import requests
import streamlit as st
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"

def start_chat_session(query: str, user_id: str = None, brand_filter: str = None, color_filter: str = None) -> Optional[Dict]:
    """Start a new chat session with the backend"""
    try:
        logger.info(f"FRONTEND: Starting chat session for query: '{query}' with brand_filter: {brand_filter}, color_filter: {color_filter}")

        payload = {"query": query, "user_id": user_id}
        if brand_filter:
            payload["brand_filter"] = brand_filter
            logger.info(f"FRONTEND: Added brand_filter to payload: {brand_filter}")
        if color_filter:
            payload["color_filter"] = color_filter
            logger.info(f"FRONTEND: Added color_filter to payload: {color_filter}")

        logger.info(f"FRONTEND: Full payload being sent: {payload}")

        response = requests.post(
            f"{BACKEND_URL}/chat/start",
            json=payload,
            timeout=120  # Increased to match backend Weaviate timeouts
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Chat session started successfully: {result.get('session_id')}")
            return result
        else:
            error_msg = f"Backend returned status {response.status_code}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return None

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to backend server. Please ensure the backend is running."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.Timeout:
        error_msg = "Request timed out. The backend server might be overloaded."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None

def send_chat_message(session_id: str, message: str, user_id: str = None, brand_filter: str = None, color_filter: str = None) -> Optional[Dict]:
    """Send a message to an existing chat session"""
    try:
        logger.info(f"Sending message to session {session_id}: '{message}'")

        # Build payload with filters
        payload = {"session_id": session_id, "message": message, "user_id": user_id}
        if brand_filter:
            payload["brand_filter"] = brand_filter
        if color_filter:
            payload["color_filter"] = color_filter

        logger.info(f"Sending chat message with filters - Brand: {brand_filter}, Color: {color_filter}")

        response = requests.post(
            f"{BACKEND_URL}/chat/message",
            json=payload,
            timeout=120  # Increased to match backend processing time
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Message sent successfully to session {session_id}")
            return result
        elif response.status_code == 404:
            error_msg = "Chat session not found. Please start a new conversation."
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return None
        else:
            error_msg = f"Backend returned status {response.status_code}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return None

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to backend server. Please ensure the backend is running."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.Timeout:
        error_msg = "Request timed out. The backend server might be overloaded."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None

def search_products(query: str, limit: int = 10, brand_filter: str = None, color_filter: str = None) -> Optional[Dict]:
    """Search for products using the backend Weaviate semantic search"""
    try:
        logger.info(f"Searching products for query: '{query}'")

        payload = {
            "query": query,
            "limit": limit
        }

        if brand_filter:
            payload["brand_filter"] = brand_filter
        if color_filter:
            payload["color_filter"] = color_filter

        response = requests.post(
            f"{BACKEND_URL}/search",
            json=payload,
            timeout=120  # Increased to match Weaviate query timeouts
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Search completed: found {len(result.get('products', []))} products")
            return result
        else:
            error_msg = f"Search failed with status {response.status_code}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return None

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to backend server. Please ensure the backend is running."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.Timeout:
        error_msg = "Search request timed out. Please try again."
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during search: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None
    except Exception as e:
        error_msg = f"Unexpected error during search: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None

def get_available_brands() -> Optional[list]:
    """Get available product brands from the backend"""
    try:
        logger.info("Fetching available brands")

        response = requests.get(f"{BACKEND_URL}/search/brands", timeout=120)  # Increased for Weaviate aggregate queries

        if response.status_code == 200:
            result = response.json()
            brands = result.get("brands", [])
            logger.info(f"Fetched {len(brands)} available brands")
            return brands
        else:
            logger.error(f"Failed to fetch brands with status {response.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching brands: {str(e)}")
        return []

def get_available_colors() -> Optional[list]:
    """Get available product colors from the backend"""
    try:
        logger.info("Fetching available colors")

        response = requests.get(f"{BACKEND_URL}/search/colors", timeout=120)  # Increased for Weaviate aggregate queries

        if response.status_code == 200:
            result = response.json()
            colors = result.get("colors", [])
            logger.info(f"Fetched {len(colors)} available colors")
            return colors
        else:
            logger.error(f"Failed to fetch colors with status {response.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching colors: {str(e)}")
        return []

def get_session_products(session_id: str) -> Optional[Dict]:
    """Get products associated with a chat session"""
    try:
        logger.info(f"Getting products for session: {session_id}")

        response = requests.get(f"{BACKEND_URL}/chat/{session_id}/products", timeout=60)  # Increased for session lookup

        if response.status_code == 200:
            result = response.json()
            products = result.get("products", [])
            logger.info(f"Got {len(products)} products for session {session_id}")
            return result
        else:
            logger.error(f"Failed to get session products with status {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting session products: {str(e)}")
        return None

def check_backend_health() -> bool:
    """Check if the backend server is running and healthy"""
    try:
        logger.info("Checking backend health")

        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        is_healthy = response.status_code == 200

        if is_healthy:
            logger.info("Backend is healthy")
        else:
            logger.warning(f"Backend health check failed with status {response.status_code}")

        return is_healthy

    except requests.exceptions.RequestException:
        logger.warning("Backend health check failed - server not reachable")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking backend health: {str(e)}")
        return False