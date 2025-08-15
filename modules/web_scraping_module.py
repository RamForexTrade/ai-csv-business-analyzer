"""
Enhanced Web Scraping Module for Business Contact Research
Railway-compatible version with improved error handling
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

def get_env_var(key, default=None):
    """Get environment variable from Railway environment or .env file"""
    # First try regular environment variables (Railway uses these)
    value = os.getenv(key)
    if value:
        return value

    # Then try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Finally try .env file (local development)
    try:
        load_dotenv()
        return os.getenv(key, default)
    except Exception:
        return default

def perform_web_scraping(filtered_df):
    """Enhanced web scraping of business contact information from filtered data"""
    
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

    # Get API keys using Railway-compatible method
    groq_key = get_env_var('GROQ_API_KEY')
    tavily_key = get_env_var('TAVILY_API_KEY')

    # Debug information for Railway
    st.write("🔍 **Debug Info:**")
    debug_col1, debug_col2 = st.columns(2)
    
    with debug_col1:
        groq_status = "Found" if groq_key else "Missing"
        st.write(f"Groq Key: {groq_status}")
        if groq_key:
            st.write(f"Length: {len(groq_key)}")
            st.write(f"Starts with: {groq_key[:10]}...")
    
    with debug_col2:
        tavily_status = "Found" if tavily_key else "Missing" 
        st.write(f"Tavily Key: {tavily_status}")
        if tavily_key:
            st.write(f"Length: {len(tavily_key)}")
            st.write(f"Starts with: {tavily_key[:10]}...")

    # Key validation - More flexible for Railway
    def is_valid_key(key, key_type):
        if not key or key.strip() == '':
            return False, "Key is empty or missing"
        if key.strip() in ['your_groq_key_here', 'your_tavily_key_here']:
            return False, "Key is a placeholder value"
        if len(key.strip()) < 10:
            return False, "Key appears too short"
        # More flexible validation for Railway environment
        if key_type == 'groq' and len(key) > 20:  # Basic length check instead of prefix
            return True, "Key format is valid"
        if key_type == 'tavily' and len(key) > 20:  # Basic length check instead of prefix
            return True, "Key format is valid"
        # Fallback - if key exists and is reasonable length, accept it
        if len(key) > 15:
            return True, "Key format appears valid"
        return False, "Key format validation failed"

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
            st.caption("Add GROQ_API_KEY to Railway environment variables")

    with col_api2:
        if tavily_valid:
            st.success("✅ Tavily API Key: Configured")
            masked_key = f"{tavily_key[:10]}...{tavily_key[-4:]}" if len(tavily_key) > 14 else f"{tavily_key[:6]}..."
            st.caption(f"Key: {masked_key}")
        else:
            st.error(f"❌ Tavily API Key: {tavily_reason}")
            st.caption("Add TAVILY_API_KEY to Railway environment variables")

    # Show setup instructions if keys are invalid
    if not groq_valid or not tavily_valid:
        st.warning("⚠️ **Setup Required**: Please configure both API keys in Railway environment variables.")

        with st.expander("📝 Railway Setup Instructions", expanded=False):
            st.markdown("""
            **To set up API keys in Railway:**

            1. **Go to your Railway project dashboard**
            2. **Click on your service**
            3. **Go to Variables tab**
            4. **Add these environment variables:**
               ```
               GROQ_API_KEY = your_actual_groq_key_here
               TAVILY_API_KEY = your_actual_tavily_key_here
               ```
            5. **Redeploy your service**
            6. **Get API keys from:**
               - [Groq API Keys](https://console.groq.com/keys)
               - [Tavily API](https://tavily.com)
            """)

    # Start research button
    both_apis_configured = groq_valid and tavily_valid
    st.markdown("---")

    button_disabled = not both_apis_configured
    button_help = f"Research {max_businesses} businesses using enhanced web scraping" if both_apis_configured else "Configure both API keys first"

    if st.button(
        f"🚀 Start Enhanced Research ({max_businesses} businesses)",
        type="primary",
        disabled=button_disabled,
        help=button_help,
        key="start_research_button"
    ):

        if not both_apis_configured:
            st.error("❌ Cannot start research: API keys not properly configured")
            return

        st.info("🔄 Starting enhanced business research...")

        try:
            # Import the enhanced business researcher with better error handling
            try:
                from modules.streamlit_business_researcher import research_businesses_from_dataframe
                st.success("✅ Successfully imported research module")
            except ImportError as e:
                st.error(f"❌ Failed to import research module: {e}")
                # Try alternative import
                try:
                    import sys
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    sys.path.insert(0, current_dir)
                    from streamlit_business_researcher import research_businesses_from_dataframe
                    st.success("✅ Successfully imported research module (alternative method)")
                except Exception as e2:
                    st.error(f"❌ Failed alternative import: {e2}")
                    return

            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.info("🚀 Initializing enhanced research system...")
            progress_bar.progress(10)

            # Get unique business names and slice properly
            unique_businesses_list = filtered_df[selected_column].dropna().unique()
            start_idx = range_from - 1
            end_idx = range_to
            businesses_to_research = unique_businesses_list[start_idx:end_idx]
            research_df = filtered_df[filtered_df[selected_column].isin(businesses_to_research)]

            st.info(f"🎯 **Researching businesses {range_from} to {range_to}:**")
            for i, business in enumerate(businesses_to_research, start=range_from):
                st.write(f"   {i}. {business}")

            status_text.info("🔍 Starting enhanced business research process...")
            progress_bar.progress(20)

            # Run the async research function with better error handling
            async def run_research():
                try:
                    return await research_businesses_from_dataframe(
                        df=research_df,
                        consignee_column=selected_column,
                        max_businesses=len(businesses_to_research),
                        enable_justdial=False
                    )
                except Exception as e:
                    st.error(f"❌ Research function error: {e}")
                    raise

            status_text.info("🌐 Connecting to research APIs...")
            progress_bar.progress(30)

            try:
                # Check if there's already an event loop running (common in deployed environments)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is already running, use asyncio.create_task (for Streamlit Cloud/Railway)
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, run_research())
                            results_df, summary, csv_filename = future.result(timeout=300)  # 5 minute timeout
                    else:
                        results_df, summary, csv_filename = loop.run_until_complete(run_research())
                except RuntimeError:
                    # No event loop, create new one
                    results_df, summary, csv_filename = asyncio.run(run_research())

                progress_bar.progress(90)
                status_text.info("✅ Research completed successfully!")

            except Exception as e:
                st.error(f"❌ Research execution error: {str(e)}")
                st.error("This might be due to API connectivity issues or environment configuration.")
                
                # Additional debugging info
                st.write("**Debug Information:**")
                st.write(f"- Groq Key Present: {bool(groq_key)}")
                st.write(f"- Tavily Key Present: {bool(tavily_key)}")
                st.write(f"- Python Version: {sys.version}")
                st.write(f"- Current Working Directory: {os.getcwd()}")
                st.write(f"- Module Path: {os.path.dirname(__file__)}")
                return

            progress_bar.progress(100)
            status_text.success("✅ Enhanced research completed!")

            # Check if we got valid results
            if results_df is not None and not results_df.empty:
                # Display enhanced summary
                st.success(f"🎉 **Enhanced Research Summary:**")
                col_sum1, col_sum2, col_sum3, col_sum4, col_sum5 = st.columns(5)

                with col_sum1:
                    st.metric("Total Processed", summary['total_processed'])
                with col_sum2:
                    st.metric("Successful", summary['successful'])
                with col_sum3:
                    st.metric("Manual Required", summary['manual_required'])
                with col_sum4:
                    st.metric("Success Rate", f"{summary['success_rate']:.1f}%")
                with col_sum5:
                    if 'government_verified' in summary:
                        st.metric("Govt Verified", summary.get('government_verified', 0))
                    else:
                        st.metric("Govt Verification", f"{summary.get('government_verification_rate', 0):.1f}%")

                # Display results table
                st.subheader("📈 Enhanced Research Results")
                
                # Show column information
                st.write("**Available Columns:**")
                cols_info = []
                for col in results_df.columns:
                    non_empty = results_df[col].notna().sum()
                    cols_info.append(f"{col} ({non_empty} filled)")
                st.write(" | ".join(cols_info))
                
                st.dataframe(results_df, use_container_width=True, height=400)

                # Download results
                st.subheader("📅 Download Enhanced Research Results")
                csv_data = results_df.to_csv(index=False)

                st.download_button(
                    label="📄 Download Enhanced Research Results CSV",
                    data=csv_data,
                    file_name=f"enhanced_business_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

                # Success message
                st.balloons()
                st.success(f"🎉 Successfully researched {summary['successful']} businesses with enhanced sources!")

                if summary['manual_required'] > 0:
                    st.info(f"🔍 {summary['manual_required']} businesses require manual research")

                # Show government verification stats if available
                if 'government_verification_rate' in summary and summary['government_verification_rate'] > 0:
                    st.success(f"🏛️ {summary['government_verification_rate']:.1f}% of businesses were verified through government sources!")

            else:
                st.warning("⚠️ Research completed but no results were found.")
                st.info("This could be due to:")
                st.write("- API connectivity issues")
                st.write("- No relevant businesses found for the wood/timber industry")
                st.write("- Location mismatch with expected addresses")

        except Exception as e:
            st.error(f"❌ System Error: {str(e)}")
            st.error("Please check the Railway logs for more detailed error information.")
            
            # Show additional debugging information
            with st.expander("🔍 Technical Details", expanded=False):
                st.write("**Error Details:**")
                st.code(str(e))
                st.write("**Environment Info:**")
                st.write(f"- Platform: {os.name}")
                st.write(f"- Python: {sys.version}")
                st.write(f"- Working Dir: {os.getcwd()}")
                st.write(f"- Available Modules: {list(sys.modules.keys())[:10]}...")
