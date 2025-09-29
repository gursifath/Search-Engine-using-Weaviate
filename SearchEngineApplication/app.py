import streamlit as st
import logging
from utils import check_backend_health, get_available_brands, get_available_colors, search_products
from components.search_interface import render_search_interface
from components.chat import render_chat_interface
from components.search_results import render_search_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Semantic Search Engine", layout="wide")

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
    }

    h1 { color: #FAFAFA; }
    h2, h3 { color: #E0E0E0; padding-bottom: 1rem;}

    [data-testid="stChatMessageContent"] {
        background-color: #1E293B;
        border-radius: 15px;
        padding: 12px;
    }
    [data-testid="stChatMessageContent"] p {
        color: #FAFAFA;
    }

    .card {
        background-color: #181E29;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #334155;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }

    .product-card {
        position: relative;
        background: linear-gradient(145deg, #181E29 0%, #1E293B 100%);
    }

    .product-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(20, 184, 166, 0.1), transparent);
        transition: left 0.6s ease;
    }

    .product-card:hover::before {
        left: 100%;
    }

    .product-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow:
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 8px 16px rgba(20, 184, 166, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: #14B8A6;
        background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%);
    }

    .card-content {
        flex-grow: 1;
        z-index: 1;
        position: relative;
    }

    .card-button-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 1rem;
        z-index: 2;
        position: relative;
    }

    .product-card .card-title {
        transition: color 0.3s ease;
    }

    .product-card:hover .card-title {
        color: #2DD4BF;
        text-shadow: 0 0 8px rgba(45, 212, 191, 0.3);
    }

    .button-spacer {
        height: 0.8rem;
    }

    /* Card styling improvements */
    .card {
        position: relative;
    }

    /* Professional Button Styling */
    .stButton > button, .stFormSubmitButton > button {
        position: relative;
        border-radius: 12px;
        background: linear-gradient(135deg, #14B8A6 0%, #0F766E 100%);
        color: #FFFFFF;
        border: none;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow:
            0 4px 14px rgba(20, 184, 166, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        overflow: hidden;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button::before, .stFormSubmitButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }

    .stButton > button:hover::before, .stFormSubmitButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
        transform: translateY(-2px) scale(1.05);
        box-shadow:
            0 8px 25px rgba(20, 184, 166, 0.4),
            0 4px 10px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }

    .stButton > button:active, .stFormSubmitButton > button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow:
            0 2px 8px rgba(20, 184, 166, 0.3),
            inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar Professional Styling */
    .stSidebar {
        background: linear-gradient(180deg, #0E1117 0%, #1E293B 100%) !important;
        border-right: 1px solid #334155 !important;
        position: relative !important;
    }

    .stSidebar::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 2px;
        height: 100%;
        background: linear-gradient(180deg, transparent, #14B8A6, transparent);
        opacity: 0.6;
    }

    /* Sidebar Content Styling */
    .stSidebar .stMarkdown h3 {
        color: #2DD4BF !important;
        text-shadow: 0 0 10px rgba(45, 212, 191, 0.3);
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #14B8A6;
    }

    .stSidebar .stSelectbox label {
        color: #E2E8F0 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.875rem;
    }

    .stSidebar .stSelectbox > div > div {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }

    .stSidebar .stSelectbox > div > div:hover {
        border-color: #14B8A6 !important;
        box-shadow: 0 0 15px rgba(20, 184, 166, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Chat Interface Professional Styling */
    [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        border-radius: 18px !important;
        padding: 14px 16px 14px 16px !important;
        border: 1px solid #475569 !important;
        position: relative !important;
        overflow: hidden !important;
        margin: 6px 0 !important;
        min-height: auto !important;
    }

    [data-testid="stChatMessageContent"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #14B8A6, transparent);
        opacity: 0.7;
    }

    [data-testid="stChatMessageContent"] p {
        color: #F1F5F9 !important;
        line-height: 1.5 !important;
        margin: 0 !important;
        padding: 0 !important;
        vertical-align: top !important;
        display: block !important;
    }

    [data-testid="stChatMessageContent"] div {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Fix chat message container spacing */
    [data-testid="stChatMessage"] {
        margin: 6px 0 !important;
        padding: 0 !important;
    }

    /* Fix vertical alignment of text in chat messages */
    [data-testid="stChatMessageContent"] > div {
        display: flex !important;
        align-items: flex-start !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Chat Input Proper Styling - Fixed Positioning */
    .stChatInput {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
    }

    .stChatInput > div {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
    }

    .stChatInput textarea {
        min-height: 52px !important;
        border-radius: 16px !important;
        border: 2px solid #14B8A6 !important;
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        color: #F1F5F9 !important;
        padding: 14px 18px !important;
        resize: vertical !important;
        max-height: 160px !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin: 0 !important;
    }

    .stChatInput textarea:focus {
        border-color: #14B8A6 !important;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15) !important;
        outline: none !important;
    }

    .stChatInput textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 0.8 !important;
    }

    /* Enhanced Search Results Header */
    h1, h2 {
        background: linear-gradient(135deg, #2DD4BF 0%, #14B8A6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(45, 212, 191, 0.3);
        font-weight: 800;
    }

    /* Scrollbar Styling for All Elements */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1E293B;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #14B8A6 0%, #0F766E 100%);
        border-radius: 4px;
        border: 1px solid #0F172A;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #2DD4BF 0%, #14B8A6 100%);
    }

    /* Simple Clean Spinner */
    .stSpinner > div {
        border-color: #14B8A6 !important;
        border-top-color: transparent !important;
    }

    /* Progress Bar and Status Messages */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #14B8A6 0%, #0F766E 100%) !important;
        border-radius: 4px !important;
    }

    .stProgress > div > div {
        background: #1E293B !important;
        border-radius: 4px !important;
        border: 1px solid #334155 !important;
    }

    /* Professional Alert/Info/Success styling */
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        border-radius: 12px !important;
        border-left: 4px solid #14B8A6 !important;
        padding: 1rem 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }

    .stAlert p, .stInfo p, .stSuccess p, .stWarning p, .stError p {
        color: #F1F5F9 !important;
        margin: 0 !important;
    }

    /* Enhanced Modal Styling */
    div[data-testid="stModal"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        background-color: rgba(0, 0, 0, 0.8) !important;
        backdrop-filter: blur(4px) !important;
        z-index: 9999 !important;
        padding: 2rem !important;
    }

    div[data-testid="stModal"] > div:first-child {
        position: relative !important;
        width: 90% !important;
        max-width: 700px !important;
        max-height: 90vh !important;
        transform: none !important;
        border-radius: 20px !important;
        background: linear-gradient(135deg, #0E1117 0%, #1E293B 100%) !important;
        border: 1px solid #334155 !important;
        box-shadow:
            0 20px 60px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(20, 184, 166, 0.1) !important;
        overflow: hidden !important;
    }

    /* Modal header styling */
    div[data-testid="stModal"] h1,
    div[data-testid="stModal"] h2,
    div[data-testid="stModal"] h3 {
        background: linear-gradient(135deg, #2DD4BF 0%, #14B8A6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #14B8A6 !important;
    }

    /* Modal close button enhancement */
    div[data-testid="stModal"] button[kind="headerNoPadding"] {
        position: absolute !important;
        top: 1rem !important;
        right: 1rem !important;
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%) !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        border: none !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        z-index: 10000 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div[data-testid="stModal"] button[kind="headerNoPadding"]:hover {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
        transform: scale(1.1) !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4) !important;
    }
    .card-title {
        color: #14B8A6;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .card-brand {
        color: #FFFFFF;
        font-weight: bold;
    }



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

    /* Keep sidebar always visible and nicely styled */
    .stSidebar {
        background-color: #0E1117 !important;
        border-right: 1px solid #334155 !important;
    }

    /* Make main content area adjust properly */
    .main .block-container {
        padding-left: 1rem !important;
        max-width: none !important;
    }

    /* Hide any remaining toggle elements that might appear */
    [class*="toggle"], [class*="Toggle"], [class*="collapse"], [class*="Collapse"] {
        display: none !important;
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