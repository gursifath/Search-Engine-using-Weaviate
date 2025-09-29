import streamlit as st
import logging
from utils import check_backend_health, get_available_brands, get_available_colors, search_products
from components.search_interface import render_search_interface
from components.chat import render_chat_interface
from components.search_results import render_search_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Semantic Search Engine", layout="wide")

# --- NEW "CLASSIC LUXURY - DARK MODE" THEME ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@400;700&display=swap');

    /* --- General & Typography --- */
    html, body, [class*="st-"] {
        font-family: 'Lato', sans-serif;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117; /* Off-black background */
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #FAFAFA; /* Light text for dark background */
        padding-bottom: 1rem;
    }
    
    h1 { font-size: 2.5rem; }
    h2 { font-size: 2rem; }
    h3 { font-size: 1.5rem; }
    p, .stMarkdown, .stSelectbox label {
        color: #E0E0E0; /* Softer light text */
    }

    /* --- Cards --- */
    .card {
        background-color: #181E29; /* Dark card background */
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #334155; /* Muted border */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease-in-out;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        border-color: #D4AF37; /* Brighter Gold Accent for Dark Mode */
    }
    
    .card-title {
        color: #D4AF37; /* Brighter Gold Accent */
        font-size: 1.1rem;
        font-weight: 700; /* Use Lato Bold */
    }
    .card-brand {
        color: #FFFFFF; /* White text for brand */
        font-weight: bold;
    }

    /* --- Buttons --- */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 8px;
        background-color: #D4AF37; /* Brighter Gold Accent */
        color: #181E29; /* Dark text on button */
        border: 1px solid #D4AF37;
        font-weight: 700;
        font-size: 0.875rem;
        padding: 0.7rem 1.4rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #C09B2C; /* Darker gold on hover */
        border-color: #C09B2C;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stButton > button:active, .stFormSubmitButton > button:active {
        transform: translateY(0px);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.15);
    }

    /* --- Sidebar --- */
    .stSidebar {
        background: #0E1117 !important; /* Match app background */
        border-right: 1px solid #334155 !important;
    }

    .stSidebar .stMarkdown h3 {
        color: #D4AF37 !important;
        text-align: center;
        border-bottom: 2px solid #334155;
    }
    
    .stSidebar .stSelectbox > div > div {
        background-color: #181E29 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    .stSidebar .stSelectbox > div > div:hover {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.15) !important;
    }

    /* --- Chat Interface --- */
    [data-testid="stChatMessageContent"] {
        background-color: #1E293B !important; /* Dark blue-grey for messages */
        border-radius: 12px !important;
        padding: 12px !important;
        border: none !important;
    }
    [data-testid="stChatMessageContent"] p {
        color: #F1F5F9 !important; /* Light text for readability */
    }
    
    .stChatInput textarea {
        min-height: 52px !important;
        border-radius: 12px !important;
        border: 2px solid #475569 !important;
        background-color: #181E29 !important;
        color: #F1F5F9 !important;
        padding: 14px 18px !important;
        transition: all 0.2s ease !important;
    }

    .stChatInput textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.2) !important;
        outline: none !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #94A3B8 !important;
    }

    /* --- Scrollbar Styling --- */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #181E29;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #475569;
        border-radius: 4px;
        border: 2px solid #181E29;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: #64748B;
    }
    
    /* --- General Cleanup & Hiding Elements --- */
    /* Hide all sidebar toggle elements and related controls */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarNav"] button[kind="headerNoPadding"],
    button[data-testid="baseButton-header"],
    button[kind="header"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] button:first-child,
    .stSidebar button[kind="headerNoPadding"],
    .stSidebar [data-testid="baseButton-header"],
    div[data-testid="stToolbar"],
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }

    .main .block-container {
        padding-left: 1rem !important;
        max-width: none !important;
    }

    /* Hide scrollbars for search results container */
    [data-testid="stVerticalBlock"] > div[style*="height: 800px"] {
        scrollbar-width: none !important; /* Firefox */
        -ms-overflow-style: none !important; /* IE and Edge */
        overflow-x: hidden !important;
    }

    [data-testid="stVerticalBlock"] > div[style*="height: 800px"]::-webkit-scrollbar {
        display: none !important; /* Chrome, Safari, Opera */
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

if "searched" not in st.session_state:
    st.session_state.searched = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "products" not in st.session_state:
    st.session_state.products = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = check_backend_health()
if "brands_cache" not in st.session_state:
    st.session_state.brands_cache = None
if "colors_cache" not in st.session_state:
    st.session_state.colors_cache = None
if "cache_loaded" not in st.session_state:
    st.session_state.cache_loaded = False
if "active_brand_filter" not in st.session_state:
    st.session_state.active_brand_filter = None
if "active_color_filter" not in st.session_state:
    st.session_state.active_color_filter = None

logger.info(f"App started - Backend connected: {st.session_state.backend_connected}")

if not st.session_state.backend_connected:
    st.warning("⚠️ Backend API is not running. Please start the backend server first.")
    st.code("cd backend && python run_server.py")
    st.info("💡 Make sure to set your OPENAI_API_KEY in the backend/.env file")

if not st.session_state.searched:
    render_search_interface()
else:
    logger.info(f"Rendering search results view (session: {st.session_state.session_id})")

    # Add search filters in sidebar
    with st.sidebar:
        st.markdown("### 🔍 Search Filters")

        if st.button("🔄 New Search", use_container_width=True):
            logger.info("New search button clicked")
            st.session_state.searched = False
            st.session_state.messages = []
            st.session_state.products = []
            st.session_state.session_id = None
            # Reset filters when starting new search
            st.session_state.active_brand_filter = None
            st.session_state.active_color_filter = None
            st.rerun()

        st.markdown("---")
        st.markdown("#### Filter Products")

        # Get original search query from session state
        original_query = ""
        if st.session_state.messages:
            original_query = st.session_state.messages[0]["content"]

        # Show active filters
        active_filters = []
        if st.session_state.active_brand_filter:
            active_filters.append(f"🏷️ Brand: {st.session_state.active_brand_filter}")
        if st.session_state.active_color_filter:
            active_filters.append(f"🎨 Color: {st.session_state.active_color_filter}")

        if active_filters:
            st.markdown("**Active Filters:**")
            for filter_text in active_filters:
                st.markdown(f"- {filter_text}")

            if st.button("🗑️ Clear Filters", use_container_width=True):
                st.session_state.active_brand_filter = None
                st.session_state.active_color_filter = None
                # Perform search with original query and no filters
                if original_query:
                    try:
                        with st.spinner("🔍 Searching without filters..."):
                            unfiltered_results = search_products(original_query)

                        if unfiltered_results and unfiltered_results.get("products"):
                            st.session_state.products = unfiltered_results["products"]
                            st.success(f"Filters cleared - showing all {len(unfiltered_results['products'])} results")
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error clearing filters: {str(e)}")
                        st.error("Error clearing filters")

        # Continue with existing code

        # Load brands/colors cache if not already loaded
        if not st.session_state.cache_loaded and st.session_state.backend_connected:
            with st.spinner("Loading filters..."):
                try:
                    st.session_state.brands_cache = get_available_brands() or []
                    st.session_state.colors_cache = get_available_colors() or []
                    st.session_state.cache_loaded = True
                except Exception as e:
                    logger.error(f"Failed to load cache: {str(e)}")
                    st.session_state.brands_cache = []
                    st.session_state.colors_cache = []
                    st.session_state.cache_loaded = True  # Prevent retry loops

        # Brand filter
        brands = st.session_state.brands_cache or []
        brand_options = ["All Brands"] + brands
        selected_brand = st.selectbox("Brand:", brand_options, key="brand_filter")

        # Color filter
        colors = st.session_state.colors_cache or []
        color_options = ["All Colors"] + colors
        selected_color = st.selectbox("Color:", color_options, key="color_filter")

        # Save filters button
        if st.button("💾 Save Filter Settings", use_container_width=True):
            brand_filter = None if selected_brand == "All Brands" else selected_brand
            color_filter = None if selected_color == "All Colors" else selected_color

            # Store filters in session state for future searches
            st.session_state.active_brand_filter = brand_filter
            st.session_state.active_color_filter = color_filter

            filter_description = []
            if brand_filter:
                filter_description.append(f"Brand: {brand_filter}")
            if color_filter:
                filter_description.append(f"Color: {color_filter}")

            if filter_description:
                st.success(f"✅ Filters saved: {', '.join(filter_description)}")
                st.info("💡 These filters will be applied to your next search query!")
            else:
                st.success("✅ All filters cleared!")

            logger.info(f"Filter settings saved - Brand: {brand_filter}, Color: {color_filter}")
            st.rerun()

    chat_col, results_col = st.columns([1, 3])

    with chat_col:
        render_chat_interface(st.session_state.session_id)

    with results_col:
        render_search_results(st.session_state.products)