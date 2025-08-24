"""
CSV Research Results Integration Module
Adds research results back to the original input CSV file
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
        Integrate research results back into original CSV
        
        Args:
            matching_strategy: 'exact', 'fuzzy', or 'manual'
            confidence_threshold: Minimum confidence for fuzzy matching
        """
        if self.original_df is None or self.research_results_df is None:
            raise ValueError("Both original data and research results must be set")
            
        # Create a copy of original data
        integrated_df = self.original_df.copy()
        
        # Add research result columns
        research_columns = [
            'research_phone', 'research_email', 'research_website', 
            'research_address', 'research_city', 'research_description',
            'research_registration_number', 'research_government_verified',
            'research_confidence', 'research_date', 'research_status',
            'research_match_confidence'
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
        """Perform exact string matching"""
        matched_count = 0
        for idx, row in integrated_df.iterrows():
            business_name = str(row[self.business_name_column]).strip()
            
            # Find exact match in research results
            research_match = self.research_results_df[
                self.research_results_df['business_name'].str.strip() == business_name
            ]
            
            if not research_match.empty:
                self._update_row_with_research(integrated_df, idx, research_match.iloc[0], 1.0)
                matched_count += 1
        
        st.info(f"✅ Exact matching completed: {matched_count} businesses matched")
    
    def _fuzzy_matching(self, integrated_df, threshold=0.8):
        """Perform fuzzy string matching using similarity scores"""
        matched_count = 0
        
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
                self._update_row_with_research(integrated_df, idx, best_match, best_score)
                matched_count += 1
        
        st.info(f"✅ Fuzzy matching completed: {matched_count} businesses matched (threshold: {threshold})")
    
    def _manual_matching(self, integrated_df):
        """Allow manual matching through Streamlit interface"""
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
        for original_name, research_name in matches.items():
            research_match = self.research_results_df[
                self.research_results_df['business_name'] == research_name
            ]
            
            if not research_match.empty:
                matching_rows = integrated_df[integrated_df[self.business_name_column] == original_name]
                for idx in matching_rows.index:
                    self._update_row_with_research(integrated_df, idx, research_match.iloc[0], 1.0)
                    matched_count += 1
        
        if matched_count > 0:
            st.success(f"✅ Manual matching completed: {matched_count} businesses matched")
    
    def _update_row_with_research(self, df, row_idx, research_data, confidence):
        """Update a specific row with research data"""
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
            'research_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'research_status': research_data.get('status', 'completed'),
            'research_match_confidence': f"{confidence:.2f}"
        }
        
        for col, value in mapping.items():
            df.at[row_idx, col] = value
    
    def export_integrated_csv(self, filename=None):
        """Export the integrated CSV file"""
        if self.integrated_df is None:
            raise ValueError("No integrated data available. Run integration first.")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"integrated_research_results_{timestamp}.csv"
        
        # Save to CSV format
        csv_data = self.integrated_df.to_csv(index=False)
        
        return csv_data, filename
    
    def get_integration_summary(self):
        """Get summary of integration results"""
        if self.integrated_df is None:
            return None
            
        total_rows = len(self.integrated_df)
        researched_rows = len(self.integrated_df[
            self.integrated_df['research_status'] != 'Not researched'
        ])
        
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
        
        return {
            'total_rows': total_rows,
            'researched_rows': researched_rows,
            'research_coverage': (researched_rows / total_rows * 100) if total_rows > 0 else 0,
            'emails_found': with_emails,
            'phones_found': with_phones,
            'government_verified': govt_verified
        }

def add_csv_integration_interface():
    """Add CSV integration interface to the main app"""
    
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
                
                # Show integration summary
                summary = integrator.get_integration_summary()
                if summary:
                    st.markdown("### 📊 **Integration Summary**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Records", summary['total_rows'])
                    with col2:
                        st.metric("Researched", summary['researched_rows'])
                    with col3:
                        st.metric("📧 Emails Found", summary['emails_found'])
                    with col4:
                        st.metric("📞 Phones Found", summary['phones_found'])
                    
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
            st.info("🔄 **Auto-Integration Detected**: Using results from previous integration.")        
        
        # Show sample of integrated data
        with st.expander("🔍 View Integrated Data (First 10 rows)", expanded=True):
            # Show only key columns for preview
            preview_cols = [col for col in integrated_df.columns 
                          if not col.startswith('research_') or col in 
                          ['research_email', 'research_phone', 'research_website']][:10]
            
            st.dataframe(
                integrated_df[preview_cols].head(10) if preview_cols else integrated_df.head(10),
                use_container_width=True,
                height=400
            )
        
        # Export options
        st.markdown("### 📥 **Export Integrated Data**")
        
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
                    filename = f"integrated_research_results_{timestamp}.csv"
                    csv_data = integrated_df.to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Full Integrated CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download complete data with research results",
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")
                st.info("📝 Using session state data for download...")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"integrated_research_results_{timestamp}.csv"
                csv_data = integrated_df.to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Full Integrated CSV (Backup)",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download complete data with research results",
                    type="secondary"
                )
        
        with col2:
            # Export only researched records
            researched_only = integrated_df[
                integrated_df['research_status'] != 'Not researched'
            ]
            if not researched_only.empty:
                csv_researched = researched_only.to_csv(index=False)
                st.download_button(
                    label="🔬 Download Researched Only",
                    data=csv_researched,
                    file_name=f"researched_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download only records with research data"
                )
        
        with col3:
            # Export contact list
            contact_fields = [st.session_state.selected_business_column, 'research_email', 'research_phone', 
                            'research_website', 'research_address', 'research_city']
            
            if all(col in integrated_df.columns for col in contact_fields):
                contacts_df = integrated_df[contact_fields].copy()
                contacts_df = contacts_df[
                    (contacts_df['research_email'] != 'Not found') & 
                    (contacts_df['research_email'] != 'Not researched')
                ]
                
                if not contacts_df.empty:
                    csv_contacts = contacts_df.to_csv(index=False)
                    st.download_button(
                        label="📧 Download Contact List",
                        data=csv_contacts,
                        file_name=f"business_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Download contact information only"
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
    """Show integration status in sidebar"""
    
    if st.session_state.get('research_completed', False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔄 Integration Status")
        
        research_results = st.session_state.get('research_results')
        if research_results is not None:
            total_researched = len(research_results)
            with_emails = len(research_results[
                (research_results['email'] != 'Not found') & 
                (research_results['email'] != 'Not researched')
            ])
            
            st.sidebar.metric("Businesses Researched", total_researched)
            st.sidebar.metric("📧 Email Addresses Found", with_emails)
            
            if st.session_state.get('integrated_df') is not None:
                st.sidebar.success("✅ Results Integrated")
                st.sidebar.download_button(
                    "📥 Quick Download",
                    data=st.session_state.integrated_df.to_csv(index=False),
                    file_name=f"integrated_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.sidebar.info("🔄 Ready for Integration")