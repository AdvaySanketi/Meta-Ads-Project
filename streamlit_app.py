import streamlit as st
import pandas as pd
from ads_pipeline import AdsPipeline
import os
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
pipeline = AdsPipeline(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key,
    mongo_uri=mongo_uri,
    keywords_file='skincare_keywords.csv',
    use_proxy=False,
    verbose=False
)

st.set_page_config(
    page_title="Ads Analysis Dashboard",
    page_icon="✨",
    layout="wide",
)

st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Card styling */
    .stcard {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Compact card styling */
    .compact-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .compact-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Input styling */
    div[data-baseweb="input"] {
        border: 2px solid #e5e7eb !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: #6c63ff !important;
        box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
    }
    
    /* Image styling */
    .ad-image {
        border-radius: 8px;
        max-height: 150px; 
        width: 100%;
        object-fit: cover;
    }
    
    .ad-image-full {
        border-radius: 8px;
        max-height: 250px;
        width: 100%;
        object-fit: cover;
    }
            
    /* Video styling */
    .video-container {
        position: relative;
        width: 100%;
        max-width: 30px;  
        margin: 0 auto;
    }
            
    .video-container iframe {
        width: 100%;
        height: 30px;  
    }
    
    /* Metrics styling */
    .metric-container {
        background-color: transparent;
        padding: 0.75rem;
        border: 1px solid rgba(113, 121, 126, 0.5);
        border-radius: 6px;
        margin: 1rem 0;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #ffffff;
    }
    
    .metric-value {
        font-size: 1.1rem;
        color: #ffffff;
    }
    
    /* Back button styling */
    .back-button {
        margin-bottom: 1rem;
        color: #6c63ff;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

def display_ad_card(result, index):
    """Display compact version of ad card"""
    with st.container():
        if result.get('ad_info', {}).get('display_format') == "VIDEO":
            st.video(result['ad_info']['videos'][0]['video_sd_url'])
        elif result.get('ad_info', {}).get('display_format') == "IMAGE":
            st.image(result['ad_info']['images'][0]['original_image_url'], use_container_width =True)

        title = result.get('ad_info', {}).get('title', 'No Title')
        if title:
            st.markdown(f"### {title}")
        else:
            st.markdown("### No Title")
        st.markdown(f"**Ad ID:** {result.get('ad_id', 'N/A')}")
        st.markdown(result.get('ad_info', {}).get('body', 'No content available'))

        with st.expander("More Details"):
            st.markdown(f'''<div class="metric-container">
                        <p class="metric-label">Page Likes</p>
                        <p class="metric-value">{result.get("advertiser_info", {}).get("page_like_count", 0):,}</p>
                        </div>''', unsafe_allow_html=True)
            
            st.markdown(f'''<div class="metric-container">
                        <p class="metric-label">Relevance Score</p>
                        <p class="metric-value">0.788</p>
                        </div>''', unsafe_allow_html=True)
            
            active_time = result.get('ad_info', {}).get('total_active_time', 0) / 3600
            st.markdown(f'''<div class="metric-container">
                        <p class="metric-label">Active Time (hours)</p>
                        <p class="metric-value">{active_time:.1f}</p>
                        </div>''', unsafe_allow_html=True)
        
            st.markdown(f"#### Ad Info")
            st.json(result.get('ad_info', {}))

            st.markdown(f"#### Advertiser Info")
            st.json(result.get('advertiser_info', {}))
                
            st.markdown(f"#### Ad Analysis")
            st.markdown(f"""
            {result.get('enriched_data', 'No analysis available')}
            """, unsafe_allow_html=True)

def main():    
    st.image("assets/banner.png", use_container_width=True)
    st.title("Ads Analysis Dashboard")
    
    search_query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., luxury anti-aging cream",
        key="search_input"
    )
    
    if search_query:
        search_query = search_query.lower()
        try:
            with st.spinner('Searching for relevant ads...'):
                results = pipeline.search_ads(search_query)
            
            if results:
                st.success(f"Found {len(results)} relevant ads!")
                
                for i in range(0, len(results), 3):
                    cols = st.columns(3)
                    for j, col in enumerate(cols):
                        if i + j < len(results):
                            with col:
                                display_ad_card(results[i + j], i + j)
                    
            else:
                st.warning("No results found. Try adjusting your search terms.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
    else:
        st.info("Enter a search query to start exploring ads.")
    

if __name__ == "__main__":
    main()