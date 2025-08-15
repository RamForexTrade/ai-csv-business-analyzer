import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio

# Import enhanced business researcher with email integration
try:
    from modules.streamlit_business_researcher import research_businesses_from_dataframe, send_curated_business_emails
    business_research_available = True
except ImportError:
    business_research_available = False

def create_data_explorer(df, identifier_cols):
    """
    Simple Data Explorer with Primary and Secondary filters - NEW VERSION
    Now includes Email Integration after business research
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
        if len(filtered_df) > 0 and business_research_available:
            if st.button("🔍 Business Research", help="Find contact information for businesses in the filtered data"):
                st.session_state.show_business_research = True
                st.session_state.research_data = filtered_df
                # Reset research results when starting new research
                if 'research_results' in st.session_state:
                    del st.session_state.research_results
                if 'researcher_instance' in st.session_state:
                    del st.session_state.researcher_instance
    
    # Show business research interface if button was clicked
    if st.session_state.get('show_business_research', False):
        show_business_research_interface(filtered_df)

def show_business_research_interface(research_df):
    """Show the business research and email interface"""
    
    st.markdown("---")
    st.subheader("🔍 Business Contact Research & Email Outreach")
    
    # Add close button
    col_close1, col_close2 = st.columns([1, 4])
    with col_close1:
        if st.button("❌ Close", key="close_research"):
            st.session_state.show_business_research = False
            st.session_state.research_data = None
            if 'research_results' in st.session_state:
                del st.session_state.research_results
            if 'researcher_instance' in st.session_state:
                del st.session_state.researcher_instance
            st.rerun()
    
    st.markdown("""
    **🚀 Complete Business Outreach Solution:**
    
    **Step 1: Research** - AI-powered web scraping to find contact information  
    **Step 2: Email** - Send curated emails to businesses with email addresses
    
    We search for: 📞 Phone numbers, 📧 Email addresses, 🌐 Websites, 📍 Addresses, 📋 Company details
    """)
    
    # Check if research has been completed
    research_completed = 'research_results' in st.session_state and st.session_state.research_results is not None
    
    if not research_completed:
        # Show research configuration
        show_research_configuration(research_df)
    else:
        # Show research results and email options
        show_research_results_and_email_options()

def show_research_configuration(research_df):
    """Show the business research configuration"""
    
    st.markdown("### 📋 Step 1: Configure Business Research")
    
    # Column selection
    business_name_columns = [col for col in research_df.columns if any(keyword in col.lower() 
                           for keyword in ['name', 'company', 'business', 'consignee', 'shipper', 'buyer', 'supplier'])]
    
    if not business_name_columns:
        business_name_columns = list(research_df.columns)
    
    selected_column = st.selectbox(
        "📝 Select column containing business names:",
        business_name_columns,
        help="Choose the column that contains the business or company names to research"
    )
    
    # Preview businesses to research
    if selected_column:
        unique_businesses = research_df[selected_column].dropna().unique()
        st.write(f"**Found {len(unique_businesses)} unique businesses to research:**")
        
        # Show preview of businesses
        preview_businesses = list(unique_businesses)[:10]
        st.write(", ".join([str(b) for b in preview_businesses]))
        if len(unique_businesses) > 10:
            st.write(f"... and {len(unique_businesses) - 10} more")
    
    # Research settings
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        max_businesses = st.number_input(
            "🎯 Max businesses to research:",
            min_value=1,
            max_value=20,
            value=min(10, len(unique_businesses)),
            help="Recommended: 5-15 businesses for optimal results and cost"
        )
    
    with col_r2:
        estimated_cost = max_businesses * 0.03
        st.metric("💰 Estimated Cost", f"${estimated_cost:.2f}")
        st.caption("~$0.03 per business (Groq + Tavily APIs)")
    
    # Start research button
    if st.button("🚀 Start Business Research", type="primary", key="start_research"):
        if selected_column:
            start_business_research(research_df, selected_column, max_businesses)
        else:
            st.error("Please select a business name column first.")

def start_business_research(research_df, selected_column, max_businesses):
    """Start the business research process"""
    
    st.write("### 🔍 Researching Businesses...")
    
    # Create progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Run research
    async def run_research():
        try:
            status_text.text("🧪 Testing APIs...")
            
            # Run the research
            results_df, summary, csv_filename, researcher = await research_businesses_from_dataframe(
                df=research_df,
                consignee_column=selected_column,
                max_businesses=max_businesses
            )
            
            return results_df, summary, csv_filename, researcher
            
        except Exception as e:
            st.error(f"Research failed: {str(e)}")
            return None, None, None, None
    
    # Run the async research
    try:
        # Update status
        status_text.text("🔍 Starting comprehensive business research...")
        progress_bar.progress(20)
        
        # For Streamlit, we need to run async code differently
        import asyncio
        
        # Create a new event loop for this thread
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the research
        results_df, summary, csv_filename, researcher = loop.run_until_complete(run_research())
        
        progress_bar.progress(100)
        status_text.text("✅ Research completed!")
        
        if results_df is not None:
            # Store results in session state
            st.session_state.research_results = results_df
            st.session_state.research_summary = summary
            st.session_state.researcher_instance = researcher
            st.session_state.csv_filename = csv_filename
            
            st.success(f"🎉 Research completed! Found contact details for {summary['successful']} businesses.")
            st.rerun()
        else:
            st.error("Research failed. Please check your API keys and try again.")
    
    except Exception as e:
        st.error(f"Research error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Research failed")

def show_research_results_and_email_options():
    """Show research results and email configuration options"""
    
    results_df = st.session_state.research_results
    summary = st.session_state.research_summary
    researcher = st.session_state.researcher_instance
    
    st.markdown("### ✅ Step 1 Complete: Research Results")
    
    # Show summary metrics
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("🔍 Researched", summary['successful'])
    with col_s2:
        st.metric("📧 With Emails", len(researcher.get_businesses_with_emails()))
    with col_s3:
        st.metric("🏛️ Gov Verified", summary.get('government_verified', 0))
    with col_s4:
        st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
    
    # Show businesses with emails
    businesses_with_emails = researcher.get_businesses_with_emails()
    
    if len(businesses_with_emails) > 0:
        st.write(f"**📧 {len(businesses_with_emails)} businesses found with email addresses:**")
        
        # Show preview of businesses with emails
        display_df = businesses_with_emails[['business_name', 'email', 'phone', 'website', 'confidence']].head(10)
        st.dataframe(display_df, use_container_width=True)
        
        if len(businesses_with_emails) > 10:
            st.caption(f"Showing first 10 of {len(businesses_with_emails)} businesses with emails")
        
        # Email outreach section
        st.markdown("---")
        st.markdown("### 📧 Step 2: Email Outreach Campaign")
        
        show_email_configuration_and_sending(researcher, businesses_with_emails)
    
    else:
        st.warning("📧 No email addresses found in the research results. Cannot send emails.")
        st.info("💡 You can still download the research results with phone numbers, websites, and addresses.")
    
    # Download research results
    st.markdown("---")
    if st.button("📊 Download Research Results", key="download_research"):
        csv = results_df.to_csv(index=False)
        st.download_button(
            "📁 Download Complete Research Data",
            csv,
            f"business_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            key="download_research_csv"
        )

def show_email_configuration_and_sending(researcher, businesses_with_emails):
    """Show email configuration and sending interface"""
    
    # Email configuration section
    with st.expander("⚙️ Email Configuration", expanded=not st.session_state.get('email_configured', False)):
        st.markdown("**Configure your email settings to send curated business emails:**")
        
        # Email provider selection
        email_provider = st.selectbox(
            "📧 Email Provider:",
            ['gmail', 'outlook', 'yahoo'],
            help="Choose your email provider. Gmail recommended for best compatibility."
        )
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            sender_email = st.text_input(
                "📧 Your Email Address:",
                placeholder="your.email@gmail.com",
                help="Your email address that will be used to send emails"
            )
            
            sender_name = st.text_input(
                "👤 Your Name:",
                placeholder="John Smith",
                help="Your name that will appear in the emails"
            )
        
        with col_e2:
            email_password = st.text_input(
                "🔐 Email Password:",
                type="password",
                placeholder="App Password (for Gmail)",
                help="Use App Password for Gmail (not your regular password)"
            )
            
            company_name = st.text_input(
                "🏢 Your Company:",
                placeholder="Your Company Name",
                help="Your company name for email personalization"
            )
        
        # Gmail setup instructions
        if email_provider == 'gmail':
            st.info("""
            📧 **Gmail Setup Instructions:**
            1. Enable 2-Factor Authentication in your Google Account
            2. Go to Google Account > Security > App passwords
            3. Generate an App Password for 'Mail'
            4. Use the 16-character App Password above (not your regular password)
            """)
        
        # Test email configuration
        if st.button("🧪 Test Email Configuration", key="test_email"):
            if sender_email and email_password:
                with st.spinner("Testing email configuration..."):
                    # Configure email
                    success, message = researcher.configure_email(
                        email_provider=email_provider,
                        email_address=sender_email,
                        email_password=email_password,
                        sender_name=sender_name
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.email_configured = True
                        st.session_state.email_config = {
                            'provider': email_provider,
                            'email': sender_email,
                            'password': email_password,
                            'sender_name': sender_name
                        }
                        st.session_state.company_name = company_name
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("Please fill in email address and password first.")
    
    # Email template and sending section
    if st.session_state.get('email_configured', False):
        st.markdown("### 📝 Customize Email Content")
        
        # Template selection
        templates = researcher.get_email_templates()
        template_names = list(templates.keys())
        template_descriptions = {
            'business_intro': '🤝 Business Introduction - Professional introduction for partnerships',
            'supplier_inquiry': '📦 Supplier Inquiry - Product requirements and pricing requests',
            'networking': '🌐 Industry Networking - Professional networking and collaboration'
        }
        
        selected_template = st.selectbox(
            "📧 Email Template:",
            template_names,
            format_func=lambda x: template_descriptions.get(x, x),
            help="Choose the type of email you want to send"
        )
        
        # Email variables
        st.write("**Customize Email Variables:**")
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            your_phone = st.text_input("📞 Your Phone:", placeholder="+1-234-567-8900")
            product_requirements = st.text_input("📦 Product Requirements:", placeholder="High-quality timber and wood products")
            volume_requirements = st.text_input("📊 Volume Requirements:", placeholder="Medium to large volumes")
        
        with col_v2:
            timeline_requirements = st.text_input("⏰ Timeline:", placeholder="Flexible, ongoing partnership")
            quality_requirements = st.text_input("✅ Quality Standards:", placeholder="Premium grade, certified sustainable")
            delay_seconds = st.number_input("⏱️ Delay between emails (seconds):", min_value=1, max_value=10, value=3, help="Recommended: 2-3 seconds to avoid rate limiting")
        
        # Email variables dict
        email_variables = {
            'your_company_name': st.session_state.get('company_name', 'Your Company Name'),
            'sender_name': st.session_state.email_config['sender_name'],
            'your_phone': your_phone or 'Contact for phone number',
            'your_email': st.session_state.email_config['email'],
            'product_requirements': product_requirements or 'High-quality products',
            'volume_requirements': volume_requirements or 'To be discussed',
            'timeline_requirements': timeline_requirements or 'Flexible timeline',
            'quality_requirements': quality_requirements or 'Standard quality'
        }
        
        # Send emails section
        st.markdown("---")
        st.markdown("### 🚀 Send Email Campaign")
        
        col_send1, col_send2, col_send3 = st.columns(3)
        
        with col_send1:
            st.metric("📧 Emails to Send", len(businesses_with_emails))
        
        with col_send2:
            estimated_time = len(businesses_with_emails) * delay_seconds / 60
            st.metric("⏰ Estimated Time", f"{estimated_time:.1f} min")
        
        with col_send3:
            st.metric("📨 Template", selected_template.replace('_', ' ').title())
        
        # Send email campaign button
        if st.button("📧 Send Email Campaign", type="primary", key="send_emails"):
            send_email_campaign(researcher, businesses_with_emails, selected_template, email_variables, delay_seconds)

def send_email_campaign(researcher, businesses_with_emails, template_name, email_variables, delay_seconds):
    """Send the email campaign"""
    
    st.write("### 📧 Sending Email Campaign...")
    
    # Create progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Email sending function
    async def run_email_campaign():
        def progress_callback(current, total):
            progress = current / total
            progress_bar.progress(progress)
        
        def status_callback(status_message):
            status_text.text(status_message)
        
        try:
            # Send emails
            email_result = await researcher.send_curated_emails(
                selected_businesses=businesses_with_emails,
                template_name=template_name,
                email_variables=email_variables,
                delay_seconds=delay_seconds,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            return email_result
            
        except Exception as e:
            st.error(f"Email campaign failed: {str(e)}")
            return None
    
    # Run the email campaign
    try:
        status_text.text("📧 Starting email campaign...")
        progress_bar.progress(5)
        
        # Run async email sending
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        email_result = loop.run_until_complete(run_email_campaign())
        
        if email_result and email_result['success']:
            progress_bar.progress(100)
            status_text.text("✅ Email campaign completed!")
            
            # Show results
            summary = email_result['summary']
            
            st.success(f"🎉 Email campaign completed successfully!")
            
            # Results metrics
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("📧 Sent", summary['emails_sent'])
            with col_r2:
                st.metric("❌ Failed", summary['emails_failed'])
            with col_r3:
                st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
            with col_r4:
                st.metric("⏰ Total Time", f"{summary['emails_sent'] * delay_seconds / 60:.1f} min")
            
            # Save email log
            if st.button("📁 Download Email Log", key="download_email_log"):
                log_filename = researcher.save_email_log()
                st.success(f"Email log saved: {log_filename}")
        
        else:
            st.error("Email campaign failed. Please check your configuration and try again.")
            progress_bar.progress(0)
            status_text.text("❌ Email campaign failed")
    
    except Exception as e:
        st.error(f"Email campaign error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Email campaign failed")
