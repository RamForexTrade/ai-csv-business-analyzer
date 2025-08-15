"""
Basic Streamlit Business Researcher - Enhanced features removed
Simple web scraping for basic business contact information
"""

import asyncio
import csv
import os
import json
import tempfile
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

class StreamlitBusinessResearcher:
    def __init__(self):
        # Load API keys
        self.tavily_key = os.getenv('TAVILY_API_KEY')
        self.groq_key = os.getenv('GROQ_API_KEY')
        
        # Validate required keys
        if not self.tavily_key:
            raise ValueError("TAVILY_API_KEY not found in .env file!")
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not found in .env file!")
        
        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=self.tavily_key)
        
        self.results = []
    
    def test_apis(self):
        """Test all APIs before starting research"""
        print("🧪 Testing APIs...")
        
        # Test Groq
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "Say 'Groq working'"}],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    print("✅ Groq API: Working")
                else:
                    return False, "Groq API: Empty response"
            else:
                error_msg = f"Groq API: HTTP {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                error_msg = f"Groq API: Billing/Quota Issue - {e}"
                print(f"💳 {error_msg}")
                return False, error_msg
            else:
                error_msg = f"Groq API: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        # Test Tavily
        try:
            response = self.tavily_client.search("test query", max_results=1)
            if response.get('results'):
                print("✅ Tavily API: Working")
            else:
                return False, "Tavily API: No results"
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str or "limit" in error_str:
                error_msg = f"Tavily API: Billing/Quota Issue - {e}"
                print(f"💳 {error_msg}")
                return False, error_msg
            else:
                error_msg = f"Tavily API: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        return True, "All APIs working"
    
    async def research_business_direct(self, business_name):
        """Research business using Tavily + Groq directly"""
        
        print(f"🔍 Researching: {business_name}")
        
        try:
            # Step 1: Search with Tavily
            search_results = self.search_with_tavily(business_name)
            
            if not search_results:
                print(f"❌ No search results found for {business_name}")
                return self.create_manual_fallback(business_name)
            
            # Step 2: Extract contact info using Groq AI
            contact_info = await self.extract_contacts_with_groq(business_name, search_results)
            
            return contact_info
            
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                print(f"💳 API Billing Error for {business_name}: {e}")
                return self.create_billing_error_result(business_name)
            else:
                print(f"❌ Error researching {business_name}: {e}")
                return self.create_manual_fallback(business_name)
    
    def search_with_tavily(self, business_name):
        """Search for business information using Tavily API"""
        
        print(f"   🌐 Searching Tavily for: {business_name}")
        
        try:
            # Multiple search queries for better coverage
            search_queries = [
                f"{business_name} contact information phone email",
                f"{business_name} business address",
                f"{business_name} company website official"
            ]
            
            all_results = []
            
            for query in search_queries:
                print(f"      📝 Query: {query}")
                
                response = self.tavily_client.search(
                    query=query,
                    max_results=3,
                    search_depth="advanced",
                    include_domains=None,
                    exclude_domains=["facebook.com", "twitter.com", "instagram.com"]
                )
                
                if response.get('results'):
                    all_results.extend(response['results'])
                    print(f"      ✅ Found {len(response['results'])} results")
                else:
                    print(f"      ❌ No results for this query")
            
            print(f"   📊 Total search results: {len(all_results)}")
            return all_results
            
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str or "limit" in error_str:
                print(f"💳 Tavily Billing Error: {e}")
                raise Exception(f"Tavily API billing issue: {e}")
            else:
                print(f"   ❌ Tavily search error: {e}")
                return []
    
    def format_search_results(self, search_results):
        """Format Tavily search results for Groq analysis"""
        
        formatted_results = []
        
        for i, result in enumerate(search_results[:10], 1):
            formatted_result = f"""
            RESULT {i}:
            Title: {result.get('title', 'No title')}
            URL: {result.get('url', 'No URL')}
            Content: {result.get('content', 'No content')[:500]}...
            """
            formatted_results.append(formatted_result)
        
        return '\n'.join(formatted_results)
    
    async def extract_contacts_with_groq(self, business_name, search_results):
        """Use Groq (Llama) to extract contact information"""
        
        print(f"   🦙 Analyzing results with Groq (Llama)...")
        
        # Prepare search results text for Groq
        results_text = self.format_search_results(search_results)
        
        prompt = f"""
Analyze the following web search results for the business "{business_name}" and extract contact information.

SEARCH RESULTS:
{results_text}

Please extract and format the following information:

BUSINESS_NAME: {business_name}
PHONE: [extract phone number if found, or "Not found"]
EMAIL: [extract email address if found, or "Not found"]  
WEBSITE: [extract official website URL if found, or "Not found"]
ADDRESS: [extract business address if found, or "Not found"]
DESCRIPTION: [brief description of business based on search results, or "No description available"]
CONFIDENCE: [rate 1-10 how confident you are this is the correct business]

Rules:
1. Only extract information that is clearly present in the search results
2. Don't make up or assume any contact details
3. Prefer official websites over directory listings
4. If multiple phone numbers found, choose the main business number
5. If no specific info found, write "Not found" for that field

Format your response exactly as shown above with the field names.
        """
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    extracted_info = result['choices'][0]['message']['content']
                    print(f"   ✅ Groq extraction completed")
                    
                    result_data = {
                        'business_name': business_name,
                        'extracted_info': extracted_info,
                        'raw_search_results': search_results,
                        'research_date': datetime.now().isoformat(),
                        'method': 'Tavily + Groq (Llama)',
                        'status': 'success'
                    }
                    
                    self.results.append(result_data)
                    
                    # Display results
                    print(f"   📋 Results for {business_name}:")
                    print("-" * 50)
                    print(extracted_info)
                    print("-" * 50)
                    
                    return result_data
                else:
                    print(f"   ❌ Groq returned empty response")
                    return self.create_manual_fallback(business_name)
            else:
                print(f"   ❌ Groq API error: HTTP {response.status_code} - {response.text}")
                return self.create_manual_fallback(business_name)
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                print(f"💳 Groq Billing Error: {e}")
                raise Exception(f"Groq API billing issue: {e}")
            else:
                print(f"   ❌ Groq extraction error: {e}")
                return self.create_manual_fallback(business_name)
    
    def create_manual_fallback(self, business_name):
        """Create fallback result when automated research fails"""
        
        fallback_info = f"""
        BUSINESS_NAME: {business_name}
        PHONE: Research required
        EMAIL: Research required
        WEBSITE: Research required  
        ADDRESS: Research required
        DESCRIPTION: Business - requires manual verification
        CONFIDENCE: 1

        MANUAL RESEARCH NEEDED:
        1. Google search: "{business_name}" contact information
        2. Check local business directories and Yellow Pages
        3. Search LinkedIn for company profile
        4. Look for trade association listings
        5. Check government business registration databases
        """
        
        result = {
            'business_name': business_name,
            'extracted_info': fallback_info,
            'raw_search_results': [],
            'research_date': datetime.now().isoformat(),
            'method': 'Manual Fallback',
            'status': 'manual_required'
        }
        
        self.results.append(result)
        
        print(f"   ⚠️  Manual research required for {business_name}")
        
        return result
    
    def create_billing_error_result(self, business_name):
        """Create result for billing error cases"""
        
        billing_info = f"""
        BUSINESS_NAME: {business_name}
        PHONE: API billing error
        EMAIL: API billing error
        WEBSITE: API billing error  
        ADDRESS: API billing error
        DESCRIPTION: Research stopped due to API billing/quota issue
        CONFIDENCE: 0

        BILLING ERROR OCCURRED:
        Research was stopped due to API billing or quota limits.
        Please resolve billing issues and restart the research process.
        """
        
        result = {
            'business_name': business_name,
            'extracted_info': billing_info,
            'raw_search_results': [],
            'research_date': datetime.now().isoformat(),
            'method': 'Billing Error',
            'status': 'billing_error'
        }
        
        self.results.append(result)
        
        print(f"   💳 Billing error occurred for {business_name}")
        
        return result
    
    async def research_from_dataframe(self, df, consignee_column='Consignee Name', max_businesses=None, enable_justdial=False):
        """Research businesses from DataFrame with basic functionality only"""
        
        # Extract business names from the specified column
        if consignee_column not in df.columns:
            available_cols = [col for col in df.columns if 'consignee' in col.lower() or 'name' in col.lower()]
            if available_cols:
                consignee_column = available_cols[0]
                print(f"⚠️  Column '{consignee_column}' not found. Using '{consignee_column}' instead.")
            else:
                raise ValueError(f"Column '{consignee_column}' not found in DataFrame. Available columns: {list(df.columns)}")
        
        # Get unique business names
        business_names = df[consignee_column].dropna().unique().tolist()
        business_names = [name.strip() for name in business_names if name.strip()]
        
        if not business_names:
            raise ValueError(f"No business names found in column '{consignee_column}'")
        
        # Limit number of businesses if specified
        if max_businesses and max_businesses < len(business_names):
            business_names = business_names[:max_businesses]
            print(f"🎯 Limited to first {max_businesses} businesses")
        
        total_businesses = len(business_names)
        print(f"📋 Found {total_businesses} unique businesses to research")
        
        # Research each business (basic functionality only)
        successful = 0
        manual_required = 0
        billing_errors = 0
        
        for i, business_name in enumerate(business_names, 1):
            print(f"\n📊 Progress: {i}/{total_businesses}")
            print(f"🏢 Business: {business_name}")
            
            try:
                # Basic research only
                result = await self.research_business_direct(business_name)
                
                if result['status'] == 'success':
                    successful += 1
                elif result['status'] == 'manual_required':
                    manual_required += 1
                elif result['status'] == 'billing_error':
                    billing_errors += 1
                    print("💳 Stopping research due to billing error.")
                    break
                
                # Delay between requests
                await asyncio.sleep(3)
                
            except Exception as e:
                error_str = str(e).lower()
                if "billing" in error_str or "quota" in error_str:
                    print(f"💳 BILLING ERROR: {e}")
                    billing_errors += 1
                    break
                else:
                    print(f"❌ Unexpected error: {e}")
                    manual_required += 1
        
        # Return summary
        summary = {
            'total_processed': len(self.results),
            'successful': successful,
            'manual_required': manual_required,
            'billing_errors': billing_errors,
            'success_rate': successful/len(self.results)*100 if self.results else 0
        }
        
        return summary
    
    def get_results_dataframe(self):
        """Convert results to DataFrame (basic version)"""
        
        if not self.results:
            return pd.DataFrame()
        
        csv_data = []
        for result in self.results:
            csv_row = self.parse_extracted_info_to_csv(result)
            csv_data.append(csv_row)
        
        return pd.DataFrame(csv_data)
    
    def save_csv_results(self, filename=None, filter_info=None):
        """Save basic research results to CSV file"""
        
        if not filename:
            if filter_info and filter_info.get('filter_summary'):
                # Use filter information for filename
                filter_summary = filter_info['filter_summary']
                safe_filter = "".join(c for c in filter_summary if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_filter = safe_filter.replace(' ', '_')[:50]  # Limit length
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"business_research_{safe_filter}_{timestamp}.csv"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"business_contacts_{timestamp}.csv"
        
        results_df = self.get_results_dataframe()
        
        # For browser download, return the data instead of saving to disk
        print(f"📁 Results prepared for download: {filename}")
        return filename, results_df
    
    def parse_extracted_info_to_csv(self, result):
        """Parse extracted info text into CSV fields (basic version)"""
        info = result['extracted_info']
        business_name = result['business_name']
        
        csv_row = {
            'business_name': business_name,
            'phone': self.extract_field_value(info, 'PHONE:'),
            'email': self.extract_field_value(info, 'EMAIL:'),
            'website': self.extract_field_value(info, 'WEBSITE:'),
            'address': self.extract_field_value(info, 'ADDRESS:'),
            'description': self.extract_field_value(info, 'DESCRIPTION:'),
            'confidence': self.extract_field_value(info, 'CONFIDENCE:'),
            'status': result['status'],
            'research_date': result['research_date'],
            'method': result['method']
        }
        
        return csv_row
    
    def extract_field_value(self, text, field_name):
        """Extract field value from formatted text"""
        try:
            lines = text.split('\n')
            for line in lines:
                if line.strip().startswith(field_name):
                    value = line.replace(field_name, '').strip()
                    return value if value and value != "Not found" else ""
            return ""
        except:
            return ""

async def research_businesses_from_dataframe(df, consignee_column='Consignee Name', max_businesses=10, enable_justdial=False, filter_info=None):
    """
    Basic function to research businesses from a DataFrame
    
    Args:
        df: pandas DataFrame containing business data
        consignee_column: name of column containing business names
        max_businesses: maximum number of businesses to research (default 10)
        enable_justdial: ignored (kept for compatibility)
        filter_info: dictionary containing filter information for filename generation
    
    Returns:
        tuple: (results_dataframe, summary_dict, csv_filename)
    """
    
    try:
        researcher = StreamlitBusinessResearcher()
        
        # Test APIs first
        api_ok, api_message = researcher.test_apis()
        if not api_ok:
            raise Exception(f"API Test Failed: {api_message}")
        
        # Research businesses (basic functionality only)
        summary = await researcher.research_from_dataframe(
            df, 
            consignee_column=consignee_column, 
            max_businesses=max_businesses,
            enable_justdial=False  # Always disable enhanced features
        )
        
        # Get results
        results_df = researcher.get_results_dataframe()
        
        # Save to CSV with basic format
        csv_filename, results_df = researcher.save_csv_results(filter_info=filter_info)
        
        return results_df, summary, csv_filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None