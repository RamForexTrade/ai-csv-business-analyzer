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
    
    async def research_business_direct(self, business_name, expected_city=None, expected_address=None):
        """Research business using Tavily + Groq directly"""
        
        print(f"🔍 Researching: {business_name}")
        
        try:
            # Step 1: Search with Tavily - Focus on wood/timber businesses
            search_results = self.search_with_tavily(business_name)
            
            if not search_results:
                print(f"❌ No search results found for {business_name}")
                return self.create_manual_fallback(business_name)
            
            # Step 2: Extract contact info using Groq AI with relevance verification
            contact_info = await self.extract_contacts_with_groq(
                business_name, search_results, expected_city, expected_address
            )
            
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
        """Search for business information using Tavily API - Focus on wood/timber"""
        
        print(f"   🌐 Searching Tavily for: {business_name}")
        
        try:
            # Wood/timber focused search queries
            search_queries = [
                f"{business_name} wood timber teak contact information phone email",
                f"{business_name} lumber plywood business address",
                f"{business_name} timber trading company website official",
                f"{business_name} wood export import contact"
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
    
    async def extract_contacts_with_groq(self, business_name, search_results, expected_city=None, expected_address=None):
        """Use Groq (Llama) to extract contact information with city/address relevance verification"""
        
        print(f"   🦙 Analyzing results with Groq (Llama)...")
        
        # Prepare search results text for Groq
        results_text = self.format_search_results(search_results)
        
        # Build the expected location context
        location_context = ""
        if expected_city or expected_address:
            location_context = f"""
EXPECTED LOCATION FROM INPUT DATA:
Expected City: {expected_city if expected_city else 'Not provided'}
Expected Address: {expected_address if expected_address else 'Not provided'}

LOCATION VERIFICATION REQUIRED:
You must verify if the business address/city found in search results matches or is relevant to the expected location above.
"""
        
        prompt = f"""You are analyzing search results for businesses related to TEAK, WOOD, TIMBER, LUMBER, and PLYWOOD industries.

BUSINESS TO RESEARCH: "{business_name}"

{location_context}

SEARCH RESULTS:
{results_text}

INSTRUCTIONS:
1. FOCUS: Only analyze if this business is related to teak, wood, timber, lumber, plywood, or wooden products industry
2. LOCATION VERIFICATION: If expected city/address is provided, verify if found business location matches or is geographically relevant
3. EXTRACT: Contact information only if business is wood/timber related AND location is relevant

EXTRACT AND FORMAT:
BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: [YES/NO - Is this business related to wood, timber, teak, lumber, plywood industry?]
LOCATION_RELEVANT: [YES/NO/UNKNOWN - Does the found address match expected city/address? Write UNKNOWN if no expected location provided]
PHONE: [extract phone number if found and business is relevant, or "Not found"]
EMAIL: [extract email address if found and business is relevant, or "Not found"]  
WEBSITE: [extract official website URL if found and business is relevant, or "Not found"]
ADDRESS: [extract business address if found and business is relevant, or "Not found"]
CITY: [extract city from address if found, or "Not found"]
DESCRIPTION: [brief description focusing on wood/timber business activities, or "No description available"]
CONFIDENCE: [rate 1-10 how confident you are this is the correct wood/timber business]
RELEVANCE_NOTES: [explain why location and industry are relevant or not]

STRICT RULES:
1. Only extract information if INDUSTRY_RELEVANT = YES
2. Only extract information if LOCATION_RELEVANT = YES or UNKNOWN
3. If business is not wood/timber related, set all contact fields to "Not relevant - not wood/timber business"
4. If location doesn't match expected city/address, set all contact fields to "Not relevant - location mismatch"
5. Don't make up or assume any contact details
6. Prefer official websites over directory listings

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
                    "max_tokens": 1000,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    extracted_info = result['choices'][0]['message']['content']
                    print(f"   ✅ Groq extraction completed")
                    
                    # Check if we need second verification
                    needs_verification = await self.check_if_needs_verification(extracted_info, business_name, results_text, expected_city, expected_address)
                    
                    if needs_verification:
                        print(f"   🔍 Running second verification...")
                        extracted_info = await self.run_second_verification(extracted_info, business_name, results_text, expected_city, expected_address)
                    
                    result_data = {
                        'business_name': business_name,
                        'extracted_info': extracted_info,
                        'raw_search_results': search_results,
                        'research_date': datetime.now().isoformat(),
                        'method': 'Tavily + Groq (Llama) - Wood/Timber Focused',
                        'status': 'success',
                        'expected_city': expected_city,
                        'expected_address': expected_address
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
    
    async def check_if_needs_verification(self, extracted_info, business_name, results_text, expected_city, expected_address):
        """Check if the extracted information needs second verification"""
        
        # Check for ambiguous cases that need verification
        ambiguous_indicators = [
            "LOCATION_RELEVANT: UNKNOWN" in extracted_info,
            "CONFIDENCE: 1" in extracted_info or "CONFIDENCE: 2" in extracted_info or "CONFIDENCE: 3" in extracted_info,
            "Not found" in extracted_info and expected_city,
            "partial" in extracted_info.lower() or "similar" in extracted_info.lower()
        ]
        
        return any(ambiguous_indicators)
    
    async def run_second_verification(self, first_result, business_name, results_text, expected_city, expected_address):
        """Run second verification for ambiguous cases"""
        
        verification_prompt = f"""You are doing a SECOND VERIFICATION of business research results.

BUSINESS: {business_name}
EXPECTED CITY: {expected_city if expected_city else 'Not provided'}
EXPECTED ADDRESS: {expected_address if expected_address else 'Not provided'}

FIRST ANALYSIS RESULT:
{first_result}

ORIGINAL SEARCH RESULTS:
{results_text}

SECOND VERIFICATION TASK:
1. Re-examine if this business is truly related to wood, timber, teak, lumber, plywood industry
2. Double-check location relevance - is the found city/address close to or matching the expected location?
3. Look for any missed contact information in the search results
4. Provide a more definitive assessment

Provide your FINAL VERIFIED result in the same format:

BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: [YES/NO after second verification]
LOCATION_RELEVANT: [YES/NO/UNCLEAR after careful location comparison]
PHONE: [verified phone number or "Not found"]
EMAIL: [verified email or "Not found"]
WEBSITE: [verified website or "Not found"]
ADDRESS: [verified address or "Not found"]
CITY: [verified city or "Not found"]
DESCRIPTION: [verified description of wood/timber activities or "No description available"]
CONFIDENCE: [rate 1-10 after second verification]
VERIFICATION_NOTES: [explain your second verification findings and decision]

CRITICAL: Be more decisive in your YES/NO determinations after this second look.
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
                    "messages": [{"role": "user", "content": verification_prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    verified_info = result['choices'][0]['message']['content']
                    print(f"   ✅ Second verification completed")
                    return verified_info
                else:
                    print(f"   ❌ Second verification failed, using first result")
                    return first_result
            else:
                print(f"   ❌ Second verification API error, using first result")
                return first_result
                
        except Exception as e:
            print(f"   ❌ Second verification error: {e}, using first result")
            return first_result
    
    def create_manual_fallback(self, business_name):
        """Create fallback result when automated research fails"""
        
        fallback_info = f"""
        BUSINESS_NAME: {business_name}
        INDUSTRY_RELEVANT: UNKNOWN
        LOCATION_RELEVANT: UNKNOWN
        PHONE: Research required
        EMAIL: Research required
        WEBSITE: Research required  
        ADDRESS: Research required
        CITY: Research required
        DESCRIPTION: Business - requires manual verification for wood/timber relevance
        CONFIDENCE: 1
        RELEVANCE_NOTES: Automated research failed - manual verification needed for industry and location relevance

        MANUAL RESEARCH NEEDED:
        1. Verify if business is related to teak, wood, timber, lumber, plywood industry
        2. Google search: "{business_name}" + "wood" OR "timber" OR "teak" contact information
        3. Check trade association listings and timber industry directories
        4. Verify location matches expected city/address from input data
        5. Look for trade association listings in wood/timber industry
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
        INDUSTRY_RELEVANT: UNKNOWN
        LOCATION_RELEVANT: UNKNOWN
        PHONE: API billing error
        EMAIL: API billing error
        WEBSITE: API billing error  
        ADDRESS: API billing error
        CITY: API billing error
        DESCRIPTION: Research stopped due to API billing/quota issue
        CONFIDENCE: 0
        RELEVANCE_NOTES: Research was stopped due to API billing or quota limits

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
    
    async def research_from_dataframe(self, df, consignee_column='Consignee Name', city_column=None, address_column=None, max_businesses=None, enable_justdial=False):
        """Research businesses from DataFrame with city/address verification"""
        
        # Extract business names from the specified column
        if consignee_column not in df.columns:
            available_cols = [col for col in df.columns if 'consignee' in col.lower() or 'name' in col.lower()]
            if available_cols:
                consignee_column = available_cols[0]
                print(f"⚠️  Column '{consignee_column}' not found. Using '{consignee_column}' instead.")
            else:
                raise ValueError(f"Column '{consignee_column}' not found in DataFrame. Available columns: {list(df.columns)}")
        
        # Auto-detect city and address columns if not specified
        if not city_column:
            city_cols = [col for col in df.columns if 'city' in col.lower() or 'consignee.*city' in col.lower()]
            city_column = city_cols[0] if city_cols else None
            
        if not address_column:
            addr_cols = [col for col in df.columns if 'address' in col.lower() or 'consignee.*address' in col.lower()]
            address_column = addr_cols[0] if addr_cols else None
        
        print(f"📍 Using columns - Business: {consignee_column}, City: {city_column}, Address: {address_column}")
        
        # Get unique business names with their city/address info
        business_data = []
        for _, row in df.iterrows():
            business_name = row.get(consignee_column)
            if pd.notna(business_name) and str(business_name).strip():
                city = row.get(city_column) if city_column else None
                address = row.get(address_column) if address_column else None
                business_data.append({
                    'name': str(business_name).strip(),
                    'city': str(city).strip() if pd.notna(city) else None,
                    'address': str(address).strip() if pd.notna(address) else None
                })
        
        # Remove duplicates based on business name
        unique_businesses = {}
        for item in business_data:
            if item['name'] not in unique_businesses:
                unique_businesses[item['name']] = item
        
        business_list = list(unique_businesses.values())
        
        if not business_list:
            raise ValueError(f"No business names found in column '{consignee_column}'")
        
        # Limit number of businesses if specified
        if max_businesses and max_businesses < len(business_list):
            business_list = business_list[:max_businesses]
            print(f"🎯 Limited to first {max_businesses} businesses")
        
        total_businesses = len(business_list)
        print(f"📋 Found {total_businesses} unique businesses to research")
        
        # Research each business with city/address verification
        successful = 0
        manual_required = 0
        billing_errors = 0
        
        for i, business_info in enumerate(business_list, 1):
            business_name = business_info['name']
            expected_city = business_info['city']
            expected_address = business_info['address']
            
            print(f"\n📊 Progress: {i}/{total_businesses}")
            print(f"🏢 Business: {business_name}")
            if expected_city:
                print(f"📍 Expected City: {expected_city}")
            if expected_address:
                print(f"🏠 Expected Address: {expected_address}")
            
            try:
                # Research with city/address verification
                result = await self.research_business_direct(
                    business_name, expected_city, expected_address
                )
                
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
        """Convert results to DataFrame"""
        
        if not self.results:
            return pd.DataFrame()
        
        csv_data = []
        for result in self.results:
            csv_row = self.parse_extracted_info_to_csv(result)
            csv_data.append(csv_row)
        
        return pd.DataFrame(csv_data)
    
    def save_csv_results(self, filename=None, filter_info=None):
        """Save research results to CSV file"""
        
        if not filename:
            if filter_info and filter_info.get('filter_summary'):
                # Use filter information for filename
                filter_summary = filter_info['filter_summary']
                safe_filter = "".join(c for c in filter_summary if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_filter = safe_filter.replace(' ', '_')[:50]  # Limit length
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"wood_timber_research_{safe_filter}_{timestamp}.csv"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"wood_timber_contacts_{timestamp}.csv"
        
        results_df = self.get_results_dataframe()
        
        # For browser download, return the data instead of saving to disk
        print(f"📁 Results prepared for download: {filename}")
        return filename, results_df
    
    def parse_extracted_info_to_csv(self, result):
        """Parse extracted info text into CSV fields"""
        info = result['extracted_info']
        business_name = result['business_name']
        
        csv_row = {
            'business_name': business_name,
            'industry_relevant': self.extract_field_value(info, 'INDUSTRY_RELEVANT:'),
            'location_relevant': self.extract_field_value(info, 'LOCATION_RELEVANT:'),
            'phone': self.extract_field_value(info, 'PHONE:'),
            'email': self.extract_field_value(info, 'EMAIL:'),
            'website': self.extract_field_value(info, 'WEBSITE:'),
            'address': self.extract_field_value(info, 'ADDRESS:'),
            'city': self.extract_field_value(info, 'CITY:'),
            'description': self.extract_field_value(info, 'DESCRIPTION:'),
            'confidence': self.extract_field_value(info, 'CONFIDENCE:'),
            'relevance_notes': self.extract_field_value(info, 'RELEVANCE_NOTES:') or self.extract_field_value(info, 'VERIFICATION_NOTES:'),
            'status': result['status'],
            'research_date': result['research_date'],
            'method': result['method'],
            'expected_city': result.get('expected_city', ''),
            'expected_address': result.get('expected_address', '')
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

async def research_businesses_from_dataframe(df, consignee_column='Consignee Name', city_column=None, address_column=None, max_businesses=10, enable_justdial=False, filter_info=None):
    """
    Research wood/timber businesses from a DataFrame with city/address verification
    
    Args:
        df: pandas DataFrame containing business data
        consignee_column: name of column containing business names
        city_column: name of column containing city information (auto-detected if None)
        address_column: name of column containing address information (auto-detected if None)
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
        
        # Research businesses with city/address verification
        summary = await researcher.research_from_dataframe(
            df, 
            consignee_column=consignee_column,
            city_column=city_column,
            address_column=address_column,
            max_businesses=max_businesses,
            enable_justdial=False  # Always disable enhanced features
        )
        
        # Get results
        results_df = researcher.get_results_dataframe()
        
        # Save to CSV with wood/timber focus
        csv_filename, results_df = researcher.save_csv_results(filter_info=filter_info)
        
        return results_df, summary, csv_filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None
