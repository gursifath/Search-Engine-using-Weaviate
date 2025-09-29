import streamlit as st
from streamlit_modal import Modal
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def render_product_card(product: Dict) -> None:
    """Render an individual product card with modal details"""
    rating = product.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating)) if rating > 0 else "No rating"

    color_display = product.get('color', 'N/A') if product.get('color') else 'N/A'
    price_display = product.get('price', 'Price not available')

    # Truncate title for header display
    display_title = product['title'][:20] + '...' if len(product['title']) > 20 else product['title']

    # Create modal first
    modal_title = product['title'][:20] + '...' if len(product['title']) > 20 else product['title']
    modal = Modal(modal_title, key=f"modal_{product['id']}", padding=20, max_width=700)

    # Create card structure with content and button in proper layout
    st.markdown(
        f"""
        <div class="card product-card">
            <div class="card-content">
                <div class="card-title">{display_title}</div>
                <div class="card-brand">{product['brand']}</div>
                <div style="color: #94A3B8; margin-top: 0.5rem;">
                    Color: {color_display} | {price_display}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Add button below the card content, right-aligned
    _, button_col = st.columns([2, 1])
    with button_col:
        if st.button("View Details", key=f"details_{product['id']}", type="primary", use_container_width=True):
            logger.info(f"Opening modal for product: {product['title']}")
            modal.open()

    if modal.is_open():
        with modal.container():
            # Add custom CSS for the modal
            st.markdown(
                """
                <style>
                .modal-content-container {
                    max-height: 500px;
                    overflow-y: auto;
                    padding-right: 10px;
                }
                .modal-content-container::-webkit-scrollbar {
                    width: 8px;
                }
                .modal-content-container::-webkit-scrollbar-track {
                    background: #1E293B;
                    border-radius: 4px;
                }
                .modal-content-container::-webkit-scrollbar-thumb {
                    background: #14B8A6;
                    border-radius: 4px;
                }
                .modal-content-container::-webkit-scrollbar-thumb:hover {
                    background: #0F766E;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Create scrollable container
            st.markdown('<div class="modal-content-container">', unsafe_allow_html=True)

            # Main details in a clean layout
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Brand:** {product['brand']}")
                st.markdown(f"**Color:** {color_display}")

            with col2:
                st.markdown(f"**Product Code:** {product['id']}")
                st.markdown(f"**Price:** {price_display}")

            # Description with character limit
            if product.get('description'):
                st.markdown("---")
                st.markdown("**Description:**")
                # Remove HTML tags and limit characters
                clean_description = product['description'].replace('<br>', '\n').replace('<BR>', '\n')
                if len(clean_description) > 400:
                    clean_description = clean_description[:400] + "..."
                st.markdown(clean_description)

            st.markdown('</div>', unsafe_allow_html=True)

def render_search_results(products: List[Dict]) -> None:
    """Render the complete search results section"""
    logger.info(f"Rendering search results with {len(products)} products")

    st.header("Search Results")

    results_container = st.container(height=800, border=False)
    with results_container:
        # Add padding wrapper to prevent card hover overflow
        st.markdown('<div style="padding: 1.5rem; margin: 0.5rem;">', unsafe_allow_html=True)
        if products:
            grid_cols = st.columns(2)
            for i, product in enumerate(products):
                with grid_cols[i % 2]:
                    render_product_card(product)
        else:
            logger.warning("No products to display")
            st.info("No products found.")

        st.markdown('</div>', unsafe_allow_html=True)