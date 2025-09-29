import streamlit as st
import time
import logging
from utils import start_chat_session, get_session_products, get_available_brands, get_available_colors, search_products

logger = logging.getLogger(__name__)

def render_search_interface():
    """Render the initial search interface"""
    logger.info("Rendering search interface")

    st.markdown("<h1 style='text-align: center; margin-top: 5rem;'>Semantic Search</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("search_form"):
            search_query = st.text_input("Search", placeholder="Looking to Search...", label_visibility="collapsed")
            submit_button = st.form_submit_button("Search", use_container_width=True)

            if submit_button and search_query:
                logger.info(f"Search submitted: '{search_query}'")

                # Create progress container
                progress_container = st.container()

                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.markdown("🔍 **Starting AI-powered search...**")
                    progress_bar.progress(25)

                    try:
                        # Check for filters and existing session
                        active_brand = getattr(st.session_state, 'active_brand_filter', None)
                        active_color = getattr(st.session_state, 'active_color_filter', None)

                        # Check if we have an existing session and no filters have changed
                        has_existing_session = hasattr(st.session_state, 'session_id') and st.session_state.session_id

                        # Always create a fresh session with current search context
                        # This ensures the AI always gets the most recent search results
                        if active_brand or active_color:
                            status_text.markdown("🤖 **Connecting to AI assistant with filters...**")
                            chat_response = start_chat_session(
                                search_query,
                                brand_filter=active_brand,
                                color_filter=active_color
                            )
                        else:
                            status_text.markdown("🤖 **Connecting to AI assistant...**")
                            chat_response = start_chat_session(search_query)

                        session_id = chat_response["session_id"]

                        progress_bar.progress(75)

                        if not chat_response:
                            raise Exception("Failed to start chat session")

                    except Exception as e:
                        progress_container.empty()
                        st.error(f"❌ Search failed: {str(e)}")
                        st.error("Please check if the backend server is running and try again.")
                        return

                progress_container.empty()

                if chat_response:
                    logger.info(f"Chat session started successfully: {session_id}")

                    # Create a new progress container for product retrieval
                    with st.container():
                        progress_bar = st.progress(75)
                        status_text = st.empty()

                        try:
                            status_text.markdown("📦 **Getting search results...**")

                            # Get session products (backend already performed the search with correct filters)
                            search_results = get_session_products(session_id)

                            progress_bar.progress(100)

                            if search_results and search_results.get("products"):
                                st.session_state.searched = True
                                st.session_state.session_id = session_id

                                # Build conversation history: keep previous messages + add new exchange
                                user_message = search_query
                                if active_brand or active_color:
                                    filter_desc = []
                                    if active_brand:
                                        filter_desc.append(f"Brand: {active_brand}")
                                    if active_color:
                                        filter_desc.append(f"Color: {active_color}")
                                    user_message = f"{search_query} (with filters: {', '.join(filter_desc)})"

                                # Preserve conversation history if it exists, otherwise start fresh
                                if has_existing_session and hasattr(st.session_state, 'messages') and st.session_state.messages:
                                    # Append new exchange to existing conversation
                                    st.session_state.messages.extend([
                                        {"role": "user", "content": user_message},
                                        {"role": "assistant", "content": chat_response["initial_message"]["content"]}
                                    ])
                                else:
                                    # Start fresh conversation
                                    st.session_state.messages = [
                                        {"role": "user", "content": user_message},
                                        {"role": "assistant", "content": chat_response["initial_message"]["content"]}
                                    ]

                                st.session_state.products = search_results["products"]

                                # Show filter status in success message
                                result_msg = f"Search completed: found {len(search_results['products'])} products"
                                if active_brand or active_color:
                                    filter_desc = []
                                    if active_brand:
                                        filter_desc.append(f"Brand: {active_brand}")
                                    if active_color:
                                        filter_desc.append(f"Color: {active_color}")
                                    result_msg += f" (with filters: {', '.join(filter_desc)})"

                                logger.info(result_msg)

                                status_text.markdown("✅ **Search completed successfully!**")
                                progress_bar.empty()
                                status_text.empty()

                                st.rerun()
                            else:
                                progress_bar.empty()
                                status_text.empty()
                                logger.warning("No products found in search results")
                                st.warning("🔍 No products found for your search query. Please try different keywords.")

                        except Exception as e:
                            progress_bar.empty()
                            status_text.empty()
                            logger.error(f"Error getting products: {str(e)}")
                            st.error("❌ Error retrieving search results. Please try again.")