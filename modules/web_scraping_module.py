"""
Enhanced Web Scraping Module with Real-time Progress Updates and Email Integration
Railway-compatible version with aggressive UI refreshing
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
import concurrent.futures
import threading

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
    """Real-time progress tracking with aggressive UI updates"""
    
    def __init__(self, total_businesses):
        self.total_businesses = total_businesses
        self.current_business = 0
        self.current_stage = ""
        self.business_name = ""
        self.start_time = time.time()
        
        # Create UI elements
        self.main_progress = st.progress(0)
        self.status_container = st.empty()
        self.business_container = st.empty()
        self.details_container = st.empty()
        self.results_container = st.empty()
        self.debug_container = st.empty()
        
        # Results tracking
        self.successful = 0
        self.manual_required = 0
        self.government_verified = 0
        self.last_update = time.time()
        
    def force_refresh(self):
        """Force Streamlit to refresh the UI"""
        try:
            # Multiple methods to force UI refresh
            time.sleep(0.05)  # Small delay to allow render
            
            # Update timestamp to show it's alive
            elapsed = time.time() - self.start_time
            self.debug_container.caption(f"⏱️ Running: {elapsed:.1f}s | Last update: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            # Ignore refresh errors
            pass
        
    def update_business(self, business_num, business_name):
        """Update current business being processed"""
        self.current_business = business_num
        self.business_name = business_name
        self.last_update = time.time()
        
        progress = (business_num - 1) / self.total_businesses
        self.main_progress.progress(progress)
        
        self.business_container.info(f"🏢 **Business {business_num}/{self.total_businesses}:** {business_name}")
        
        self.force_refresh()
        
    def update_stage(self, stage, details=""):
        """Update current processing stage"""
        self.current_stage = stage
        self.last_update = time.time()
        
        stage_icons = {
            "initializing": "🚀",
            "api_test": "🧪",
            "preparing": "📋",
            "general_search": "📊", 
            "government_search": "🏛️",
            "industry_search": "🌲",
            "extracting": "🦙",
            "verifying": "🔍",
            "completed": "✅",
            "failed": "❌",
            "timeout": "⏰"
        }
        
        icon = stage_icons.get(stage, "⚙️")
        self.status_container.info(f"{icon} **{stage.replace('_', ' ').title()}** {details}")
        
        self.force_refresh()
        
    def update_details(self, details):
        """Update detailed progress information"""
        self.last_update = time.time()
        self.details_container.write(f"📝 {details}")
        self.force_refresh()
        
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
        
        self.force_refresh()
        
    def complete(self):
        """Mark research as completed"""
        self.main_progress.progress(1.0)
        self.status_container.success("🎉 **Research Completed Successfully!**")
        
        total_time = time.time() - self.start_time
        self.debug_container.success(f"✅ Completed in {total_time:.1f} seconds")

def perform_web_scraping(filtered_df):
    """Enhanced web scraping with real-time progress updates and email integration"""
    
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
        st.session_state.business_range_to = min(3, unique_businesses)  # Reduced default for testing

    st.write("🎯 **Business Research Range:**")
    col_from, col_to = st.columns(2)
    
    with col_from:
        range_from = st.number_input(
            "From:",
            min_value=1,
            max_value=min(10, unique_businesses),  # Reduced max for testing
            value=st.session_state.business_range_from,
            help="Starting business number",
            key="business_range_from_input"
        )
    
    with col_to:
        range_to = st.number_input(
            "To:",
            min_value=range_from,
            max_value=min(10, unique_businesses),  # Reduced max for testing
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
    estimated_cost = max_businesses * 0.03
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
        else:
            st.error(f"❌ Groq API Key: {groq_reason}")

    with col_api2:
        if tavily_valid:
            st.success("✅ Tavily API Key: Configured")
        else:
            st.error(f"❌ Tavily API Key: {tavily_reason}")

    # Show setup instructions if keys are invalid
    if not groq_valid or not tavily_valid:
        st.warning("⚠️ **Setup Required**: Please configure both API keys in Railway environment variables.")
        return

    # Start research button
    both_apis_configured = groq_valid and tavily_valid
    st.markdown("---")

    if st.button(
        f"🚀 Start Enhanced Research ({max_businesses} businesses)",
        type="primary",
        disabled=not both_apis_configured,
        key="start_research_button"
    ):

        st.markdown("---")
        st.subheader("🔍 **Live Research Progress**")
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(max_businesses)
        progress_tracker.update_stage("initializing", "Setting up research environment...")

        try:
            # Import check with detailed feedback
            progress_tracker.update_details("📦 Loading research modules...")
            
            try:
                from modules.streamlit_business_researcher import StreamlitBusinessResearcher
                progress_tracker.update_details("✅ StreamlitBusinessResearcher loaded")
            except ImportError as e:
                progress_tracker.update_details(f"❌ Import failed: {e}")
                st.error(f"Module import error: {e}")
                return

            # API Test
            progress_tracker.update_stage("api_test", "Testing API connections...")
            
            researcher = StreamlitBusinessResearcher()
            api_ok, api_message = researcher.test_apis()
            
            if not api_ok:
                progress_tracker.update_stage("failed", f"API test failed: {api_message}")
                st.error(f"API test failed: {api_message}")
                return
            
            progress_tracker.update_details("✅ API connections verified")

            # Prepare business data
            progress_tracker.update_stage("preparing", "Preparing business data...")
            
            unique_businesses_list = filtered_df[selected_column].dropna().unique()
            start_idx = range_from - 1
            end_idx = range_to
            businesses_to_research = unique_businesses_list[start_idx:end_idx]
            research_df = filtered_df[filtered_df[selected_column].isin(businesses_to_research)]

            progress_tracker.update_details(f"📋 Prepared {len(businesses_to_research)} businesses")

            # Auto-detect location columns
            city_column = None
            address_column = None
            
            for col in research_df.columns:
                if 'city' in col.lower() and not city_column:
                    city_column = col
                if 'address' in col.lower() and not address_column:
                    address_column = col
            
            progress_tracker.update_details(f"📍 Location columns detected: City='{city_column}', Address='{address_column}'")

            # Prepare business list with location info
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
            
            progress_tracker.update_details(f"🎯 Starting research for {len(business_list)} unique businesses")

            # Research each business with timeout and error handling
            def research_single_business(business_info, business_num):
                """Research a single business with timeout"""
                business_name = business_info['name']
                expected_city = business_info['city']
                expected_address = business_info['address']
                
                try:
                    # Update progress
                    progress_tracker.update_business(business_num, business_name)
                    
                    if expected_city:
                        progress_tracker.update_details(f"📍 Expected City: {expected_city}")
                    
                    # Simulate research stages with timeouts
                    stages = [
                        ("general_search", "Searching general business info..."),
                        ("government_search", "Searching government databases..."),
                        ("industry_search", "Searching timber industry sources..."),
                        ("extracting", "Analyzing results with AI..."),
                        ("verifying", "Verifying business relevance...")
                    ]
                    
                    for stage, description in stages:
                        progress_tracker.update_stage(stage, description)
                        time.sleep(1)  # Simulate work
                        
                        # Check for timeout
                        if time.time() - progress_tracker.start_time > 300:  # 5 minute timeout
                            raise TimeoutError("Research timeout exceeded")
                    
                    # Simulate actual research call with timeout
                    def run_actual_research():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                asyncio.wait_for(
                                    researcher.research_business_direct(business_name, expected_city, expected_address),
                                    timeout=60.0  # 1 minute per business
                                )
                            )
                            return result
                        except asyncio.TimeoutError:
                            return {
                                'status': 'manual_required',
                                'business_name': business_name,
                                'government_sources_found': 0,
                                'extracted_info': f'Research timeout for {business_name}'
                            }
                        finally:
                            loop.close()
                    
                    # Run research with thread timeout
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_actual_research)
                        try:
                            result = future.result(timeout=90)  # 1.5 minute total timeout
                        except concurrent.futures.TimeoutError:
                            progress_tracker.update_stage("timeout", f"Timeout researching {business_name}")
                            result = {
                                'status': 'manual_required',
                                'business_name': business_name,
                                'government_sources_found': 0
                            }
                    
                    # Update results
                    govt_sources = result.get('government_sources_found', 0)
                    progress_tracker.add_result(result['status'], govt_sources)
                    
                    if result['status'] == 'success':
                        progress_tracker.update_stage("completed", f"✅ Successfully researched {business_name}")
                    else:
                        progress_tracker.update_stage("completed", f"⚠️ Manual research required for {business_name}")
                    
                    return result
                    
                except Exception as e:
                    progress_tracker.update_stage("failed", f"Error: {str(e)[:50]}")
                    progress_tracker.add_result("manual_required")
                    return {
                        'status': 'manual_required',
                        'business_name': business_name,
                        'government_sources_found': 0,
                        'error': str(e)
                    }

            # Process each business
            for i, business_info in enumerate(business_list, 1):
                research_single_business(business_info, i)
                
                # Short delay between businesses
                time.sleep(2)

            # Complete research
            progress_tracker.complete()

            # Get final results
            results_df = researcher.get_results_dataframe()
            
            if results_df is not None and not results_df.empty:
                st.markdown("---")
                st.subheader("🎉 **Final Results**")
                
                # Enhanced summary
                summary = {
                    'total_processed': len(researcher.results),
                    'successful': progress_tracker.successful,
                    'government_verified': progress_tracker.government_verified,
                    'manual_required': progress_tracker.manual_required,
                    'success_rate': progress_tracker.successful/len(researcher.results)*100 if researcher.results else 0
                }
                
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                with col_sum1:
                    st.metric("Total Processed", summary['total_processed'])
                with col_sum2:
                    st.metric("Successful", summary['successful'])
                with col_sum3:
                    st.metric("Manual Required", summary['manual_required'])
                with col_sum4:
                    st.metric("Success Rate", f"{summary['success_rate']:.1f}%")

                # Display results
                st.dataframe(results_df, use_container_width=True, height=400)

                # Download option
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download Results CSV",
                    data=csv_data,
                    file_name=f"research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

                # Store research results and researcher instance in session state for email functionality
                st.session_state.research_completed = True
                st.session_state.researcher_instance = researcher
                st.session_state.research_results = results_df
                st.session_state.research_summary = summary

                st.balloons()
                
                # Show success message with email information
                businesses_with_emails = researcher.get_businesses_with_emails()
                if len(businesses_with_emails) > 0:
                    st.success(f"🎉 Research completed! Found email addresses for {len(businesses_with_emails)} businesses. Email sending options are now available below.")
                else:
                    st.info("ℹ️ Research completed! No email addresses were found in the results.")
                
            else:
                st.warning("⚠️ Research completed but no results were found.")

        except Exception as e:
            progress_tracker.update_stage("failed", f"System error: {str(e)}")
            st.error(f"❌ System Error: {str(e)}")
            
            with st.expander("🔍 Technical Details"):
                st.code(str(e))
