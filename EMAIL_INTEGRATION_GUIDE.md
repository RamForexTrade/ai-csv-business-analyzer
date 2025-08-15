# 📧 Email Integration Quick Start Guide

## 🚀 How to Use the Email Feature After Business Research

### Step-by-Step Process

#### 1. **Filter Your Data**
- Go to the **📊 Data Explorer** tab
- Use Primary and Secondary filters to narrow down to your target businesses
- Example: Filter by Country = "USA", Industry = "Timber"

#### 2. **Start Business Research**
- Click the **🔍 Business Research** button
- Select the column containing business names (e.g., "Consignee Name")
- Choose how many businesses to research (recommended: 5-15)
- Click **🚀 Start Business Research**

#### 3. **Wait for Research to Complete**
- The system will search government databases, industry sources, and the web
- Research typically takes 45-60 seconds per business
- You'll see progress updates and real-time results

#### 4. **Configure Email Settings** (One-time setup)
- After research completes, expand **⚙️ Email Configuration**
- Choose your email provider (Gmail recommended)
- Enter your email address and App Password (see Gmail setup below)
- Enter your name and company name
- Click **🧪 Test Email Configuration**

#### 5. **Customize Email Content**
- Choose an email template:
  - **🤝 Business Introduction** - Professional partnership introduction
  - **📦 Supplier Inquiry** - Product requirements and pricing requests
  - **🌐 Industry Networking** - Professional networking outreach
- Fill in your business details (phone, requirements, etc.)

#### 6. **Send Email Campaign**
- Review the businesses that will receive emails
- Set delay between emails (recommended: 2-3 seconds)
- Click **📧 Send Email Campaign**
- Monitor progress and success rate

---

## 📧 Gmail App Password Setup

### Quick Setup (5 minutes):

1. **Enable 2-Factor Authentication**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Turn on **2-Step Verification** if not already enabled

2. **Generate App Password**:
   - Go to **Security** > **2-Step Verification** > **App passwords**
   - Select **Mail** and your device
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Use in Email Configuration**:
   ```
   Email Provider: Gmail
   Email Address: your.email@gmail.com
   Password: abcd efgh ijkl mnop  (16-character App Password)
   Your Name: John Smith
   Company: Your Company Name
   ```

---

## 📋 Complete Workflow Example

### Scenario: Timber Business Outreach

1. **Upload Your Data**: CSV with company names, countries, products
2. **Filter**: Country = "India", Product contains "wood"
3. **Research**: Find 10 businesses → Research finds emails for 6 businesses
4. **Email Setup**: Configure Gmail with App Password
5. **Campaign**: Send "Supplier Inquiry" emails to 6 businesses
6. **Results**: 5 emails sent successfully, 1 failed (invalid email)

---

## ⚙️ Email Configuration Options

### Where to Configure Email Settings:

**In the Streamlit App:**
- After business research completes
- Look for **⚙️ Email Configuration** section
- Fill in the form and test configuration

**For Developers (Programmatic):**
```python
# In your Python code
email_config = {
    'provider': 'gmail',
    'email': 'your.email@gmail.com',
    'password': 'your_16_character_app_password',
    'sender_name': 'Your Full Name'
}

# This configuration is handled automatically in the UI
```

---

## 🔧 Troubleshooting

### Common Issues:

**"Email configuration failed"**
- ✅ Make sure you're using App Password (not regular password) for Gmail
- ✅ Check that 2FA is enabled in your Google Account
- ✅ Verify email address is correct

**"No businesses with email addresses found"**
- ℹ️ This is normal - not all businesses have publicly available emails
- ℹ️ Try researching more businesses to increase chances
- ℹ️ Research typically finds emails for 30-60% of businesses

**"Email sending failed"**
- ✅ Check your internet connection
- ✅ Verify email configuration is still valid
- ✅ Make sure you haven't exceeded daily sending limits

**"Research failed"**
- ✅ Check that GROQ_API_KEY and TAVILY_API_KEY are configured
- ✅ Verify API keys are valid and have sufficient credits

---

## 📊 What Gets Extracted

### Business Research Finds:
- 📞 **Phone numbers** (business contact numbers)
- 📧 **Email addresses** (business email contacts)
- 🌐 **Website URLs** (official company websites)
- 📍 **Addresses** (business locations)
- 🏛️ **Government verification** (official registration status)
- 📄 **Registration numbers** (company/GST registration)
- 📋 **Business descriptions** (company activities and focus)

### Email Campaign Provides:
- ✅ **Delivery tracking** (sent/failed counts)
- 📊 **Success rates** (percentage delivered)
- ⏰ **Campaign timing** (progress and completion time)
- 📁 **Detailed logs** (downloadable email campaign log)

---

## 💡 Best Practices

### For Better Results:
1. **Filter your data first** - Target specific industries/regions
2. **Research 5-15 businesses at a time** - Optimal balance of cost and results
3. **Use professional email templates** - Higher response rates
4. **Personalize email variables** - Include specific product requirements
5. **Add delays between emails** - Avoid being flagged as spam (2-3 seconds)
6. **Test email configuration first** - Ensure emails will send successfully

### Email Template Tips:
- **Business Introduction**: Great for general partnership outreach
- **Supplier Inquiry**: Best for specific product sourcing
- **Industry Networking**: Ideal for relationship building

---

## 🎯 Success Metrics

### Typical Results:
- **Research Success**: 70-90% of businesses get researched successfully
- **Email Discovery**: 30-60% of businesses have findable email addresses
- **Email Delivery**: 85-95% of found emails get delivered successfully
- **Cost per Business**: ~$0.03 for research + free email sending

---

**Need Help?** Check the troubleshooting section above or create an issue in the GitHub repository.
