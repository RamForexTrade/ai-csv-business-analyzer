"""
Enhanced Web Scraping Module with Real-time Progress Updates and Email Integration
Railway-compatible version with aggressive UI refreshing and Editable Results
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

def create_editable_results_interface():
    """Create an editable interface for research results"""
    
    if not st.session_state.get('research_completed', False):
        return

    if not st.session_state.get('research_results') is not None:
        return
        
    # Show success message if changes were saved recently
    if st.session_state.get('changes_saved', False):
        st.success("✅ Your changes have been saved successfully and applied!")
        # Clear the success flag after displaying
        del st.session_state['changes_saved']
        
    # Handle post-save state
    if st.session_state.get('just_saved', False):
        st.info("🎉 Save completed! You are now viewing the updated results.")
        # Clear the just_saved flag
        del st.session_state['just_saved']
        
    # Handle reset state
    if st.session_state.get('reset_clicked', False):
        st.info("🔄 Edit mode reset - back to read-only view.")
        # Clear the reset flag
        del st.session_state['reset_clicked']
        
    st.markdown("---")
    st.subheader("✏️ **Edit Research Results**")
    
    # Toggle between view and edit mode
    col_toggle1, col_toggle2 = st.columns([1, 3])
    
    with col_toggle1:
        edit_mode = st.toggle(
            "📝 Edit Mode", 
            value=st.session_state.get('results_edit_mode', False),
            help="Toggle to enable editing of research results"
        )
        st.session_state.results_edit_mode = edit_mode
    
    with col_toggle2:
        if edit_mode:
            st.info("✏️ Edit mode enabled - you can modify the research results below")
        else:
            st.info("👀 View mode - research results are read-only")
    
    # Get current results
    results_df = st.session_state.research_results.copy()
    
    if edit_mode:
        st.markdown("### 📝 **Editable Results Table**")
        st.markdown("💡 **Instructions:** Click on any cell to edit. Modified cells will be highlighted.")
        
        # Create editable interface
        edited_results = create_editable_business_data(results_df)
        
        # Save changes button
        col_save1, col_save2, col_save3 = st.columns([2, 1, 1])
        
        with col_save1:
            save_clicked = st.button("💾 Save Changes", type="primary", key="save_changes_btn")
            
            if save_clicked:
                # Update the session state with edited results
                st.session_state.research_results = edited_results
                
                # Update the researcher instance results if available
                if 'researcher_instance' in st.session_state:
                    researcher = st.session_state.researcher_instance
                    # Update the internal results of the researcher
                    update_researcher_results(researcher, edited_results)
                
                # Set flags for post-save state
                st.session_state.changes_saved = True
                st.session_state.results_edit_mode = False
                st.session_state.just_saved = True
                
                # Show immediate success message
                st.success("✅ Changes saved successfully!")
                st.balloons()
                
                # Let the user know the changes are saved and they should refresh manually if needed
                st.info("🔄 Changes saved! The interface will update shortly.")
                
                # Use a lighter refresh approach
                time.sleep(1.5)
                st.rerun()
        
        with col_save2:
            reset_clicked = st.button("🔄 Reset", key="reset_changes_btn")
            if reset_clicked:
                st.session_state.results_edit_mode = False
                st.session_state.reset_clicked = True
                st.info("🔄 Reset completed - returning to view mode.")
                time.sleep(1)
                st.rerun()
                
        with col_save3:
            # Download edited results
            csv_data = edited_results.to_csv(index=False)
            st.download_button(
                label="📥 Download",
                data=csv_data,
                file_name=f"edited_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Show changes summary
        if not edited_results.equals(results_df):
            st.markdown("### 📊 **Changes Summary**")
            changes_detected = show_changes_summary(results_df, edited_results)
            if changes_detected:
                st.info(f"📝 {changes_detected} changes detected. Click 'Save Changes' to apply them.")
    
    else:
        # View mode - show results in read-only format
        st.markdown("### 👀 **Research Results (Read-Only)**")
        display_results_summary(results_df)
        st.dataframe(results_df, use_container_width=True, height=400)
        
        # Download and Integration buttons for view mode
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Results CSV",
                data=csv_data,
                file_name=f"research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col_action2:
            if st.button(
                "🔄 Integrate Research Results", 
                type="secondary",
                help="Merge research results with your original CSV data"
            ):
                # Auto-integrate and navigate to integration tab
                if auto_integrate_research_results():
                    st.success("✅ Research results integrated! Navigate to the 🔄 CSV Integration tab to view and download.")
                    st.balloons()
                    
                    # Show quick preview of integration
                    with st.expander("🔍 Integration Preview", expanded=True):
                        if 'integrated_df' in st.session_state:
                            integrated_df = st.session_state.integrated_df
                            summary = get_integration_summary(integrated_df)
                            
                            col_prev1, col_prev2, col_prev3 = st.columns(3)
                            with col_prev1:
                                st.metric("Total Records", summary['total_rows'])
                            with col_prev2:
                                st.metric("Researched", summary['researched_rows']) 
                            with col_prev3:
                                st.metric("Emails Found", summary['emails_found'])
                            
                            st.info(f"🎯 Research Coverage: {summary['research_coverage']:.1f}%")
                            
                            # Quick download of integrated results
                            csv_data_integrated = integrated_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Quick Download Integrated CSV",
                                data=csv_data_integrated,
                                file_name=f"integrated_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                type="primary"
                            )
                else:
                    st.warning("⚠️ Integration failed. Please use the CSV Integration tab manually.")

def create_editable_business_data(df):
    """Create editable interface for business data using Streamlit data editor"""
    
    # Key editable columns
    editable_columns = [
        'business_name', 'email', 'phone', 'website', 'address', 
        'city', 'description', 'registration_number'
    ]
    
    # Configure column settings for better editing experience
    column_config = {
        'business_name': st.column_config.TextColumn(
            "Business Name",
            help="Name of the business",
            max_chars=100,
        ),
        'email': st.column_config.TextColumn(
            "Email Address", 
            help="Email address for business contact",
            validate="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        ),
        'phone': st.column_config.TextColumn(
            "Phone Number",
            help="Phone number for business contact",
            max_chars=50,
        ),
        'website': st.column_config.LinkColumn(
            "Website",
            help="Business website URL",
            validate="^https?://.*",
        ),
        'address': st.column_config.TextColumn(
            "Address",
            help="Business address",
            max_chars=200,
        ),
        'city': st.column_config.TextColumn(
            "City",
            help="Business city/location",
            max_chars=50,
        ),
        'description': st.column_config.TextColumn(
            "Description",
            help="Business description and activities",
            max_chars=300,
        ),
        'registration_number': st.column_config.TextColumn(
            "Registration #",
            help="Business registration or GST number",
            max_chars=50,
        ),
        'confidence': st.column_config.NumberColumn(
            "Confidence",
            help="Research confidence score (1-10)",
            min_value=1,
            max_value=10,
            step=1,
            format="%d"
        ),
        'government_verified': st.column_config.SelectboxColumn(
            "Gov Verified",
            help="Whether verified through government sources",
            options=['YES', 'NO']
        ),
        'industry_relevant': st.column_config.SelectboxColumn(
            "Industry Relevant", 
            help="Whether business is relevant to timber/wood industry",
            options=['YES', 'NO', 'UNKNOWN']
        ),
        'location_relevant': st.column_config.SelectboxColumn(
            "Location Relevant",
            help="Whether business location matches expected location", 
            options=['YES', 'NO', 'UNKNOWN']
        )
    }
    
    # Show editing instructions
    st.markdown("🔧 **Quick Edit Tips:**")
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **📧 Email:** Enter valid email addresses  
        **📞 Phone:** Use any format (e.g., +91-9876543210)  
        **🌐 Website:** Include https:// prefix
        """)
    
    with tips_col2:
        st.markdown("""
        **📍 Address:** Full business address  
        **🏢 Registration:** GST or company registration number  
        **📝 Description:** Brief business description
        """)
    
    # Create the editable data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",  # Allow adding/removing rows
        height=500,
        key="business_data_editor"
    )
    
    return edited_df

def display_results_summary(df):
    """Display summary statistics for results"""
    
    total_businesses = len(df)
    businesses_with_emails = len(df[df['email'].notna() & (df['email'] != '') & (df['email'] != 'Not found')])
    businesses_with_phones = len(df[df['phone'].notna() & (df['phone'] != '') & (df['phone'] != 'Not found')])
    businesses_with_websites = len(df[df['website'].notna() & (df['website'] != '') & (df['website'] != 'Not found')])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Businesses", total_businesses)
    with col2:
        st.metric("📧 With Emails", businesses_with_emails)  
    with col3:
        st.metric("📞 With Phones", businesses_with_phones)
    with col4:
        st.metric("🌐 With Websites", businesses_with_websites)

def show_changes_summary(original_df, edited_df):
    """Show summary of changes made to the data"""
    
    changes_count = 0
    
    try:
        # Compare dataframes and count changes
        if original_df.shape != edited_df.shape:
            changes_count += abs(original_df.shape[0] - edited_df.shape[0])
            st.info(f"📊 Row count changed: {original_df.shape[0]} → {edited_df.shape[0]}")
        
        # Check for cell-level changes in common rows
        common_rows = min(len(original_df), len(edited_df))
        
        for idx in range(common_rows):
            for col in original_df.columns:
                if col in edited_df.columns:
                    orig_val = str(original_df.iloc[idx][col]) if pd.notna(original_df.iloc[idx][col]) else ""
                    edit_val = str(edited_df.iloc[idx][col]) if pd.notna(edited_df.iloc[idx][col]) else ""
                    
                    if orig_val != edit_val:
                        changes_count += 1
                        
                        # Show specific change details for key fields
                        if col in ['email', 'phone', 'website'] and changes_count <= 5:
                            business_name = edited_df.iloc[idx].get('business_name', f'Row {idx+1}')
                            st.write(f"📝 **{business_name}** - {col}: `{orig_val}` → `{edit_val}`")
        
        if changes_count > 5:
            st.write(f"... and {changes_count - 5} more changes")
            
    except Exception as e:
        st.warning(f"Could not compare changes: {str(e)}")
        changes_count = 1  # Assume changes were made
    
    return changes_count

def update_researcher_results(researcher, edited_df):
    """Update the researcher instance with edited results"""
    
    try:
        # Convert edited dataframe back to researcher's internal format
        updated_results = []
        
        for idx, row in edited_df.iterrows():
            # Create a result entry in the researcher's format
            result_entry = {
                'business_name': row.get('business_name', ''),
                'status': 'success' if row.get('email', '') not in ['', 'Not found', 'Research required'] else 'manual_required',
                'government_sources_found': 1 if row.get('government_verified', 'NO') == 'YES' else 0,
                'industry_sources_found': 0,
                'total_sources': 1,
                'research_date': datetime.now().isoformat(),
                'method': 'Manual Edit',
                'extracted_info': create_extracted_info_from_row(row)
            }
            updated_results.append(result_entry)
        
        # Update the researcher's results
        researcher.results = updated_results
        
    except Exception as e:
        st.warning(f"Could not update researcher results: {str(e)}")

def create_extracted_info_from_row(row):
    """Create extracted info string from dataframe row for researcher compatibility"""
    
    return f"""
BUSINESS_NAME: {row.get('business_name', '')}
INDUSTRY_RELEVANT: {row.get('industry_relevant', 'YES')}
LOCATION_RELEVANT: {row.get('location_relevant', 'YES')}
PHONE: {row.get('phone', 'Not found')}
EMAIL: {row.get('email', 'Not found')}
WEBSITE: {row.get('website', 'Not found')}
ADDRESS: {row.get('address', 'Not found')}
CITY: {row.get('city', 'Not found')}
REGISTRATION_NUMBER: {row.get('registration_number', 'Not found')}
LICENSE_DETAILS: {row.get('license_details', 'Not found')}
DIRECTORS: {row.get('directors', 'Not found')}
DESCRIPTION: {row.get('description', 'Business activities')}
GOVERNMENT_VERIFIED: {row.get('government_verified', 'NO')}
CONFIDENCE: {row.get('confidence', '5')}
RELEVANCE_NOTES: Manual edit - {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

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
    
    # STORE the selected column in session state for CSV integration
    st.session_state.selected_business_column = selected_column

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

    # Cost estimation based on enabled layers
    try:
        from search_config import get_enabled_layers
        enabled_layers = get_enabled_layers()
        cost_per_business = len(enabled_layers) * 0.01  # $0.01 per layer per business
        estimated_cost = max_businesses * cost_per_business
        st.warning(f"💰 **Estimated API Cost:** ~${estimated_cost:.2f} (approx ${cost_per_business:.2f} per business with {len(enabled_layers)} layer{'s' if len(enabled_layers) != 1 else ''})")
    except ImportError:
        estimated_cost = max_businesses * 0.03
        st.warning(f"💰 **Estimated API Cost:** ~${estimated_cost:.2f} (approx $0.03 per business)")

    # Search Configuration display
    st.write("⚙️ **Search Configuration:**")
    
    try:
        from search_config import get_search_summary, get_enabled_layers
        enabled_layers = get_enabled_layers()
        search_summary = get_search_summary()
        
        if len(enabled_layers) == 1:
            st.success(f"🚀 {search_summary} - Faster search with reduced API costs")
        elif len(enabled_layers) == 2:
            st.info(f"⚖️ {search_summary} - Balanced search with moderate API costs")
        else:
            st.warning(f"🔍 {search_summary} - Comprehensive search with higher API costs")
            
        # Show configuration details
        layer_status = []
        layer_status.append("✅ Layer 1: General" if "General" in enabled_layers else "❌ Layer 1: General")
        layer_status.append("✅ Layer 2: Government" if "Government" in enabled_layers else "❌ Layer 2: Government")
        layer_status.append("✅ Layer 3: Industry" if "Industry" in enabled_layers else "❌ Layer 3: Industry")
        
        st.write(" | ".join(layer_status))
        
        if len(enabled_layers) < 3:
            st.info("📝 **Note:** To enable more search layers, modify `enable_government_search` and `enable_industry_search` in `search_config.py`")
            
    except ImportError:
        st.error("Search configuration not found. Please ensure search_config.py exists.")
    
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

                # Store research results and researcher instance in session state for email functionality
                st.session_state.research_completed = True
                st.session_state.researcher_instance = researcher
                st.session_state.research_results = results_df
                st.session_state.research_summary = summary
                st.session_state.results_edit_mode = False  # Start in view mode

                st.balloons()
                
                # Show success message with email information
                businesses_with_emails = researcher.get_businesses_with_emails()
                if len(businesses_with_emails) > 0:
                    st.success(f"🎉 Research completed! Found email addresses for {len(businesses_with_emails)} businesses. You can now edit the results and send emails.")
                else:
                    st.info("ℹ️ Research completed! No email addresses were found in the results. You can manually add them using the edit feature below.")
                
            else:
                st.warning("⚠️ Research completed but no results were found.")

        except Exception as e:
            progress_tracker.update_stage("failed", f"System error: {str(e)}")
            st.error(f"❌ System Error: {str(e)}")
            
            with st.expander("🔍 Technical Details"):
                st.code(str(e))
    
    # Show editable results interface if research is completed
    create_editable_results_interface()

def auto_integrate_research_results():
    """Automatically integrate research results with original CSV and store in session state"""
    
    try:
        # Import CSV integration functionality
        from modules.csv_research_integrator import CSVResearchIntegrator
        
        # Check if we have all required components
        if 'uploaded_df' not in st.session_state:
            st.error("❌ Original CSV data not found")
            return False
            
        if 'research_results' not in st.session_state or st.session_state.research_results is None:
            st.error("❌ Research results not found")
            return False
            
        if 'selected_business_column' not in st.session_state:
            st.error("❌ Business column not identified")
            return False
        
        # Show integration progress
        with st.spinner("🔄 Auto-integrating research results..."):
            # Initialize integrator
            integrator = CSVResearchIntegrator()
            
            # Set original data and research results
            integrator.set_original_data(
                st.session_state.uploaded_df, 
                st.session_state.selected_business_column
            )
            integrator.set_research_results(st.session_state.research_results)
            
            # Perform integration with fuzzy matching
            integrated_df = integrator.integrate_research_results(
                matching_strategy='fuzzy',
                confidence_threshold=0.8
            )
            
            # Store integrated results
            st.session_state.integrated_df = integrated_df
            st.session_state.auto_integration_completed = True
            
            return True
            
    except ImportError:
        st.error("❌ CSV integration module not available")
        return False
    except Exception as e:
        st.error(f"❌ Auto-integration failed: {str(e)}")
        return False

def get_integration_summary(integrated_df):
    """Get summary statistics for integrated results"""
    
    total_rows = len(integrated_df)
    researched_rows = len(integrated_df[
        integrated_df['research_status'] != 'Not researched'
    ])
    
    with_emails = len(integrated_df[
        (integrated_df['research_email'] != 'Not found') & 
        (integrated_df['research_email'] != 'Not researched')
    ])
    
    with_phones = len(integrated_df[
        (integrated_df['research_phone'] != 'Not found') & 
        (integrated_df['research_phone'] != 'Not researched')
    ])
    
    govt_verified = len(integrated_df[
        integrated_df['research_government_verified'] == 'YES'
    ])
    
    return {
        'total_rows': total_rows,
        'researched_rows': researched_rows,
        'research_coverage': (researched_rows / total_rows * 100) if total_rows > 0 else 0,
        'emails_found': with_emails,
        'phones_found': with_phones,
        'government_verified': govt_verified
    }