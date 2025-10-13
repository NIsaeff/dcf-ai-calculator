"""DCF Calculator - Main Streamlit Application."""

import streamlit as st

def main():
    st.set_page_config(
        page_title="DCF Calculator - Finance Club",
        page_icon="chart_with_upwards_trend",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("DCF Calculator")
    st.markdown("**Finance Club - Portfolio Analysis Tool**")
    
    # Import and show main page
    from stlitpages.mainpage import show_main_page
    show_main_page()

if __name__ == "__main__":
    main()
