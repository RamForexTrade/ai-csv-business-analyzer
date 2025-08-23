import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio

# Import web scraping module for business research
try:
    from modules.web_scraping_module import perform_web_scraping
except ImportError:
    perform_web_scraping = None

# Import email configuration
try:
    from email_config import EMAIL_CONFIG
except ImportError:
    EMAIL_CONFIG = None

# Import enhanced business researcher with email integration
try:
    from modules.streamlit_business_researcher import research_businesses_from_dataframe, send_curated_business_emails
    business_research_available = True
except ImportError:
    business_research_available = False

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
        
        # Email sending section - Added after business research
        show_email_sending_section()

def show_email_sending_section():
    """Show email sending options after business research with preview functionality"""
    
    # Check if research results exist
    if 'research_completed' in st.session_state and st.session_state.research_completed:
        
        st.markdown("---")
        st.subheader("📧 Send Curated Emails")
        
        # Check if businesses with emails are available
        researcher = st.session_state.get('researcher_instance')
        if researcher:
            businesses_with_emails = researcher.get_businesses_with_emails()
            
            if len(businesses_with_emails) > 0:
                st.success(f"📧 Found {len(businesses_with_emails)} businesses with email addresses!")
                
                # Show email configuration and template selection
                col_e1, col_e2 = st.columns(2)
                
                with col_e1:
                    email_template = st.selectbox(
                        "📝 Email Template:",
                        ["business_intro", "supplier_inquiry", "networking"],
                        format_func=lambda x: {
                            "business_intro": "🤝 Business Introduction",
                            "supplier_inquiry": "📦 Supplier Inquiry", 
                            "networking": "🌐 Industry Networking"
                        }[x]
                    )
                
                with col_e2:
                    delay_seconds = st.number_input(
                        "⏱️ Delay between emails (seconds):",
                        min_value=1, max_value=10, value=3,
                        help="Recommended: 2-3 seconds to avoid spam detection"
                    )
                
                # NEW: Email Preview and Edit Section
                st.markdown("---")
                st.subheader("✉️ Email Preview & Edit")
                st.info("📝 Review and customize your email before sending to all businesses")
                
                # Load default email templates for preview
                if 'email_templates_loaded' not in st.session_state:
                    if researcher.emailer:
                        st.session_state.email_templates_loaded = researcher.emailer.get_default_templates()
                    else:
                        st.session_state.email_templates_loaded = {}
                
                # Get template content
                templates = st.session_state.email_templates_loaded
                selected_template = templates.get(email_template, {})
                
                # Prepare sample variables for preview
                email_variables = {
                    'your_company_name': 'TeakWood Business',
                    'sender_name': EMAIL_CONFIG['sender_name'] if EMAIL_CONFIG else 'Your Name',
                    'your_phone': '+91-9876543210',
                    'your_email': EMAIL_CONFIG['email'] if EMAIL_CONFIG else 'your.email@example.com',
                    'product_requirements': 'High-quality teak and timber products',
                    'volume_requirements': 'Medium to large volumes',
                    'timeline_requirements': 'Flexible, ongoing partnership',
                    'quality_requirements': 'Premium grade, certified sustainable',
                    'business_name': '[Business Name]',
                    'recipient_email': '[Recipient Email]',
                    'business_description': '[Business Description]'
                }
                
                # Email Address Configuration
                st.markdown("### 📮 Email Configuration")
                col_addr1, col_addr2 = st.columns(2)
                
                with col_addr1:
                    from_email = st.text_input(
                        "📤 From Email Address:",
                        value=EMAIL_CONFIG['email'] if EMAIL_CONFIG else '',
                        help="Your email address that will appear as sender"
                    )
                    
                    sender_name = st.text_input(
                        "👤 Sender Name:",
                        value=EMAIL_CONFIG['sender_name'] if EMAIL_CONFIG else '',
                        help="Name that will appear as sender"
                    )
                
                with col_addr2:
                    st.markdown("**📥 To Email Addresses:**")
                    st.info(f"Will send to {len(businesses_with_emails)} businesses with emails")
                    
                    # Show first few email addresses as preview
                    sample_emails = businesses_with_emails['email'].head(3).tolist()
                    for i, email in enumerate(sample_emails, 1):
                        st.text(f"{i}. {email}")
                    if len(businesses_with_emails) > 3:
                        st.text(f"... and {len(businesses_with_emails) - 3} more")
                
                # Email Content Preview and Editing
                st.markdown("### 📝 Email Content")
                
                # Subject Line
                original_subject = selected_template.get('subject', 'Subject not found').format(**email_variables)
                edited_subject = st.text_input(
                    "📋 Email Subject:",
                    value=original_subject,
                    help="Edit the email subject line"
                )
                
                # Email Body Content
                original_html_body = selected_template.get('html_body', 'Template not found')
                
                # Convert HTML template to a more readable format for editing
                try:
                    formatted_body = original_html_body.format(**email_variables)
                    # Simple HTML to text conversion for editing
                    import re
                    # Remove HTML tags for editing interface
                    text_body_for_edit = re.sub('<[^<]+?>', '', formatted_body)
                    text_body_for_edit = re.sub(r'\n\s*\n', '\n\n', text_body_for_edit)  # Clean up extra newlines
                    text_body_for_edit = text_body_for_edit.strip()
                except:
                    text_body_for_edit = "Error loading template content"
                
                edited_body = st.text_area(
                    "📄 Email Content:",
                    value=text_body_for_edit,
                    height=300,
                    help="Edit the email content. HTML formatting will be preserved when sending."
                )
                
                # Email Variables Section
                with st.expander("🔧 Email Variables (Advanced)"):
                    st.markdown("**Customize the variables used in your emails:**")
                    
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        your_company = st.text_input("Your Company:", value=email_variables['your_company_name'])
                        your_phone = st.text_input("Your Phone:", value=email_variables['your_phone'])
                        product_req = st.text_area("Product Requirements:", value=email_variables['product_requirements'], height=80)
                    
                    with col_v2:
                        volume_req = st.text_input("Volume Requirements:", value=email_variables['volume_requirements'])
                        timeline_req = st.text_input("Timeline:", value=email_variables['timeline_requirements'])
                        quality_req = st.text_input("Quality Standards:", value=email_variables['quality_requirements'])
                    
                    # Update email variables if changed
                    email_variables.update({
                        'your_company_name': your_company,
                        'your_phone': your_phone,
                        'product_requirements': product_req,
                        'volume_requirements': volume_req,
                        'timeline_requirements': timeline_req,
                        'quality_requirements': quality_req,
                        'sender_name': sender_name,
                        'your_email': from_email
                    })
                
                # Email Preview
                st.markdown("### 👀 Final Email Preview")
                with st.expander("📧 Click to Preview Final Email", expanded=False):
                    st.markdown("**Subject:** " + edited_subject)
                    st.markdown("**From:** " + f"{sender_name} <{from_email}>")
                    st.markdown("**To:** [Individual business emails]")
                    st.markdown("---")
                    st.markdown("**Content:**")
                    st.text_area("", value=edited_body, height=200, disabled=True)
                
                # Send Email Buttons
                st.markdown("---")
                st.markdown("### 🚀 Send Emails")
                
                col_send1, col_send2, col_send3 = st.columns([2, 1, 1])
                
                with col_send1:
                    send_emails_button = st.button(
                        "📧 Send Emails to All Businesses", 
                        type="primary",
                        help=f"Send customized email to {len(businesses_with_emails)} businesses"
                    )
                
                with col_send2:
                    st.metric("📧 Ready to Send", len(businesses_with_emails))
                
                with col_send3:
                    if st.button("📝 Reset to Template"):
                        st.rerun()
                
                # Process email sending with custom content
                if send_emails_button:
                    if not from_email or not sender_name:
                        st.error("❌ Please provide both sender email and name")
                    elif EMAIL_CONFIG:
                        send_customized_emails_to_businesses(
                            researcher, 
                            businesses_with_emails, 
                            email_template,
                            edited_subject,
                            edited_body,
                            email_variables,
                            from_email,
                            sender_name,
                            delay_seconds
                        )
                    else:
                        st.error("❌ Email configuration not found. Please check email_config.py")
                
                # Show preview of businesses with emails
                with st.expander("👀 Preview Businesses with Emails"):
                    preview_df = businesses_with_emails[['business_name', 'email', 'phone', 'website']].head(10)
                    st.dataframe(preview_df, use_container_width=True)
                    if len(businesses_with_emails) > 10:
                        st.caption(f"Showing first 10 of {len(businesses_with_emails)} businesses")
            
            else:
                st.warning("📧 No email addresses found in research results.")
                st.info("💡 Try researching more businesses to find email contacts.")
        
        else:
            st.info("🔍 Complete business research first to send emails.")
    
    else:
        st.info("🔍 Complete business research first to see email sending options.")

def send_customized_emails_to_businesses(researcher, businesses_with_emails, template_name, 
                                       custom_subject, custom_body, email_variables,
                                       from_email, sender_name, delay_seconds):
    """Send emails to businesses with customized content and progress tracking"""
    
    if not EMAIL_CONFIG:
        st.error("❌ Email configuration not available")
        return
    
    st.write("### 📧 Sending Email Campaign...")
    
    # Configure email with provided settings
    success, message = researcher.configure_email(
        email_provider=EMAIL_CONFIG['provider'],
        email_address=from_email,
        email_password=EMAIL_CONFIG['password'],  # Keep original password
        sender_name=sender_name
    )
    
    if not success:
        st.error(f"❌ Email configuration failed: {message}")
        return
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Create custom email template with user's content
    researcher.emailer.create_template(
        template_name=f"custom_{template_name}",
        subject=custom_subject,
        html_body=convert_text_to_html(custom_body),  # Convert edited text back to HTML
        text_body=custom_body
    )
    
    # Send emails asynchronously with custom content
    async def run_custom_email_campaign():
        def progress_callback(current, total):
            progress = current / total
            progress_bar.progress(progress)
        
        def status_callback(status_message):
            status_text.text(status_message)
        
        try:
            # Use the custom template
            email_result = await researcher.send_curated_emails(
                selected_businesses=businesses_with_emails,
                template_name=f"custom_{template_name}",
                email_variables=email_variables,
                delay_seconds=delay_seconds,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            return email_result
        except Exception as e:
            st.error(f"❌ Email sending failed: {str(e)}")
            return None
    
    # Run email campaign
    try:
        status_text.text("📧 Starting email campaign...")
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Send emails
        email_result = loop.run_until_complete(run_custom_email_campaign())
        
        if email_result and email_result['success']:
            progress_bar.progress(1.0)
            status_text.text("✅ Email campaign completed!")
            
            # Show results
            summary = email_result['summary']
            st.success(f"🎉 Email campaign completed!")
            
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("📧 Sent", summary['emails_sent'])
            with col_r2:
                st.metric("❌ Failed", summary['emails_failed'])
            with col_r3:
                st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
            
            # Show sent email details
            with st.expander("📋 Email Campaign Details"):
                st.markdown(f"**Subject Used:** {custom_subject}")
                st.markdown(f"**From:** {sender_name} <{from_email}>")
                st.markdown(f"**Total Businesses:** {len(businesses_with_emails)}")
                st.markdown(f"**Delay Between Emails:** {delay_seconds} seconds")
            
            # Email log download
            if st.button("📁 Download Email Log"):
                log_filename = researcher.save_email_log()
                st.success(f"📁 Email log saved: {log_filename}")
        
        else:
            st.error("❌ Email campaign failed")
            
    except Exception as e:
        st.error(f"❌ Email campaign error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Failed")

def convert_text_to_html(text_content):
    """Convert plain text to simple HTML format for email sending"""
    
    # Simple text to HTML conversion
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {text_content.replace(chr(10), '<br>')}
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_emails_to_businesses(researcher, businesses_with_emails, template_name, delay_seconds):
    """Original send emails function - kept for compatibility"""
    
    if not EMAIL_CONFIG:
        st.error("❌ Email configuration not available")
        return
    
    st.write("### 📧 Sending Email Campaign...")
    
    # Configure email with stored settings
    success, message = researcher.configure_email(
        email_provider=EMAIL_CONFIG['provider'],
        email_address=EMAIL_CONFIG['email'],
        email_password=EMAIL_CONFIG['password'],
        sender_name=EMAIL_CONFIG['sender_name']
    )
    
    if not success:
        st.error(f"❌ Email configuration failed: {message}")
        return
    
    # Prepare email variables
    email_variables = {
        'your_company_name': 'TeakWood Business',
        'sender_name': EMAIL_CONFIG['sender_name'],
        'your_phone': '+91-9876543210',
        'your_email': EMAIL_CONFIG['email'],
        'product_requirements': 'High-quality teak and timber products',
        'volume_requirements': 'Medium to large volumes',
        'timeline_requirements': 'Flexible, ongoing partnership',
        'quality_requirements': 'Premium grade, certified sustainable'
    }
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Send emails asynchronously
    async def run_email_campaign():
        def progress_callback(current, total):
            progress = current / total
            progress_bar.progress(progress)
        
        def status_callback(status_message):
            status_text.text(status_message)
        
        try:
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
            st.error(f"❌ Email sending failed: {str(e)}")
            return None
    
    # Run email campaign
    try:
        status_text.text("📧 Starting email campaign...")
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Send emails
        email_result = loop.run_until_complete(run_email_campaign())
        
        if email_result and email_result['success']:
            progress_bar.progress(100)
            status_text.text("✅ Email campaign completed!")
            
            # Show results
            summary = email_result['summary']
            st.success(f"🎉 Email campaign completed!")
            
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("📧 Sent", summary['emails_sent'])
            with col_r2:
                st.metric("❌ Failed", summary['emails_failed'])
            with col_r3:
                st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
            
            # Email log download
            if st.button("📁 Download Email Log"):
                log_filename = researcher.save_email_log()
                st.success(f"📁 Email log saved: {log_filename}")
        
        else:
            st.error("❌ Email campaign failed")
            
    except Exception as e:
        st.error(f"❌ Email campaign error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Failed")
