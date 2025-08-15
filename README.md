# 🤖 AI-Powered CSV Business Analyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

A comprehensive Streamlit application that combines AI-powered data analysis with business contact research and automated email outreach capabilities. Upload any CSV or Excel file and instantly start analyzing data, chatting with your dataset, finding business contact information, and sending curated emails to prospects.

## 🚀 Features

### 📊 **Smart Data Analysis**
- **Intelligent Data Loading**: Automatically detects and properly handles identifier columns (HS codes, product codes, etc.)
- **Excel & CSV Support**: Upload any Excel (.xlsx, .xls) or CSV file with automatic sheet selection
- **Smart Column Detection**: Distinguishes between numeric data and identifier codes for accurate analysis

### 🤖 **AI-Powered Chat Interface**
- **Natural Language Queries**: Ask questions about your data in plain English
- **Powered by Groq Llama**: Fast, cost-effective AI responses using Llama-3.3-70b-versatile
- **DataFrame Agent**: Built-in Excel-like operations via natural language
  - "filter where Country = US and Amount > 1000"
  - "group by Category and sum Amount"
  - "show me top 10 by Revenue"

### 🔍 **Business Contact Research**
- **AI-Powered Web Scraping**: Find contact information for businesses in your data
- **Comprehensive Data Extraction**:
  - 📞 Phone numbers
  - 📧 Email addresses
  - 🌐 Website URLs
  - 📍 Business addresses
  - 📋 Company descriptions
  - 🏛️ Government verification
  - 📄 Registration numbers
- **Multi-Source Research**: Government databases, industry associations, and general web sources
- **Integrated Workflow**: Research contacts directly from filtered data in Data Explorer

### 📧 **Automated Email Outreach**
- **Curated Email Campaigns**: Send personalized emails to businesses with found email addresses
- **Multiple Email Providers**: 
  - 📧 Gmail SMTP support (with App Password)
  - 📨 Outlook/Hotmail SMTP
  - 🟡 Yahoo Mail SMTP
  - 🚀 SendGrid API
  - 📮 Mailgun API
- **Professional Templates**:
  - Business Introduction
  - Supplier Inquiry
  - Industry Networking
  - Custom templates support
- **Smart Email Features**:
  - Personalized variables (business name, address, etc.)
  - Rate limiting to avoid spam detection
  - Email delivery tracking
  - Success/failure reporting
  - Email logs with timestamps

### 📈 **Advanced Visualizations**
- **Quick Visualizations**: Generate charts and graphs instantly
- **Correlation Analysis**: Automatic correlation matrices for numeric data
- **Distribution Analysis**: Histograms and value distribution charts
- **Interactive Plotly Charts**: Zoom, filter, and explore your data visually

### 🎛️ **Data Explorer**
- **Advanced Filtering**: Primary and secondary filters with search functionality
- **Real-time Metrics**: Records count, percentage of total, data quality indicators
- **Export Capabilities**: Download filtered data as CSV
- **Research Integration**: Launch business research directly from filtered results

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### 1. Clone the Repository
```bash
git clone https://github.com/RamForexTrade/ai-csv-business-analyzer.git
cd ai-csv-business-analyzer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
# Required for AI chat and business research features
```

### 4. Configure API Keys
Edit the `.env` file with your actual API keys:

```env
# AI Chat Provider (Required)
GROQ_API_KEY=gsk_your_actual_groq_key_here

# Business Research API (Required for web scraping)
TAVILY_API_KEY=tvly-your_actual_tavily_key_here
```

#### Getting API Keys:
- **Groq API**: [Get your free API key](https://console.groq.com/keys)
  - Fast Llama model inference
  - Cost-effective for high-volume usage
  - Free tier available

- **Tavily API**: [Sign up for Tavily](https://tavily.com)
  - Advanced web search for business research
  - Free tier with monthly credits
  - High-quality business data extraction

## 🚀 Usage

### Running Locally
```bash
streamlit run ai_csv_analyzer.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Application

#### 1. **Upload Your Data**
- Click "Choose a CSV or Excel file" in the sidebar
- Select your data file (supports .csv, .xlsx, .xls)
- For Excel files, choose the specific worksheet to analyze

#### 2. **Explore Your Data**
Navigate through the tabs:

**🤖 AI Chat**
- Ask natural language questions about your data
- Get instant insights and analysis
- Use the suggested questions or create your own

**📊 Data Overview**
- View dataset statistics and metrics
- See data types and missing value analysis
- Understand identifier vs. numeric columns

**📈 Quick Viz**
- Generate instant visualizations
- Create correlation matrices
- Analyze distributions and patterns

**📊 Data Explorer**
- Apply advanced filters to your data
- Use primary and secondary filtering
- Export filtered results
- **🔍 Business Research**: Click to find contact information for businesses in filtered data

#### 3. **Business Contact Research**
- Filter your data to specific businesses of interest
- Click "🔍 Business Research" in the Data Explorer
- Select the column containing business names
- Choose research range (1-20 businesses recommended)
- Review API cost estimates
- Start research and download results

#### 4. **📧 Email Outreach Campaign**
After business research is complete:

**Setup Email Configuration**
```python
# Example email setup (Gmail)
email_config = {
    'provider': 'gmail',
    'email': 'your.email@gmail.com',
    'password': 'your_app_password',  # Use App Password for Gmail
    'sender_name': 'Your Full Name'
}
```

**Send Curated Emails**
- Filter businesses with email addresses
- Choose from professional email templates
- Customize email variables (company name, requirements, etc.)
- Send personalized emails with rate limiting
- Track success/failure rates
- Download email campaign logs

### 📧 Gmail App Password Setup

For Gmail SMTP, you need to use an App Password:

1. **Enable 2-Factor Authentication**:
   - Go to your Google Account settings
   - Security > 2-Step Verification
   - Turn on 2-Step Verification

2. **Generate App Password**:
   - Go to Google Account > Security
   - Under "2-Step Verification" click "App passwords"
   - Select "Mail" and your device
   - Google will generate a 16-character password
   - Use this password instead of your regular Gmail password

### Example Use Cases

**📈 Sales Data Analysis**
```
"What are the top 10 customers by revenue?"
"Show me sales trends by month"
"Filter where Region = 'North' and Amount > 50000"
```

**🌍 Trade Data Analysis**
```
"What are the most common HS codes?"
"Group by Country and sum Quantity"
"Show me importers from India"
```

**🏢 Business Research & Outreach**
```
Filter by: Country = "USA", Industry = "Technology"
Research: Find contact details for filtered companies
Email: Send supplier inquiry to businesses with emails
Export: Download business contacts and email logs
```

## 📁 Project Structure

```
ai-csv-business-analyzer/
├── ai_csv_analyzer.py          # Main Streamlit application
├── data_explorer_new.py        # Data Explorer with filtering and research
├── email_integration_examples.py  # Email integration usage examples
├── modules/
│   ├── __init__.py
│   ├── streamlit_business_researcher.py  # Business research with email integration
│   ├── business_emailer.py              # Email sending module
│   └── web_scraping_module.py           # Web scraping interface
├── .streamlit/
│   ├── config.toml             # Streamlit configuration
│   └── secrets.toml.example    # Secrets template
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── Procfile                   # Deployment configuration
└── README.md                  # This file
```

## 🔧 Configuration

### Streamlit Configuration
The app includes optimized Streamlit settings in `.streamlit/config.toml`:
- Maximum upload size: 200MB
- Optimized performance settings
- Custom theme matching the app design

### Environment Variables
All sensitive configuration is managed through environment variables:
- `GROQ_API_KEY`: Required for AI chat functionality
- `TAVILY_API_KEY`: Required for business research

### Email Configuration
Supports multiple email providers:

```python
# Gmail (recommended)
email_config = {
    'provider': 'gmail',
    'smtp_server': 'smtp.gmail.com',
    'port': 587
}

# Outlook
email_config = {
    'provider': 'outlook',
    'smtp_server': 'smtp-mail.outlook.com',
    'port': 587
}

# SendGrid API
emailer.configure_sendgrid(
    api_key='your_sendgrid_api_key',
    from_email='noreply@yourdomain.com'
)
```

## 🚦 Deployment

### Streamlit Cloud
1. Fork this repository
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your API keys in Streamlit Cloud secrets
4. Deploy with one click

### Heroku
```bash
# The included Procfile supports Heroku deployment
git push heroku main
```

### Docker
```dockerfile
# Example Dockerfile for containerized deployment
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "ai_csv_analyzer.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📊 API Usage & Costs

### Estimated Costs (Per Business)
- **Business Research**: ~$0.03 per business
  - Groq API: ~$0.01 (Llama-3.3-70b-versatile)
  - Tavily API: ~$0.02 (web search + extraction)
- **Email Sending**: Free with SMTP providers
  - Gmail/Outlook: Free with your existing account
  - SendGrid: 100 emails/day free tier
  - Mailgun: 1000 emails/month free tier

### Rate Limits
- Groq: 30 requests/minute (free tier)
- Tavily: 1000 searches/month (free tier)
- Gmail SMTP: ~500 emails/day (with App Password)
- Outlook SMTP: ~300 emails/day

## 📧 Email Templates

### Built-in Templates

1. **Business Introduction**
   - Professional introduction email
   - Partnership opportunity focus
   - Contact information request

2. **Supplier Inquiry**
   - Product requirements specification
   - Volume and timeline details
   - Pricing and catalog request

3. **Industry Networking**
   - Professional networking approach
   - Collaboration opportunities
   - Knowledge sharing focus

### Custom Template Example
```python
emailer.create_template(
    template_name='follow_up',
    subject='Follow-up: Partnership Discussion - {your_company_name}',
    html_body='''
    <html>
    <body>
        <h2>Hello {business_name},</h2>
        <p>Following up on our previous email...</p>
        <p>Best regards,<br>{sender_name}</p>
    </body>
    </html>
    '''
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**"API key not found"**
- Ensure your `.env` file exists and contains valid API keys
- Restart the application after adding API keys

**"Business research not working"**
- Check that both GROQ_API_KEY and TAVILY_API_KEY are configured
- Verify API key validity at respective provider consoles

**"Email sending failed"**
- For Gmail: Ensure 2FA is enabled and you're using App Password
- Check email provider settings and credentials
- Verify rate limits haven't been exceeded

**"File upload errors"**
- Maximum file size is 200MB
- Supported formats: .csv, .xlsx, .xls
- Ensure file is not corrupted

### Get Help
- 📧 Create an issue in this repository
- 💬 Join our discussions for questions and feature requests
- 📖 Check the documentation in this README
- 🔍 Review `email_integration_examples.py` for email usage examples

## 🏆 Acknowledgments

- **Streamlit**: For the amazing web app framework
- **Groq**: For fast and cost-effective AI inference
- **Tavily**: For powerful web search capabilities
- **Plotly**: For interactive visualizations
- **Pandas**: For robust data manipulation

---

**Built with ❤️ using Streamlit, Groq AI, modern web scraping, and email automation technologies.**

## 🎯 Quick Start Examples

### Sample Questions to Try:
- "What's the overview of this dataset?"
- "Show me the top 10 values by count"
- "Filter where Country contains 'India'"
- "Group by Category and sum Amount"
- "What are the correlations between numeric columns?"

### Complete Workflow Examples:

#### 🏢 **B2B Lead Generation**
1. Upload customer/prospect data
2. Filter by industry, region, company size
3. Research contact details (phone, email, website)
4. Send personalized business introduction emails
5. Track email delivery and responses

#### 🌍 **Export/Import Outreach**
1. Upload trade data (HS codes, countries, companies)
2. Filter by product categories and countries
3. Research importer/exporter contact information
4. Send supplier inquiry emails with product requirements
5. Download contact database and email logs

#### 🤝 **Partnership Development**
1. Upload industry database
2. Filter potential partners by criteria
3. Research company details and decision makers
4. Send networking emails for collaboration
5. Manage outreach campaign with tracking

---

⭐ **Star this repository if you find it useful!**

🔗 **Repository**: https://github.com/RamForexTrade/ai-csv-business-analyzer
