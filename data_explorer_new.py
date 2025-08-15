import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Import web scraping module for business research
try:
    from modules.web_scraping_module import perform_web_scraping
except ImportError:
    perform_web_scraping = None

def create_data_explorer(df, identifier_cols):
    """
    Simple Data Explorer with Primary and Secondary filters - NEW VERSION
    """
    
    # Title exactly as requested
    st.title("📊 Data Explorer")

    if df is None or len(df) == 0:
        st.warning("No data available to explore.")
        return
    
    # Get categorical columns
    categorical_cols = []
    object_cols = df.select_dtypes(include=['object']).columns.tolist()
    categorical_cols.extend(object_cols)
    
    if identifier_cols:
        categorical_cols.extend([col for col in identifier_cols if col not in categorical_cols])
    
    categorical_cols = sorted(list(set(categorical_cols)))
    
    if not categorical_cols:
        st.info("No categorical columns found for filtering.")
        st.dataframe(df.head(100), use_container_width=True)
        return
    
    # Filter section header exactly as requested
    st.subheader("🔍 Filter Your Data:")
    
    # Two columns layout exactly as shown in screenshot
    col1, col2 = st.columns(2)
    
    # LEFT COLUMN - Primary Filter
    with col1:
        st.write("**Primary Filter**")
        primary_filter_col = st.selectbox(
            "Select Column",
            ["None"] + categorical_cols,
            key="new_primary_col"
        )
        
        if primary_filter_col != "None":
            unique_values = ["All"] + sorted([str(val) for val in df[primary_filter_col].dropna().unique()])
            primary_filter_value = st.selectbox(
                f"Filter by {primary_filter_col}",
                unique_values,
                key="new_primary_val"
            )
            
            primary_search = st.text_input(
                f"Search in {primary_filter_col}",
                placeholder="Enter search term...",
                key="new_primary_search"
            )
        else:
            primary_filter_value = "All"
            primary_search = ""
    
    # RIGHT COLUMN - Secondary Filter  
    with col2:
        st.write("**Secondary Filter**")
        secondary_options = [col for col in categorical_cols if col != primary_filter_col]
        
        secondary_filter_col = st.selectbox(
            "Select Column",
            ["None"] + secondary_options,
            key="new_secondary_col"
        )
        
        if secondary_filter_col != "None":
            unique_values = ["All"] + sorted([str(val) for val in df[secondary_filter_col].dropna().unique()])
            secondary_filter_value = st.selectbox(
                f"Filter by {secondary_filter_col}",
                unique_values,
                key="new_secondary_val"
            )
            
            secondary_search = st.text_input(
                f"Search in {secondary_filter_col}",
                placeholder="Enter search term...",
                key="new_secondary_search"
            )
        else:
            secondary_filter_value = "All"
            secondary_search = ""
    
    # Apply filters
    filtered_df = df.copy()
    
    # Apply primary filter
    if primary_filter_col != "None":
        if primary_filter_value != "All":
            filtered_df = filtered_df[filtered_df[primary_filter_col].astype(str) == primary_filter_value]
        
        if primary_search:
            mask = filtered_df[primary_filter_col].astype(str).str.contains(primary_search, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    # Apply secondary filter
    if secondary_filter_col != "None":
        if secondary_filter_value != "All":
            filtered_df = filtered_df[filtered_df[secondary_filter_col].astype(str) == secondary_filter_value]
        
        if secondary_search:
            mask = filtered_df[secondary_filter_col].astype(str).str.contains(secondary_search, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    # Results summary
    st.markdown("---")
    
    # Display metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("📊 Records", f"{len(filtered_df):,}")
    with col_m2:
        pct = (len(filtered_df) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("📈 % of Total", f"{pct:.1f}%")
    with col_m3:
        st.metric("🔢 Columns", len(filtered_df.columns))
    with col_m4:
        completeness = (1 - filtered_df.isnull().sum().sum() / (len(filtered_df) * len(filtered_df.columns))) * 100 if len(filtered_df) > 0 else 0
        st.metric("✅ Quality", f"{completeness:.1f}%")
    
    # Display filtered data
    if len(filtered_df) == 0:
        st.warning("No records match your filter criteria.")
        return
    
    # Display options
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        max_rows = min(500, len(filtered_df))
        if max_rows <= 10:
            rows_to_show = max_rows
        else:
            rows_to_show = st.slider("Rows to display:", 10, max_rows, min(100, max_rows))
    
    with col_d2:
        st.write(f"Showing {min(rows_to_show, len(filtered_df))} of {len(filtered_df)} rows")
    
    # Show data
    st.dataframe(filtered_df.head(rows_to_show), use_container_width=True, height=400)
    
    # Download and actions
    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        if len(filtered_df) > 0:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📊 Download CSV",
                csv,
                f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col_a2:
        if len(filtered_df) > 0:
            if st.button("🔍 Business Research", help="Find contact information for businesses in the filtered data"):
                st.session_state.show_business_research = True
                st.session_state.research_data = filtered_df
    
    # Show business research interface if button was clicked
    if st.session_state.get('show_business_research', False):
        st.markdown("---")
        st.subheader("🔍 Business Contact Research")
        
        st.markdown("""
        **Find contact information for businesses using AI-powered web scraping.**
        
        This tool searches the web and extracts:
        - 📞 Phone numbers
        - 📧 Email addresses  
        - 🌐 Website URLs
        - 📍 Business addresses
        - 📋 Company descriptions
        """)
        
        # Add close button
        if st.button("❌ Close Business Research"):
            st.session_state.show_business_research = False
            st.session_state.research_data = None
            st.rerun()
        
        # Call the web scraping functionality
        if perform_web_scraping:
            research_df = st.session_state.get('research_data', filtered_df)
            perform_web_scraping(research_df)
        else:
            st.error("⚠️ Business research module not available. Please check your installation.")