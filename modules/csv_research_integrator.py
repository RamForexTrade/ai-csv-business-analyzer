"""
CSV Research Results Integration Module
Adds research results back to the original input CSV file
Now includes enhanced research status tracking and duplicate prevention
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import os
import tempfile
from pathlib import Path
from difflib import SequenceMatcher

class CSVResearchIntegrator:
    """
    Integrates business research results back into the original CSV file
    Now with enhanced research status tracking to prevent duplicates
    """
    
    def __init__(self):
        self.original_df = None
        self.research_results_df = None
        self.integrated_df = None
        self.business_name_column = None
        
    def set_original_data(self, df, business_name_column):
        """Set the original CSV data and business name column"""
        self.original_df = df.copy()
        self.business_name_column = business_name_column
        
    def set_research_results(self, research_df):
        """Set the research results from the business researcher"""
        self.research_results_df = research_df.copy()
        
    def integrate_research_results(self, matching_strategy='fuzzy', confidence_threshold=0.8):
        """
        Integrate research results back into original CSV with enhanced status tracking
        
        Args:
            matching_strategy: 'exact', 'fuzzy', or 'manual'
            confidence_threshold: Minimum confidence for fuzzy matching
        """
        if self.original_df is None or self.research_results_df is None:
            raise ValueError("Both original data and research results must be set")
            
        # Create a copy of original data
        integrated_df = self.original_df.copy()
        
        # Enhanced research result columns with status tracking
        research_columns = [
            'research_phone', 'research_email', 'research_website', 
            'research_address', 'research_city', 'research_description',
            'research_registration_number', 'research_government_verified',
            'research_confidence', 'research_date', 'research_status',
            'research_match_confidence', 'research_method', 'research_sources_found',
            'research_industry_relevant', 'research_location_relevant',
            'research_govt_sources', 'research_industry_sources'
        ]
        
        # Initialize research columns with default values
        for col in research_columns:
            integrated_df[col] = 'Not researched'
            
        # Perform matching based on strategy
        if matching_strategy == 'exact':
            self._exact_matching(integrated_df)
        elif matching_strategy == 'fuzzy':
            self._fuzzy_matching(integrated_df, confidence_threshold)
        elif matching_strategy == 'manual':
            self._manual_matching(integrated_df)
            
        self.integrated_df = integrated_df
        return integrated_df
    
    def _exact_matching(self, integrated_df):
        """Perform exact string matching with case-insensitive comparison and enhanced status tracking"""
        matched_count = 0
        total_original = len(integrated_df)
        
        # Create lookup dictionary for faster matching (case-insensitive)
        research_lookup = {}
        for idx, row in self.research_results_df.iterrows():
            if pd.notna(row.get('business_name')):
                clean_name = str(row['business_name']).strip()
                clean_name_lower = clean_name.lower()  # Use lowercase for matching
                research_lookup[clean_name_lower] = row
        
        # Perform matching (case-insensitive exact matching)
        unmatched_names = []
        cached_results = []
        
        for idx, row in integrated_df.iterrows():
            if pd.notna(row.get(self.business_name_column)):
                business_name = str(row[self.business_name_column]).strip()
                business_name_lower = business_name.lower()  # Compare in lowercase
                
                # Try exact match (case-insensitive)
                if business_name_lower in research_lookup:
                    research_data = research_lookup[business_name_lower]
                    self._update_row_with_enhanced_research(integrated_df, idx, research_data, 1.0)
                    matched_count += 1
                    
                    # Track if this was a cached result
                    if research_data.get('research_status') == 'cached':
                        cached_results.append(business_name)
                else:
                    unmatched_names.append(business_name)
        
        # Show enhanced matching results
        st.success(f"✅ **Exact matching completed: {matched_count}/{total_original} businesses matched**")
        
        if cached_results:
            st.info(f"🔄 **{len(cached_results)} businesses used cached results** (previously researched)")
        
        if unmatched_names:
            st.warning(f"⚠️ **{len(unmatched_names)} businesses not matched**")
            with st.expander("View unmatched business names"):
                for name in unmatched_names[:10]:  # Show first 10
                    st.write(f"- {name}")
                if len(unmatched_names) > 10:
                    st.write(f"... and {len(unmatched_names) - 10} more")
        
        return matched_count
    
    def _fuzzy_matching(self, integrated_df, threshold=0.8):
        """Perform fuzzy string matching using similarity scores with enhanced status tracking"""
        matched_count = 0
        cached_count = 0
        
        for idx, row in integrated_df.iterrows():
            business_name = str(row[self.business_name_column]).strip().lower()
            
            best_match = None
            best_score = 0
            
            # Find best fuzzy match
            for _, research_row in self.research_results_df.iterrows():
                research_name = str(research_row['business_name']).strip().lower()
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, business_name, research_name).ratio()
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = research_row
            
            if best_match is not None:
                self._update_row_with_enhanced_research(integrated_df, idx, best_match, best_score)
                matched_count += 1
                
                if best_match.get('research_status') == 'cached':
                    cached_count += 1
        
        st.info(f"✅ Fuzzy matching completed: {matched_count} businesses matched (threshold: {threshold})")
        if cached_count > 0:
            st.info(f"🔄 {cached_count} businesses used cached results")
    
    def _manual_matching(self, integrated_df):
        """Allow manual matching through Streamlit interface with enhanced status tracking"""
        st.subheader("🔗 Manual Business Matching")
        st.write("Match businesses from your original data with research results:")
        
        unmatched_businesses = integrated_df[self.business_name_column].unique()
        research_businesses = ['None'] + list(self.research_results_df['business_name'].unique())
        
        matches = {}
        
        # Show matching interface for first 10 businesses
        for i, business in enumerate(unmatched_businesses[:10]):
            selected_match = st.selectbox(
                f"Match '{business}' with:",
                research_businesses,
                key=f"match_{business}_{i}"
            )
            
            if selected_match != 'None':
                matches[business] = selected_match
        
        if len(unmatched_businesses) > 10:
            st.info(f"Showing first 10 businesses. Total: {len(unmatched_businesses)}")
        
        # Apply manual matches
        matched_count = 0
        cached_count = 0
        
        for original_name, research_name in matches.items():
            research_match = self.research_results_df[
                self.research_results_df['business_name'] == research_name
            ]
            
            if not research_match.empty:
                matching_rows = integrated_df[integrated_df[self.business_name_column] == original_name]
                for idx in matching_rows.index:
                    self._update_row_with_enhanced_research(integrated_df, idx, research_match.iloc[0], 1.0)
                    matched_count += 1
                    
                    if research_match.iloc[0].get('research_status') == 'cached':
                        cached_count += 1
        
        if matched_count > 0:
            st.success(f"✅ Manual matching completed: {matched_count} businesses matched")
            if cached_count > 0:
                st.info(f"🔄 {cached_count} businesses used cached results")
    
    def _update_row_with_enhanced_research(self, df, row_idx, research_data, confidence):
        """Update a specific row with enhanced research data including status tracking"""
        try:
            # Enhanced mapping with status tracking and additional fields
            mapping = {
                'research_phone': research_data.get('phone', 'Not found'),
                'research_email': research_data.get('email', 'Not found'),
                'research_website': research_data.get('website', 'Not found'),
                'research_address': research_data.get('address', 'Not found'),
                'research_city': research_data.get('city', 'Not found'),
                'research_description': research_data.get('description', 'Not found'),
                'research_registration_number': research_data.get('registration_number', 'Not found'),
                'research_government_verified': research_data.get('government_verified', 'NO'),
                'research_confidence': research_data.get('confidence', 5),
                'research_date': research_data.get('research_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'research_status': research_data.get('research_status', 'completed'),
                'research_match_confidence': f"{confidence:.2f}",
                'research_method': research_data.get('method', 'Unknown method'),
                'research_sources_found': research_data.get('total_sources', 0),
                'research_industry_relevant': research_data.get('industry_relevant', 'UNKNOWN'),
                'research_location_relevant': research_data.get('location_relevant', 'UNKNOWN'),
                'research_govt_sources': research_data.get('govt_sources_found', 0),
                'research_industry_sources': research_data.get('industry_sources_found', 0)
            }
            
            for col, value in mapping.items():
                if col in df.columns:  # Only update if column exists
                    df.at[row_idx, col] = value
                    
        except Exception as e:
            st.warning(f"Error updating row {row_idx}: {str(e)}")
            # At minimum, mark as researched even if data update fails
            if 'research_status' in df.columns:
                df.at[row_idx, 'research_status'] = research_data.get('research_status', 'completed')
    
    def export_integrated_csv(self, filename=None):
        """Export the integrated CSV file with enhanced data"""
        if self.integrated_df is None:
            raise ValueError("No integrated data available. Run integration first.")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"integrated_research_results_{timestamp}.csv"
        
        # Save to CSV format
        csv_data = self.integrated_df.to_csv(index=False)
        
        return csv_data, filename
    
    def get_integration_summary(self):
        """Get enhanced summary of integration results with status tracking"""
        if self.integrated_df is None:
            return None
            
        total_rows = len(self.integrated_df)
        researched_rows = len(self.integrated_df[
            self.integrated_df['research_status'] != 'Not researched'
        ])
        
        # Count different research statuses
        status_counts = {}
        if 'research_status' in self.integrated_df.columns:
            status_counts = self.integrated_df['research_status'].value_counts().to_dict()
        
        with_emails = len(self.integrated_df[
            (self.integrated_df['research_email'] != 'Not found') & 
            (self.integrated_df['research_email'] != 'Not researched')
        ])
        
        with_phones = len(self.integrated_df[
            (self.integrated_df['research_phone'] != 'Not found') & 
            (self.integrated_df['research_phone'] != 'Not researched')
        ])
        
        govt_verified = len(self.integrated_df[
            self.integrated_df['research_government_verified'] == 'YES'
        ])
        
        # Count cached results
        cached_results = len(self.integrated_df[
            self.integrated_df['research_status'] == 'cached'
        ])
        
        return {
            'total_rows': total_rows,
            'researched_rows': researched_rows,
            'research_coverage': (researched_rows / total_rows * 100) if total_rows > 0 else 0,
            'emails_found': with_emails,
            'phones_found': with_phones,
            'government_verified': govt_verified,
            'cached_results': cached_results,
            'status_breakdown': status_counts,
            'successful_research': status_counts.get('success', 0) + status_counts.get('completed', 0),
            'manual_required': status_counts.get('manual_required', 0),
            'billing_errors': status_counts.get('billing_error', 0)
        }

def add_csv_integration_interface():
    """Add enhanced CSV integration interface with research status tracking"""
    
    st.markdown("### 🔄 **Integrate Research Results with Original CSV**")
    
    if not st.session_state.get('research_completed', False):
        st.info("🔬 Complete business research first to integrate results with your CSV.")
        st.markdown("""
        **How to get started:**
        1. Go to the **📊 Data Explorer** tab
        2. Filter your data to specific businesses
        3. Click **🔍 Business Research** to find contact information
        4. Return here to integrate the results with your original CSV
        """)
        return
    
    if st.session_state.get('research_results') is None:
        st.warning("⚠️ No research results found. Please run business research first.")
        return
    
    # Initialize integrator and sync with session state if needed
    if 'csv_integrator' not in st.session_state:
        st.session_state.csv_integrator = CSVResearchIntegrator()
    
    integrator = st.session_state.csv_integrator
    
    # Show research status summary if available
    if st.session_state.get('research_results') is not None:
        research_df = st.session_state.research_results
        
        # Enhanced status summary
        st.markdown("#### 📊 **Research Status Summary**")
        col1, col2, col3, col4 = st.columns(4)
        
        total_researched = len(research_df)
        cached_count = len(research_df[research_df.get('research_status', '') == 'cached']) if 'research_status' in research_df.columns else 0
        successful_count = len(research_df[research_df.get('research_status', '').isin(['success', 'completed'])]) if 'research_status' in research_df.columns else 0
        manual_count = len(research_df[research_df.get('research_status', '') == 'manual_required']) if 'research_status' in research_df.columns else 0
        
        with col1:
            st.metric("Total Researched", total_researched)
        with col2:
            st.metric("🔄 Cached Results", cached_count)
        with col3:
            st.metric("✅ Successful", successful_count)
        with col4:
            st.metric("⚠️ Manual Required", manual_count)
    
    # Sync with session state data if auto-integration was used
    if (st.session_state.get('integrated_df') is not None and 
        integrator.integrated_df is None and
        st.session_state.get('uploaded_df') is not None and
        st.session_state.get('research_results') is not None):
        
        # Set up the integrator with session state data
        integrator.set_original_data(
            st.session_state.uploaded_df, 
            st.session_state.get('selected_business_column', 'business_name')
        )
        integrator.set_research_results(st.session_state.research_results)
        integrator.integrated_df = st.session_state.integrated_df.copy()
        
        st.success("✅ **Auto-Integration Results Found**: Ready to export integrated data.")
    
    # Validate prerequisites
    errors, warnings = validate_integration_prerequisites()
    
    if errors:
        st.error("❌ **Cannot proceed with integration:**")
        for error in errors:
            st.write(f"• {error}")
        return
    
    if warnings:
        st.warning("⚠️ **Please note:**")
        for warning in warnings:
            st.write(f"• {warning}")
    
    # Set original data
    if 'uploaded_df' in st.session_state and 'selected_business_column' in st.session_state:
        integrator.set_original_data(
            st.session_state.uploaded_df, 
            st.session_state.selected_business_column
        )
        integrator.set_research_results(st.session_state.research_results)
        
        # Show data info
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Original CSV Rows", len(st.session_state.uploaded_df))
        with col_info2:
            st.metric("Research Results", len(st.session_state.research_results))
    
    # Configuration options
    st.markdown("### ⚙️ **Integration Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        matching_strategy = st.selectbox(
            "🔗 Matching Strategy:",
            ['exact', 'fuzzy', 'manual'],
            help="How to match businesses between original data and research results"
        )
    
    with col2:
        if matching_strategy == 'fuzzy':
            confidence_threshold = st.slider(
                "🎯 Match Confidence Threshold:",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                help="Minimum similarity score for fuzzy matching"
            )
        else:
            confidence_threshold = 0.8
    
    # Integration button
    if st.button("🔄 Integrate Research Results", type="primary"):
        try:
            with st.spinner("🔄 Integrating research results with original data..."):
                integrated_df = integrator.integrate_research_results(
                    matching_strategy=matching_strategy,
                    confidence_threshold=confidence_threshold
                )
                
                # Store integrated results
                st.session_state.integrated_df = integrated_df
                
                st.success("✅ Research results successfully integrated!")
                
                # Show enhanced integration summary
                summary = integrator.get_integration_summary()
                if summary:
                    st.markdown("### 📊 **Enhanced Integration Summary**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Records", summary['total_rows'])
                    with col2:
                        st.metric("Researched", summary['researched_rows'])
                    with col3:
                        st.metric("📧 Emails Found", summary['emails_found'])
                    with col4:
                        st.metric("📞 Phones Found", summary['phones_found'])
                    
                    # Show status breakdown
                    col5, col6, col7, col8 = st.columns(4)
                    with col5:
                        st.metric("🔄 Cached Results", summary['cached_results'])
                    with col6:
                        st.metric("✅ Successful", summary['successful_research'])
                    with col7:
                        st.metric("🏛️ Govt Verified", summary['government_verified'])
                    with col8:
                        st.metric("⚠️ Manual Required", summary['manual_required'])
                    
                    st.info(f"🎯 Research Coverage: {summary['research_coverage']:.1f}%")
                
        except Exception as e:
            st.error(f"❌ Integration failed: {str(e)}")
    
    # Show integrated results and export option
    if 'integrated_df' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 **Integrated Results Preview**")
        
        integrated_df = st.session_state.integrated_df
        
        # Sync session state data with integrator instance if needed
        if integrator.integrated_df is None and integrated_df is not None:
            integrator.integrated_df = integrated_df.copy()
            st.info("🔄 **Auto-Integration Results Available**: Ready to export integrated data.")        
        
        # Show sample of integrated data with enhanced columns
        with st.expander("🔍 View Enhanced Integrated Data (First 10 rows)", expanded=True):
            # Show key columns including status tracking
            preview_cols = []
            
            # Always include business name
            if st.session_state.get('selected_business_column'):
                preview_cols.append(st.session_state.selected_business_column)
            
            # Add research result columns
            research_cols = ['research_email', 'research_phone', 'research_website', 
                           'research_status', 'research_government_verified', 'research_confidence']
            
            for col in research_cols:
                if col in integrated_df.columns:
                    preview_cols.append(col)
            
            # Limit total columns shown
            preview_cols = preview_cols[:12]
            
            st.dataframe(
                integrated_df[preview_cols].head(10) if preview_cols else integrated_df.head(10),
                use_container_width=True,
                height=400
            )
        
        # Export options
        st.markdown("### 📥 **Export Enhanced Integrated Data**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export full integrated CSV - Handle both integrator and session state data
            try:
                # First try to use integrator data if available
                if integrator.integrated_df is not None:
                    csv_data, filename = integrator.export_integrated_csv()
                else:
                    # Fallback to session state data (from auto-integration)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"enhanced_integrated_research_results_{timestamp}.csv"
                    csv_data = integrated_df.to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Full Enhanced CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download complete data with enhanced research results and status tracking",
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")
                # Fallback to session state data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_integrated_research_results_{timestamp}.csv"
                csv_data = integrated_df.to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Enhanced CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download complete data with enhanced research results",
                    type="secondary"
                )
        
        with col2:
            # Export only successfully researched records (excluding cached and manual required)
            successful_only = integrated_df[
                integrated_df['research_status'].isin(['success', 'completed'])
            ]
            if not successful_only.empty:
                csv_successful = successful_only.to_csv(index=False)
                st.download_button(
                    label="✅ Download Successful Research Only",
                    data=csv_successful,
                    file_name=f"successful_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download only records with successful research data"
                )
        
        with col3:
            # Export contact list (with valid emails only)
            contact_fields = [st.session_state.selected_business_column, 'research_email', 'research_phone', 
                            'research_website', 'research_address', 'research_city', 'research_status',
                            'research_government_verified', 'research_confidence']
            
            if all(col in integrated_df.columns for col in contact_fields):
                contacts_df = integrated_df[contact_fields].copy()
                contacts_df = contacts_df[
                    (contacts_df['research_email'] != 'Not found') & 
                    (contacts_df['research_email'] != 'Not researched') &
                    (~contacts_df['research_email'].str.contains('not relevant', case=False, na=False))
                ]
                
                if not contacts_df.empty:
                    csv_contacts = contacts_df.to_csv(index=False)
                    st.download_button(
                        label="📧 Download Enhanced Contact List",
                        data=csv_contacts,
                        file_name=f"enhanced_business_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Download contact information with research status and verification details"
                    )

def validate_integration_prerequisites():
    """Validate that all prerequisites for integration are met"""
    
    errors = []
    warnings = []
    
    # Check if original data is loaded
    if not st.session_state.get('uploaded_df') is not None:
        errors.append("Original CSV data not found")
    
    # Check if research is completed
    if not st.session_state.get('research_completed', False):
        warnings.append("Business research not completed")
    
    # Check if research results exist
    if st.session_state.get('research_results') is None:
        warnings.append("No research results available")
    
    # Check if business column is selected
    if not st.session_state.get('selected_business_column'):
        warnings.append("Business name column not identified")
    
    return errors, warnings

def show_integration_status_sidebar():
    """Show enhanced integration status in sidebar with research status tracking"""
    
    if st.session_state.get('research_completed', False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔄 Enhanced Integration Status")
        
        research_results = st.session_state.get('research_results')
        if research_results is not None:
            total_researched = len(research_results)
            
            # Count different statuses
            status_counts = {}
            if 'research_status' in research_results.columns:
                status_counts = research_results['research_status'].value_counts().to_dict()
            
            # Count valid emails
            with_emails = len(research_results[
                (research_results['email'] != 'Not found') & 
                (research_results['email'] != 'Not researched') &
                (~research_results['email'].str.contains('not relevant', case=False, na=False))
            ])
            
            st.sidebar.metric("Total Researched", total_researched)
            st.sidebar.metric("📧 Valid Email Addresses", with_emails)
            
            # Show status breakdown
            cached_count = status_counts.get('cached', 0)
            successful_count = status_counts.get('success', 0) + status_counts.get('completed', 0)
            
            if cached_count > 0:
                st.sidebar.metric("🔄 Cached Results", cached_count)
            if successful_count > 0:
                st.sidebar.metric("✅ New Successful Research", successful_count)
            
            if st.session_state.get('integrated_df') is not None:
                st.sidebar.success("✅ Results Integrated")
                st.sidebar.download_button(
                    "📥 Quick Download",
                    data=st.session_state.integrated_df.to_csv(index=False),
                    file_name=f"enhanced_integrated_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.sidebar.info("🔄 Ready for Integration")
