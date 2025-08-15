"""
Enhanced Web Scraping Module with Real-time Progress Updates
Railway-compatible version with live progress streaming
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
import time

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

class ProgressTracker:
    """Real-time progress tracking for Railway deployment"""
    
    def __init__(self, total_businesses):
        self.total_businesses = total_businesses
        self.current_business = 0
        self.current_stage = ""
        self.business_name = ""
        
        # Create UI elements
        self.main_progress = st.progress(0)
        self.status_container = st.empty()
        self.business_container = st.empty()
        self.details_container = st.empty()
        self.results_container = st.empty()
        
        # Results tracking
        self.successful = 0
        self.manual_required = 0
        self.government_verified = 0
        
    def update_business(self, business_num, business_name):
        """Update current business being processed"""
        self.current_business = business_num
        self.business_name = business_name
        
        progress = (business_num - 1) / self.total_businesses
        self.main_progress.progress(progress)
        
        self.business_container.info(f"🏢 **Business {business_num}/{self.total_businesses}:** {business_name}")
        
    def update_stage(self, stage, details=""):
        """Update current processing stage"""
        self.current_stage = stage
        
        stage_icons = {
            "initializing": "🚀",
            "general_search": "📊", 
            "government_search": "🏛️",
            "industry_search": "🌲",
            "extracting": "🦙",
            "verifying": "🔍",
            "completed": "✅",
            "failed": "❌"
        }
        
        icon = stage_icons.get(stage, "⚙️")
        self.status_container.info(f"{icon} **{stage.replace('_', ' ').title()}** {details}")
        
    def update_details(self, details):
        """Update detailed progress information"""
        self.details_container.write(f"📝 {details}")
        
    def add_result(self, status, government_sources=0):
        """Track research results"""
        if status == "success":
            self.successful += 1
            if government_sources > 0:
                self.government_verified += 1
        elif status == "manual_required":
            self.manual_required += 1
            
        # Update results summary
        self.results_container.write(f"""
        **📊 Progress Summary:**
        - ✅ Successful: {self.successful}
        - 🏛️ Government Verified: {self.government_verified}  
        - 🔍 Manual Required: {self.manual_required}
        """)
        
    def complete(self):
        """Mark research as completed"""
        self.main_progress.progress(1.0)
        self.status_container.success("🎉 **Research Completed Successfully!**")

def perform_web_scraping(filtered_df):
    """Enhanced web scraping with real-time progress updates"""
    
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

    # Key validation - More flexible for Railway
    def is_valid_key(key, key_type):
        if not key or key.strip() == '':
            return False, "Key is empty or missing"
        if key.strip() in ['your_groq_key_here', 'your_tavily_key_here']:
            return False, "Key is a placeholder value"
        if len(key.strip()) < 10:
            return False, "Key appears too short"
        # More flexible validation for Railway environment
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
    button_help = f"Research {max_businesses} businesses with real-time progress" if both_apis_configured else "Configure both API keys first"

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

        st.markdown("---")
        st.subheader("🔍 **Live Research Progress**")
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(max_businesses)
        progress_tracker.update_stage("initializing", "Setting up research environment...")

        try:
            # Import the enhanced business researcher with better error handling
            try:
                from modules.streamlit_business_researcher import research_businesses_from_dataframe
                progress_tracker.update_details("✅ Research module loaded successfully")
            except ImportError as e:
                progress_tracker.update_details(f"❌ Module import failed: {e}")
                # Try alternative import
                try:
                    import sys
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    sys.path.insert(0, current_dir)
                    from streamlit_business_researcher import research_businesses_from_dataframe
                    progress_tracker.update_details("✅ Research module loaded (alternative method)")
                except Exception as e2:
                    progress_tracker.update_stage("failed", f"Module import failed: {e2}")
                    return

            # Get unique business names and slice properly
            unique_businesses_list = filtered_df[selected_column].dropna().unique()
            start_idx = range_from - 1
            end_idx = range_to
            businesses_to_research = unique_businesses_list[start_idx:end_idx]
            research_df = filtered_df[filtered_df[selected_column].isin(businesses_to_research)]

            progress_tracker.update_details(f"📋 Prepared {len(businesses_to_research)} businesses for research")

            # Enhanced research function with progress callbacks
            async def run_research_with_progress():
                try:
                    # Custom research function that provides progress updates
                    from modules.streamlit_business_researcher import StreamlitBusinessResearcher
                    
                    researcher = StreamlitBusinessResearcher()
                    
                    # Test APIs
                    progress_tracker.update_stage("initializing", "Testing API connections...")
                    api_ok, api_message = researcher.test_apis()
                    if not api_ok:
                        raise Exception(f"API Test Failed: {api_message}")
                    
                    progress_tracker.update_details("✅ API connections verified")
                    
                    # Get business data with location info
                    city_column = None
                    address_column = None
                    
                    # Auto-detect city and address columns
                    for col in research_df.columns:
                        if 'city' in col.lower() and not city_column:
                            city_column = col
                        if 'address' in col.lower() and not address_column:
                            address_column = col
                    
                    progress_tracker.update_details(f"📍 Location columns: City='{city_column}', Address='{address_column}'")
                    
                    # Prepare business data
                    business_data = []
                    for _, row in research_df.iterrows():
                        business_name = row.get(selected_column)
                        if pd.notna(business_name) and str(business_name).strip():
                            city = row.get(city_column) if city_column else None
                            address = row.get(address_column) if address_column else None
                            business_data.append({
                                'name': str(business_name).strip(),
                                'city': str(city).strip() if pd.notna(city) else None,
                                'address': str(address).strip() if pd.notna(address) else None
                            })
                    
                    # Remove duplicates
                    unique_businesses = {}
                    for item in business_data:
                        if item['name'] not in unique_businesses:
                            unique_businesses[item['name']] = item
                    
                    business_list = list(unique_businesses.values())
                    
                    # Research each business with live updates
                    for i, business_info in enumerate(business_list, 1):
                        business_name = business_info['name']
                        expected_city = business_info['city']
                        expected_address = business_info['address']
                        
                        progress_tracker.update_business(i, business_name)
                        
                        if expected_city:
                            progress_tracker.update_details(f"📍 Expected City: {expected_city}")
                        if expected_address:
                            progress_tracker.update_details(f"🏠 Expected Address: {expected_address}")
                        
                        try:
                            # Layer 1: General search
                            progress_tracker.update_stage("general_search", f"Searching general business info...")
                            await asyncio.sleep(0.1)  # Allow UI update
                            
                            # Layer 2: Government search  
                            progress_tracker.update_stage("government_search", f"Searching government databases...")
                            await asyncio.sleep(0.1)  # Allow UI update
                            
                            # Layer 3: Industry search
                            progress_tracker.update_stage("industry_search", f"Searching timber industry sources...")
                            await asyncio.sleep(0.1)  # Allow UI update
                            
                            # AI extraction
                            progress_tracker.update_stage("extracting", f"Analyzing results with AI...")
                            await asyncio.sleep(0.1)  # Allow UI update
                            
                            # Actual research
                            result = await researcher.research_business_direct(
                                business_name, expected_city, expected_address
                            )
                            
                            # Verification stage
                            progress_tracker.update_stage("verifying", f"Verifying business relevance...")
                            await asyncio.sleep(0.1)  # Allow UI update
                            
                            # Update results
                            govt_sources = result.get('government_sources_found', 0)
                            progress_tracker.add_result(result['status'], govt_sources)
                            
                            if result['status'] == 'success':
                                progress_tracker.update_stage("completed", f"✅ Successfully researched {business_name}")
                            else:
                                progress_tracker.update_stage("completed", f"⚠️ Manual research required for {business_name}")
                            
                            # Short delay between businesses
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            progress_tracker.update_stage("failed", f"Error researching {business_name}: {str(e)[:50]}")
                            progress_tracker.add_result("manual_required")
                            await asyncio.sleep(1)
                    
                    # Get final results
                    results_df = researcher.get_results_dataframe()
                    
                    # Calculate summary
                    summary = {
                        'total_processed': len(researcher.results),
                        'successful': progress_tracker.successful,
                        'government_verified': progress_tracker.government_verified,
                        'manual_required': progress_tracker.manual_required,
                        'success_rate': progress_tracker.successful/len(researcher.results)*100 if researcher.results else 0,
                        'government_verification_rate': progress_tracker.government_verified/len(researcher.results)*100 if researcher.results else 0
                    }
                    
                    return results_df, summary, f"enhanced_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    
                except Exception as e:
                    progress_tracker.update_stage("failed", f"Research error: {str(e)}")
                    raise

            progress_tracker.update_stage("initializing", "Starting enhanced research process...")

            try:
                # Check if there's already an event loop running
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is already running, use concurrent execution
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, run_research_with_progress())
                            results_df, summary, csv_filename = future.result(timeout=600)  # 10 minute timeout
                    else:
                        results_df, summary, csv_filename = loop.run_until_complete(run_research_with_progress())
                except RuntimeError:
                    # No event loop, create new one
                    results_df, summary, csv_filename = asyncio.run(run_research_with_progress())

                progress_tracker.complete()

            except Exception as e:
                progress_tracker.update_stage("failed", f"Execution error: {str(e)}")
                st.error(f"❌ Research execution error: {str(e)}")
                return

            # Display final results
            if results_df is not None and not results_df.empty:
                st.markdown("---")
                st.subheader("🎉 **Final Results**")
                
                # Enhanced summary
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
                    st.metric("Govt Verified", summary['government_verified'])

                # Display results table
                st.subheader("📈 Enhanced Research Results")
                st.dataframe(results_df, use_container_width=True, height=400)

                # Download results
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

                if summary['government_verification_rate'] > 0:
                    st.success(f"🏛️ {summary['government_verification_rate']:.1f}% of businesses were verified through government sources!")

            else:
                st.warning("⚠️ Research completed but no results were found.")

        except Exception as e:
            st.error(f"❌ System Error: {str(e)}")
            
            # Show additional debugging information
            with st.expander("🔍 Technical Details", expanded=False):
                st.write("**Error Details:**")
                st.code(str(e))
                st.write("**Environment Info:**")
                st.write(f"- Platform: {os.name}")
                st.write(f"- Python: {sys.version}")
                st.write(f"- Working Dir: {os.getcwd()}")
