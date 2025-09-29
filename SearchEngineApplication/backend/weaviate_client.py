import logging
import weaviate
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery
import weaviate.classes.query as wvcq
from typing import List, Dict, Optional
import time
from config import config

logger = logging.getLogger(__name__)

class WeaviateClientSingleton:
    _instance: Optional['WeaviateClientSingleton'] = None
    _client: Optional[weaviate.WeaviateClient] = None
    _initialized: bool = False
    _last_health_check: float = 0
    _health_check_interval: float = 300  # 5 minutes
    _connection_timeout: int = 60  # 60 seconds timeout
    _max_retries: int = 3

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Creating new Weaviate client singleton instance")
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._create_connection()

    def _create_connection(self) -> None:
        """Create a new Weaviate connection with proper timeout configuration"""
        if not config.WEAVIATE_URL:
            logger.error("Weaviate URL not found in environment variables")
            raise ValueError("Weaviate URL not configured")

        try:
            # Configure timeouts and connection settings
            timeout_config = Timeout(
                init=30,      # 30 seconds for initialization
                query=60,     # 60 seconds for queries (important for semantic search)
                insert=120    # 2 minutes for insert operations
            )

            additional_config = AdditionalConfig(
                timeout=timeout_config
            )

            # Check if we have API key for Weaviate Cloud or local instance
            if hasattr(config, 'WEAVIATE_API_KEY') and config.WEAVIATE_API_KEY:
                # Connect to Weaviate Cloud (matching your notebook implementation)
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=config.WEAVIATE_URL,
                    auth_credentials=Auth.api_key(config.WEAVIATE_API_KEY),
                    headers={"X-OpenAI-Api-Key": config.OPENAI_API_KEY} if config.OPENAI_API_KEY else {},
                    additional_config=additional_config
                )
                logger.info("Connected to Weaviate Cloud with timeout configuration")
            else:
                # Connect to local Weaviate instance
                headers = {}
                if config.OPENAI_API_KEY:
                    headers["X-OpenAI-Api-Key"] = config.OPENAI_API_KEY

                self._client = weaviate.connect_to_local(
                    host=config.WEAVIATE_URL.replace('http://', '').replace('https://', '').replace(':8080', ''),
                    headers=headers,
                    additional_config=additional_config
                )
                logger.info("Connected to local Weaviate instance with timeout configuration")

            if self._client.is_ready():
                self._initialized = True
                self._last_health_check = time.time()
                logger.info("Weaviate client v4 initialized successfully with robust connection settings")
            else:
                raise ConnectionError("Weaviate client not ready")

        except Exception as e:
            logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            self._client = None
            self._initialized = False
            raise

    def _check_connection_health(self) -> bool:
        """Check if the connection is still healthy"""
        if not self._client or not self._initialized:
            return False

        current_time = time.time()

        # Only check health if enough time has passed
        if current_time - self._last_health_check < self._health_check_interval:
            return True

        try:
            # Quick health check
            is_ready = self._client.is_ready()
            self._last_health_check = current_time

            if not is_ready:
                logger.warning("Weaviate connection health check failed")
                return False

            logger.debug("Weaviate connection health check passed")
            return True

        except Exception as e:
            logger.error(f"Weaviate health check error: {str(e)}")
            return False

    def _reconnect_if_needed(self) -> None:
        """Reconnect if the connection is unhealthy"""
        if not self._check_connection_health():
            logger.info("Attempting to reconnect to Weaviate...")

            # Close existing connection if it exists
            if self._client:
                try:
                    self._client.close()
                except Exception as e:
                    logger.warning(f"Error closing old connection: {str(e)}")

            # Reset state
            self._client = None
            self._initialized = False

            # Retry connection
            for attempt in range(self._max_retries):
                try:
                    logger.info(f"Reconnection attempt {attempt + 1}/{self._max_retries}")
                    self._create_connection()

                    if self._initialized:
                        logger.info("Successfully reconnected to Weaviate")
                        return

                except Exception as e:
                    logger.error(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self._max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff

            raise ConnectionError(f"Failed to reconnect to Weaviate after {self._max_retries} attempts")

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Get the Weaviate client with automatic reconnection"""
        self._reconnect_if_needed()

        if self._client is None or not self._initialized:
            logger.error("Weaviate client not initialized")
            raise RuntimeError("Weaviate client not initialized")

        return self._client

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        brand_filter: Optional[str] = None,
        color_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform semantic search on EcommerceProducts collection using Weaviate v4 API
        """
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Performing semantic search for: '{query}' (limit: {limit}) - Attempt {attempt + 1}")

                # Get the collection - this will auto-reconnect if needed
                ecommerce_products = self.client.collections.get("EcommerceProducts")

                # Build filters using the exact syntax from your notebook
                filters = []
                if brand_filter:
                    filters.append(("product_brand", brand_filter))
                    logger.debug(f"Added brand filter: {brand_filter}")
                if color_filter and color_filter.strip():
                    filters.append(("product_color", color_filter))
                    logger.debug(f"Added color filter: {color_filter}")

                # Perform the query using v4 API matching your notebook
                if filters:
                    # Use the exact syntax from your notebook
                    result = ecommerce_products.query.near_text(
                        query=query,
                        limit=limit,
                        filters=wvcq.Filter.all_of([wvcq.Filter.by_property(filter[0]).equal(filter[1]) for filter in filters]),
                        return_metadata=MetadataQuery(score=True)
                    )
                    logger.debug(f"Query with filters: {filters}")
                else:
                    # Query without filters
                    result = ecommerce_products.query.near_text(
                        query=query,
                        limit=limit,
                        return_metadata=MetadataQuery(score=True)
                    )

                if not result.objects:
                    logger.warning(f"No results found in Weaviate for query: '{query}' with filters: brand={brand_filter}, color={color_filter}")
                    return []

                products = result.objects
                logger.info(f"Found {len(products)} products for query: '{query}' with filters: brand={brand_filter}, color={color_filter}")

                # Transform the results to match expected format
                transformed_products = []
                for obj in products:
                    product_props = obj.properties
                    transformed_product = {
                        "id": product_props.get("product_id", ""),
                        "title": product_props.get("product_title", ""),
                        "brand": product_props.get("product_brand", ""),
                        "color": product_props.get("product_color", ""),
                        "description": product_props.get("product_description", ""),
                        "bullet_points": product_props.get("product_bullet_point", ""),
                        "price": "Price not available",  # Not available in current schema
                        "image_url": "",  # Not available in current schema
                        "rating": 0,  # Not available in current schema
                        "reviews": 0  # Not available in current schema
                    }
                    transformed_products.append(transformed_product)

                return transformed_products

            except (ConnectionError, TimeoutError, Exception) as e:
                logger.error(f"Error performing semantic search (attempt {attempt + 1}): {str(e)}")

                if attempt < self._max_retries - 1:
                    # Force reconnection on next attempt
                    self._last_health_check = 0
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error("All semantic search attempts failed")
                    raise

    def get_available_brands(self, limit: int = 50) -> List[str]:
        """
        Get list of available product brands using HTTP REST only (avoiding gRPC issues)
        """
        # Skip aggregate entirely - go straight to HTTP REST fetch
        try:
            logger.info("Fetching available brands using HTTP REST fetch method")
            ecommerce_products = self.client.collections.get("EcommerceProducts")

            # Fetch large sample to get comprehensive brand list
            result = ecommerce_products.query.fetch_objects(
                limit=2000,  # Larger sample for better frequency analysis
                return_properties=["product_brand"]  # Only fetch brand field for efficiency
            )

            # Count brand frequencies
            brand_counts = {}
            for obj in result.objects:
                brand = obj.properties.get("product_brand")
                if brand and brand.strip():
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1

            # Sort by frequency (most frequent first)
            brand_list = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
            brand_list = [brand for brand, count in brand_list[:limit]]
            logger.info(f"HTTP REST method successful: Found {len(brand_list)} unique brands")
            return brand_list

        except Exception as e:
            logger.error(f"HTTP REST fetch failed: {str(e)}")
            # Return hardcoded brands as fallback
            fallback_brands = ["Apple", "Dell", "HP", "Lenovo", "ASUS", "Acer", "Samsung", "Microsoft", "Sony", "LG",
                             "Canon", "Nikon", "Nike", "Adidas", "Amazon", "Google", "Intel", "AMD", "NVIDIA", "Tesla"]
            logger.info(f"Using hardcoded fallback brands: {len(fallback_brands)} brands")
            return fallback_brands[:limit]

    def get_available_colors(self, limit: int = 50) -> List[str]:
        """
        Get list of available product colors using HTTP REST only (avoiding gRPC issues)
        """
        # Skip aggregate entirely - go straight to HTTP REST fetch
        try:
            logger.info("Fetching available colors using HTTP REST fetch method")
            ecommerce_products = self.client.collections.get("EcommerceProducts")

            # Fetch large sample to get comprehensive color list
            result = ecommerce_products.query.fetch_objects(
                limit=2000,  # Larger sample for better frequency analysis
                return_properties=["product_color"]  # Only fetch color field for efficiency
            )

            # Count color frequencies
            color_counts = {}
            for obj in result.objects:
                color = obj.properties.get("product_color")
                if color and color.strip():
                    color_counts[color] = color_counts.get(color, 0) + 1

            # Sort by frequency (most frequent first)
            color_list = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            color_list = [color for color, count in color_list[:limit]]
            logger.info(f"HTTP REST method successful: Found {len(color_list)} unique colors")
            return color_list

        except Exception as e:
            logger.error(f"HTTP REST fetch failed: {str(e)}")
            # Return hardcoded colors as fallback
            fallback_colors = ["Black", "White", "Gray", "Silver", "Blue", "Red", "Green", "Gold", "Pink", "Purple",
                             "Yellow", "Orange", "Brown", "Navy", "Beige", "Tan", "Maroon", "Teal", "Olive", "Coral"]
            logger.info(f"Using hardcoded fallback colors: {len(fallback_colors)} colors")
            return fallback_colors[:limit]

weaviate_client = WeaviateClientSingleton()