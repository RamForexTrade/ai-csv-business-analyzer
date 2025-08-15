# 🤖 AI-Powered CSV Business Analyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

A comprehensive Streamlit application that combines AI-powered data analysis with business contact research capabilities. Upload any CSV or Excel file and instantly start analyzing data, chatting with your dataset, and finding business contact information using advanced web scraping.

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
- **Integrated Workflow**: Research contacts directly from filtered data in Data Explorer

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

**🏢 Business Research**
```
Filter by: Country = "USA", Industry = "Technology"
Research: Find contact details for filtered companies
Export: Download business contacts as CSV
```

## 📁 Project Structure

```
ai-csv-business-analyzer/
├── ai_csv_analyzer.py          # Main Streamlit application
├── data_explorer_new.py        # Data Explorer with filtering and research
├── modules/
│   ├── __init__.py
│   ├── streamlit_business_researcher.py  # Business research logic
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

### Estimated Costs (Per Business Research)
- **Groq API**: ~$0.01 per business (Llama-3.3-70b-versatile)
- **Tavily API**: ~$0.02 per business (web search + extraction)
- **Total**: ~$0.03 per business researched

### Rate Limits
- Groq: 30 requests/minute (free tier)
- Tavily: 1000 searches/month (free tier)

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

**"File upload errors"**
- Maximum file size is 200MB
- Supported formats: .csv, .xlsx, .xls
- Ensure file is not corrupted

### Get Help
- 📧 Create an issue in this repository
- 💬 Join our discussions for questions and feature requests
- 📖 Check the documentation in this README

## 🏆 Acknowledgments

- **Streamlit**: For the amazing web app framework
- **Groq**: For fast and cost-effective AI inference
- **Tavily**: For powerful web search capabilities
- **Plotly**: For interactive visualizations
- **Pandas**: For robust data manipulation

---

**Built with ❤️ using Streamlit, Groq AI, and modern web scraping technologies.**

## 🎯 Quick Start Examples

### Sample Questions to Try:
- "What's the overview of this dataset?"
- "Show me the top 10 values by count"
- "Filter where Country contains 'India'"
- "Group by Category and sum Amount"
- "What are the correlations between numeric columns?"

### Business Research Examples:
1. **Trade Data**: Research importers/exporters for contact details
2. **Customer Lists**: Find phone and email for sales outreach
3. **Supplier Data**: Get business addresses and websites
4. **Lead Generation**: Extract contact info from prospect lists

---

⭐ **Star this repository if you find it useful!**

🔗 **Repository**: https://github.com/RamForexTrade/ai-csv-business-analyzer