"""
Email Integration Usage Examples
Example usage of the integrated email functionality in the Business Researcher module
"""

import asyncio
import pandas as pd
from modules.streamlit_business_researcher import (
    research_businesses_from_dataframe, 
    send_curated_business_emails
)

async def example_email_integration():
    """
    Complete example of business research followed by email outreach
    """
    
    # Step 1: Research businesses from your CSV data
    print("Step 1: Researching businesses...")
    
    # Load your CSV file
    df = pd.read_csv('your_business_data.csv')
    
    # Research businesses (this will also return the researcher instance)
    results_df, summary, csv_filename, researcher = await research_businesses_from_dataframe(
        df=df,
        consignee_column='Consignee Name',  # Your business name column
        max_businesses=20  # Limit for testing
    )
    
    print(f"Research completed! Found {summary['successful']} businesses")
    
    # Step 2: Check which businesses have email addresses
    print("\nStep 2: Checking businesses with emails...")
    
    businesses_with_emails = researcher.get_businesses_with_emails()
    print(f"Found {len(businesses_with_emails)} businesses with email addresses")
    
    if len(businesses_with_emails) == 0:
        print("No businesses with email addresses found. Email campaign skipped.")
        return
    
    # Display businesses with emails
    print("\nBusinesses with email addresses:")
    for idx, business in businesses_with_emails.iterrows():
        print(f"- {business['business_name']}: {business['email']}")
    
    # Step 3: Configure email settings
    print("\nStep 3: Configuring email...")
    
    email_config = {
        'provider': 'gmail',  # gmail, outlook, yahoo
        'email': 'your.email@gmail.com',
        'password': 'your_app_password',  # Use App Password for Gmail
        'sender_name': 'Your Name'
    }
    
    # Step 4: Prepare email variables
    email_variables = {
        'your_company_name': 'Your Company Name',
        'sender_name': 'Your Name',
        'your_phone': '+1-234-567-8900',
        'your_email': 'your.email@gmail.com',
        'product_requirements': 'High-quality teak and timber products',
        'volume_requirements': 'Medium to large volumes',
        'timeline_requirements': 'Flexible, ongoing partnership',
        'quality_requirements': 'Premium grade, certified sustainable'
    }
    
    # Step 5: Send emails
    print("\nStep 5: Sending curated emails...")
    
    def progress_callback(current, total):
        print(f"Progress: {current}/{total} emails processed")
    
    def status_callback(status_message):
        print(f"Status: {status_message}")
    
    # Send emails using business introduction template
    email_result = await send_curated_business_emails(
        researcher=researcher,
        selected_businesses=businesses_with_emails,  # or None for all
        email_config=email_config,
        template_name='business_intro',  # 'business_intro', 'supplier_inquiry', 'networking'
        email_variables=email_variables,
        delay_seconds=3.0,  # Delay between emails to avoid rate limiting
        progress_callback=progress_callback,
        status_callback=status_callback
    )
    
    # Step 6: Review results
    print("\nStep 6: Email campaign results...")
    
    if email_result['success']:
        summary = email_result['summary']
        print(f"✅ Email campaign completed successfully!")
        print(f"📧 Total emails sent: {summary['emails_sent']}")
        print(f"❌ Failed emails: {summary['emails_failed']}")
        print(f"📊 Success rate: {summary['success_rate']:.1f}%")
        
        # Save email log
        log_filename = researcher.save_email_log()
        print(f"📁 Email log saved: {log_filename}")
        
        # Get detailed statistics
        stats = researcher.get_email_statistics()
        print(f"\n📈 Detailed Statistics:")
        print(f"Total sent: {stats['total_sent']}")
        print(f"Total failed: {stats['total_failed']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        
    else:
        print(f"❌ Email campaign failed: {email_result['message']}")

def example_selective_email_sending():
    """
    Example of sending emails to selected businesses only
    """
    
    # Assume you already have research results and researcher instance
    # researcher = ... (from previous research)
    
    # Get all businesses with emails
    all_businesses = researcher.get_businesses_with_emails()
    
    # Filter to select only high-confidence businesses
    selected_businesses = all_businesses[
        (all_businesses['confidence'].astype(int) >= 7) &  # High confidence
        (all_businesses['government_verified'] == 'YES')    # Government verified
    ].copy()
    
    print(f"Selected {len(selected_businesses)} high-quality businesses for email outreach")
    
    # Send emails to selected businesses only
    # ... rest of email sending code

def example_email_templates():
    """
    Example of available email templates and customization
    """
    
    # Get available templates
    from modules.business_emailer import BusinessEmailer
    
    emailer = BusinessEmailer()
    templates = emailer.get_default_templates()
    
    print("Available Email Templates:")
    for template_id, template_data in templates.items():
        print(f"\n📧 Template: {template_id}")
        print(f"Name: {template_data['name']}")
        print(f"Subject: {template_data['subject']}")
        print("-" * 50)
    
    # You can customize templates by creating new ones
    emailer.create_template(
        template_name='custom_followup',
        subject='Follow-up: Partnership Discussion - {your_company_name}',
        html_body='''
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Hello {business_name},</h2>
            
            <p>Following up on our previous email regarding potential partnership opportunities.</p>
            
            <p>We're still very interested in exploring how we can work together in the timber industry.</p>
            
            <p>Best regards,<br>
            {sender_name}<br>
            {your_company_name}</p>
        </body>
        </html>
        '''
    )

# Gmail App Password Setup Instructions
GMAIL_SETUP_INSTRUCTIONS = """
📧 Gmail App Password Setup Instructions:

1. Enable 2-Factor Authentication:
   - Go to your Google Account settings
   - Security > 2-Step Verification
   - Turn on 2-Step Verification

2. Generate App Password:
   - Go to Google Account > Security
   - Under "2-Step Verification" click "App passwords"
   - Select "Mail" and your device
   - Google will generate a 16-character password
   - Use this password instead of your regular Gmail password

3. Email Configuration:
   email_config = {
       'provider': 'gmail',
       'email': 'your.email@gmail.com',
       'password': 'your_16_character_app_password',  # NOT your regular password
       'sender_name': 'Your Full Name'
   }

⚠️ Security Notes:
- Never share your app password
- Use environment variables for production
- Consider using .env file for local development
"""

if __name__ == "__main__":
    print("Email Integration Examples")
    print("=" * 50)
    
    print("\n📧 Gmail Setup Instructions:")
    print(GMAIL_SETUP_INSTRUCTIONS)
    
    # Run the complete example
    # asyncio.run(example_email_integration())
