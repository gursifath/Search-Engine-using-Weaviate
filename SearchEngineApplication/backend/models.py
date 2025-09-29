from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    response_id: Optional[str] = None
    previous_response_id: Optional[str] = None

class StartChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    brand_filter: Optional[str] = None
    color_filter: Optional[str] = None

class StartChatResponse(BaseModel):
    session_id: str
    initial_message: ChatMessage
    response_id: str
    status: str

class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None
    brand_filter: Optional[str] = None
    color_filter: Optional[str] = None

class SendMessageResponse(BaseModel):
    session_id: str
    user_message: ChatMessage
    assistant_response: ChatMessage
    status: str

class Product(BaseModel):
    id: str
    title: str
    brand: str
    color: Optional[str] = ""
    description: Optional[str] = ""
    bullet_points: Optional[str] = ""
    price: str = "Price not available"
    image_url: str = ""
    rating: float = 0.0
    reviews: int = 0

class ChatSession(BaseModel):
    session_id: str
    user_id: Optional[str]
    messages: List[ChatMessage]
    created_at: datetime
    last_updated: datetime
    conversation_id: Optional[str] = None
    search_query: Optional[str] = None
    products: List[Product] = []

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    brand_filter: Optional[str] = None
    color_filter: Optional[str] = None

class SearchResponse(BaseModel):
    products: List[Product]
    total_results: int
    status: str = "success"

class ErrorResponse(BaseModel):
    error: str
    message: str
    status: str = "error"