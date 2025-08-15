"""
Basic Web Scraping Module for Business Contact Research
Simplified version with only basic functionality
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
import asyncio
import importlib
import dotenv
from dotenv import load_dotenv

def perform_web_scraping(filtered_df):
    """Basic web scraping of business contact information from filtered data"""
    
    # Check if DataFrame is empty
    if len(filtered_df) == 0:
        st.error("❌ No data to scrape. Please adjust your filters.")
        return

    # Find suitable columns for business names
    potential_name_columns = []
    for col in filtered_df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['consignee', 'name', 'company', 'business', 'shipper', 'supplier']):
            potential_name_columns.append(col)

    if not potential_name_columns:
        st.error("❌ No suitable business name columns found. Need columns like 'Consignee Name', 'Company Name', etc.")
        return

    # User selects which column to use for business names
    st.write("🏷️ **Select Business Name Column:**")
    selected_column = st.selectbox(
        "Choose the column containing business names:",
        potential_name_columns,
        help="Select the column that contains the business names you want to research",
        key="business_name_column_selector"
    )

    # Check unique business count
    unique_businesses = filtered_df[selected_column].dropna().nunique()
    if unique_businesses == 0:
        st.error(f"❌ No business names found in column '{selected_column}'")
        return

    st.info(f"📊 Found {unique_businesses} unique businesses to research in '{selected_column}'")

    # Research limit selection
    if 'business_range_from' not in st.session_state:
        st.session_state.business_range_from = 1
    if 'business_range_to' not in st.session_state:
        st.session_state.business_range_to = min(5, unique_businesses)

    st.write("🎯 **Business Research Range:**")
    col_from, col_to = st.columns(2)
    
    with col_from:
        range_from = st.number_input(
            "From:",
            min_value=1,
            max_value=min(20, unique_businesses),
            value=st.session_state.business_range_from,
            help="Starting business number",
            key="business_range_from_input"
        )
    
    with col_to:
        range_to = st.number_input(
            "To:",
            min_value=range_from,
            max_value=min(20, unique_businesses),
            value=max(st.session_state.business_range_to, range_from),
            help="Ending business number",
            key="business_range_to_input"
        )
    
    # Calculate number of businesses to research
    max_businesses = range_to - range_from + 1
    
    # Update session state
    st.session_state.business_range_from = range_from
    st.session_state.business_range_to = range_to
    
    # Show summary
    st.info(f"📊 Will research businesses {range_from} to {range_to} ({max_businesses} total businesses)")

    # Cost estimation
    estimated_cost = max_businesses * 0.03  # Rough estimate
    st.warning(f"💰 **Estimated API Cost:** ~${estimated_cost:.2f} (approx $0.03 per business)")

    # API Configuration check
    st.write("🔧 **API Configuration:**")

    # Force reload environment variables
    importlib.reload(dotenv)
    load_dotenv(override=True)

    groq_key = os.getenv('GROQ_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')

    # Key validation
    def is_valid_key(key, key_type):
        if not key or key.strip() == '':
            return False, "Key is empty or missing"
        if key.strip() in ['your_groq_key_here', 'your_tavily_key_here', 'gsk_...', 'tvly-...']:
            return False, "Key is a placeholder value"
        if key_type == 'groq' and not key.startswith('gsk_'):
            return False, "Groq key should start with 'gsk_'"
        if key_type == 'tavily' and not key.startswith('tvly-'):
            return False, "Tavily key should start with 'tvly-'"
        return True, "Key format is valid"

    groq_valid, groq_reason = is_valid_key(groq_key, 'groq')
    tavily_valid, tavily_reason = is_valid_key(tavily_key, 'tavily')

    # Display status
    col_api1, col_api2 = st.columns(2)

    with col_api1:
        if groq_valid:
            st.success("✅ Groq API Key: Configured")
            masked_key = f"{groq_key[:10]}...{groq_key[-4:]}" if len(groq_key) > 14 else f"{groq_key[:6]}..."
            st.caption(f"Key: {masked_key}")
        else:
            st.error(f"❌ Groq API Key: {groq_reason}")
            st.caption("Add GROQ_API_KEY to .env file")

    with col_api2:
        if tavily_valid:
            st.success("✅ Tavily API Key: Configured")
            masked_key = f"{tavily_key[:10]}...{tavily_key[-4:]}" if len(tavily_key) > 14 else f"{tavily_key[:6]}..."
            st.caption(f"Key: {masked_key}")
        else:
            st.error(f"❌ Tavily API Key: {tavily_reason}")
            st.caption("Add TAVILY_API_KEY to .env file")

    # Show setup instructions if keys are invalid
    if not groq_valid or not tavily_valid:
        st.warning("⚠️ **Setup Required**: Please configure both API keys before starting research.")

        with st.expander("📝 Setup Instructions", expanded=False):
            st.markdown("""
            **To set up API keys:**

            1. **Edit your .env file** in the app directory
            2. **Add your API keys:**
               ```
               GROQ_API_KEY=gsk_your_actual_groq_key_here
               TAVILY_API_KEY=tvly-your_actual_tavily_key_here
               ```
            3. **Restart the app**
            4. **Get API keys from:**
               - [Groq API Keys](https://console.groq.com/keys)
               - [Tavily API](https://tavily.com)
            """)

    # Start research button
    both_apis_configured = groq_valid and tavily_valid
    st.markdown("---")

    button_disabled = not both_apis_configured
    button_help = f"Research {max_businesses} businesses using basic web scraping" if both_apis_configured else "Configure both API keys first"

    if st.button(
        f"🚀 Start Basic Research ({max_businesses} businesses)",
        type="primary",
        disabled=button_disabled,
        help=button_help,
        key="start_research_button"
    ):

        if not both_apis_configured:
            st.error("❌ Cannot start research: API keys not properly configured")
            return

        st.info("🔄 Starting basic business research...")

        try:
            # Import the basic business researcher
            modules_path = os.path.dirname(__file__)
            if modules_path not in sys.path:
                sys.path.insert(0, modules_path)
                
            from streamlit_business_researcher import research_businesses_from_dataframe

            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.info("🚀 Initializing research system...")
            progress_bar.progress(10)

            with st.spinner("Researching businesses using basic web scraping..."):

                # Get unique business names and slice properly
                unique_businesses_list = filtered_df[selected_column].dropna().unique()
                start_idx = range_from - 1
                end_idx = range_to
                businesses_to_research = unique_businesses_list[start_idx:end_idx]
                research_df = filtered_df[filtered_df[selected_column].isin(businesses_to_research)]

                st.info(f"🎯 **Researching businesses {range_from} to {range_to}:**")
                for i, business in enumerate(businesses_to_research, start=range_from):
                    st.write(f"   {i}. {business}")

                # Run the async research function
                async def run_research():
                    return await research_businesses_from_dataframe(
                        df=research_df,
                        consignee_column=selected_column,
                        max_businesses=len(businesses_to_research),
                        enable_justdial=False  # Disable enhanced features
                    )

                status_text.info("🔍 Starting business research process...")
                progress_bar.progress(20)

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    status_text.info("🌐 Connecting to research APIs...")
                    progress_bar.progress(30)

                    results_df, summary, csv_filename = loop.run_until_complete(run_research())
                    loop.close()

                    progress_bar.progress(90)
                    status_text.info("✅ Research completed successfully!")

                except Exception as e:
                    st.error(f"❌ Research Error: {str(e)}")
                    return

                progress_bar.progress(100)
                status_text.success("✅ Research completed!")

                # Check if we got valid results
                if results_df is not None and not results_df.empty:
                    # Display summary
                    st.success(f"🎉 **Basic Research Summary:**")
                    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)

                    with col_sum1:
                        st.metric("Total Processed", summary['total_processed'])
                    with col_sum2:
                        st.metric("Successful", summary['successful'])
                    with col_sum3:
                        st.metric("Manual Required", summary['manual_required'])
                    with col_sum4:
                        st.metric("Success Rate", f"{summary['success_rate']:.1f}%")

                    # Display results table
                    st.subheader("📈 Research Results")
                    st.dataframe(results_df, use_container_width=True, height=400)

                    # Download results
                    st.subheader("📅 Download Research Results")
                    csv_data = results_df.to_csv(index=False)

                    st.download_button(
                        label="📄 Download Research Results CSV",
                        data=csv_data,
                        file_name=f"basic_business_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    # Success message
                    st.balloons()
                    st.success(f"🎉 Successfully researched {summary['successful']} businesses!")

                    if summary['manual_required'] > 0:
                        st.info(f"🔍 {summary['manual_required']} businesses require manual research")

                else:
                    st.warning("⚠️ Research completed but no results were found.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")