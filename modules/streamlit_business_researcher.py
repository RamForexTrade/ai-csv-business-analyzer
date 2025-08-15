"""
Enhanced Streamlit Business Researcher with Government Sources and Email Integration
Includes specific searches for government business databases and official registrations
Focused on teak, wood, timber, lumber businesses with city/address verification
Integrated with Business Email Module for curated outreach
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
from modules.business_emailer import BusinessEmailer, get_email_provider_config

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
        
        # Initialize email module
        self.emailer = BusinessEmailer()
        
        self.results = []
    
    def configure_email(self, email_provider='gmail', email_address=None, email_password=None, sender_name=None):
        """Configure email settings for sending curated emails"""
        try:
            if not email_address or not email_password:
                return False, "Email address and password are required"
            
            provider_config = get_email_provider_config(email_provider)
            if not provider_config:
                return False, f"Email provider '{email_provider}' not supported"
            
            # Configure SMTP settings
            self.emailer.configure_smtp(
                smtp_server=provider_config['smtp_server'],
                port=provider_config['port'],
                email=email_address,
                password=email_password,
                sender_name=sender_name or email_address
            )
            
            # Test the configuration
            test_success, test_message = self.emailer.test_email_config()
            
            if test_success:
                return True, f"Email configured successfully with {email_provider.title()}"
            else:
                return False, f"Email configuration failed: {test_message}"
                
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"
    
    def get_businesses_with_emails(self):
        """Get list of businesses that have email addresses from research results"""
        if not self.results:
            return pd.DataFrame()
        
        # Convert results to DataFrame
        results_df = self.get_results_dataframe()
        
        # Filter businesses with valid email addresses
        businesses_with_emails = results_df[
            (results_df['email'].notna()) & 
            (results_df['email'] != '') & 
            (results_df['email'] != 'Not found') &
            (results_df['email'] != 'Research required') &
            (results_df['email'] != 'API billing error') &
            (~results_df['email'].str.contains('not relevant', case=False, na=False))
        ].copy()
        
        return businesses_with_emails
    
    def get_email_templates(self):
        """Get available email templates"""
        return self.emailer.get_default_templates()
    
    async def send_curated_emails(self, selected_businesses=None, template_name='business_intro', 
                                email_variables=None, delay_seconds=2.0, 
                                progress_callback=None, status_callback=None):
        """Send curated emails to selected businesses or all businesses with email addresses"""
        
        try:
            # Get businesses with emails
            if selected_businesses is not None:
                # Use provided business list
                businesses_to_email = selected_businesses
            else:
                # Use all businesses with email addresses
                businesses_to_email = self.get_businesses_with_emails()
            
            if len(businesses_to_email) == 0:
                return {
                    'success': False,
                    'message': 'No businesses with email addresses found',
                    'summary': {
                        'total_businesses': 0,
                        'emails_to_send': 0,
                        'emails_sent': 0,
                        'emails_failed': 0,
                        'success_rate': 0
                    }
                }
            
            # Prepare default email variables if not provided
            if not email_variables:
                email_variables = {
                    'your_company_name': 'Your Company Name',
                    'sender_name': 'Your Name',
                    'your_phone': 'Your Phone Number',
                    'your_email': 'your.email@example.com',
                    'product_requirements': 'High-quality timber and wood products',
                    'volume_requirements': 'To be discussed',
                    'timeline_requirements': 'Flexible',
                    'quality_requirements': 'Premium grade'
                }
            
            # Load email templates if not already loaded
            templates = self.emailer.get_default_templates()
            
            # Send bulk emails
            summary = await self.emailer.send_bulk_emails(
                businesses_df=businesses_to_email,
                template_name=template_name,
                base_variables=email_variables,
                delay_seconds=delay_seconds,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            return {
                'success': True,
                'message': f'Email campaign completed. Sent {summary["emails_sent"]} emails.',
                'summary': summary,
                'email_log': self.emailer.get_email_log()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Email campaign failed: {str(e)}',
                'summary': {
                    'total_businesses': 0,
                    'emails_to_send': 0,
                    'emails_sent': 0,
                    'emails_failed': 0,
                    'success_rate': 0
                }
            }
    
    def save_email_log(self, filename=None):
        """Save email sending log"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_email_log_{timestamp}.json"
        
        return self.emailer.save_email_log(filename)
    
    def get_email_statistics(self):
        """Get email sending statistics"""
        log = self.emailer.get_email_log()
        
        return {
            'total_sent': log['total_sent'],
            'total_failed': log['total_failed'],
            'success_rate': (log['total_sent'] / (log['total_sent'] + log['total_failed']) * 100) if (log['total_sent'] + log['total_failed']) > 0 else 0,
            'recent_sent': log['sent_emails'][-5:] if log['sent_emails'] else [],
            'recent_failed': log['failed_emails'][-5:] if log['failed_emails'] else []
        }
    
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
        """Research business using comprehensive multi-layer strategy"""
        
        print(f"🔍 Researching: {business_name}")
        
        try:
            # Multi-layer enhanced search strategy
            all_search_results = []
            
            # Layer 1: General wood/timber business information
            print("   📊 Layer 1: General business search...")
            general_results = self.search_general_business_info(business_name)
            all_search_results.extend(general_results)
            
            # Layer 2: Government and official sources
            print("   🏛️ Layer 2: Government sources search...")
            government_results = self.search_government_sources(business_name)
            all_search_results.extend(government_results)
            
            # Layer 3: Industry-specific sources
            print("   🌲 Layer 3: Timber industry sources...")
            industry_results = self.search_industry_sources(business_name)
            all_search_results.extend(industry_results)
            
            if not all_search_results:
                print(f"❌ No search results found for {business_name}")
                return self.create_manual_fallback(business_name)
            
            # Step 2: Extract contact info using Groq AI with comprehensive data and relevance verification
            contact_info = await self.extract_contacts_with_groq(
                business_name, all_search_results, expected_city, expected_address
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
    
    def search_general_business_info(self, business_name):
        """Search for general wood/timber business information"""
        
        search_queries = [
            f"{business_name} wood timber teak contact information phone email",
            f"{business_name} lumber plywood business address website",
            f"{business_name} timber trading company official contact",
            f"{business_name} wood export import contact details"
        ]
        
        return self.execute_search_queries(search_queries, "General")
    
    def search_government_sources(self, business_name):
        """Search specifically in government databases and official sources"""
        
        # Government and official database searches for wood/timber businesses
        government_queries = [
            f'"{business_name}" site:gov.in business registration timber',
            f'"{business_name}" site:nic.in company details wood',
            f'"{business_name}" ministry commerce industry registration timber',
            f'"{business_name}" GST registration number lumber',
            f'"{business_name}" ROC registrar companies wood',
            f'"{business_name}" forest department license timber',
            f'"{business_name}" pollution control board clearance wood',
            f'"{business_name}" shop establishment license timber',
            f'"{business_name}" trade license municipal corporation wood',
            f'"{business_name}" forest produce trading license',
            f'"{business_name}" environmental clearance wood industry',
            f'"{business_name}" state forest corporation timber dealer'
        ]
        
        return self.execute_search_queries(government_queries, "Government")
    
    def search_industry_sources(self, business_name):
        """Search in timber/wood industry specific sources"""
        
        industry_queries = [
            f'"{business_name}" timber traders association member',
            f'"{business_name}" wood importers exporters directory',
            f'"{business_name}" forest produce trading license',
            f'"{business_name}" timber merchants federation',
            f'"{business_name}" wood industry chamber commerce',
            f'"{business_name}" lumber dealers association',
            f'"{business_name}" plywood manufacturers association',
            f'"{business_name}" teak wood suppliers directory',
            f'"{business_name}" timber industry federation member',
            f'"{business_name}" wood products manufacturers association',
            f'"{business_name}" forest based industries directory',
            f'"{business_name}" timber trade association registry'
        ]
        
        return self.execute_search_queries(industry_queries, "Industry")
    
    def execute_search_queries(self, queries, search_type):
        """Execute a list of search queries and return results"""
        
        all_results = []
        
        for query in queries:
            try:
                print(f"      📝 {search_type}: {query[:60]}...")
                
                # Search with Tavily using preferred domains
                response = self.tavily_client.search(
                    query=query,
                    max_results=2,  # Reduced per query but more queries
                    search_depth="advanced",
                    include_domains=self.get_preferred_domains(search_type),
                    exclude_domains=["facebook.com", "twitter.com", "instagram.com", "linkedin.com"]
                )
                
                if response.get('results'):
                    # Tag results with search type
                    for result in response['results']:
                        result['search_type'] = search_type
                    all_results.extend(response['results'])
                    print(f"         ✅ Found {len(response['results'])} results")
                else:
                    print(f"         ❌ No results")
                    
            except Exception as e:
                print(f"         ⚠️ Error: {str(e)[:50]}")
                
        print(f"   📊 {search_type} total: {len(all_results)} results")
        return all_results
    
    def get_preferred_domains(self, search_type):
        """Get preferred domains for different search types"""
        
        domain_preferences = {
            "Government": [
                "gov.in", "nic.in", "india.gov.in", "mca.gov.in", 
                "cbic.gov.in", "incometax.gov.in", "gst.gov.in",
                "moef.gov.in", "forest.gov.in", "cpcb.nic.in",
                "sfac.in", "fsi.nic.in"
            ],
            "Industry": [
                "fidr.org", "plywoodassociation.org", "itpo.gov.in",
                "cii.in", "ficci.in", "assocham.org", "fidr.in",
                "woodindustry.in", "timberassociation.org"
            ],
            "General": None  # No domain restriction for general search
        }
        
        return domain_preferences.get(search_type)
    
    def categorize_search_results(self, search_results):
        """Categorize results by source type"""
        
        categorized = {
            'Government': [],
            'Industry': [],
            'General': []
        }
        
        for result in search_results:
            search_type = result.get('search_type', 'General')
            categorized[search_type].append(result)
        
        return categorized
    
    def format_search_results_enhanced(self, categorized_results):
        """Format categorized search results for enhanced analysis"""
        
        formatted_sections = []
        
        for category, results in categorized_results.items():
            if results:
                formatted_sections.append(f"\n=== {category.upper()} SOURCES ===")
                
                for i, result in enumerate(results[:4], 1):  # Top 4 per category
                    formatted_result = f"""
                    {category.upper()} RESULT {i}:
                    Title: {result.get('title', 'No title')}
                    URL: {result.get('url', 'No URL')}
                    Content: {result.get('content', 'No content')[:400]}...
                    """
                    formatted_sections.append(formatted_result)
        
        return '\n'.join(formatted_sections)
    
    async def extract_contacts_with_groq(self, business_name, search_results, expected_city=None, expected_address=None):
        """Enhanced Groq extraction with government data analysis and city/address verification"""
        
        print(f"   🦙 Analyzing {len(search_results)} results with Enhanced Groq...")
        
        # Categorize results by source type
        categorized_results = self.categorize_search_results(search_results)
        
        # Format results for Groq analysis
        results_text = self.format_search_results_enhanced(categorized_results)
        
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
        
        # Count sources by type
        govt_sources = len(categorized_results.get('Government', []))
        industry_sources = len(categorized_results.get('Industry', []))
        
        prompt = f"""You are analyzing comprehensive search results for businesses related to TEAK, WOOD, TIMBER, LUMBER, and PLYWOOD industries.
Results include {govt_sources} government sources, {industry_sources} industry sources, and general web sources.

BUSINESS TO RESEARCH: "{business_name}"

{location_context}

COMPREHENSIVE SEARCH RESULTS:
{results_text}

INSTRUCTIONS:
1. FOCUS: Only analyze if this business is related to teak, wood, timber, lumber, plywood, or wooden products industry
2. LOCATION VERIFICATION: If expected city/address is provided, verify if found business location matches or is geographically relevant
3. GOVERNMENT VERIFICATION: Priority to information from government sources (.gov.in domains)
4. CROSS-VERIFICATION: Cross-verify information across multiple source types
5. EXTRACT: Complete business information including official registrations and licenses

EXTRACT AND FORMAT:
BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: [YES/NO - Is this business related to wood, timber, teak, lumber, plywood industry?]
LOCATION_RELEVANT: [YES/NO/UNKNOWN - Does the found address match expected city/address? Write UNKNOWN if no expected location provided]
PHONE: [extract phone number if found and business is relevant, or "Not found"]
EMAIL: [extract email address if found and business is relevant, or "Not found"]  
WEBSITE: [extract official website URL if found and business is relevant, or "Not found"]
ADDRESS: [extract business address if found and business is relevant, or "Not found"]
CITY: [extract city from address if found, or "Not found"]
REGISTRATION_NUMBER: [extract company registration/GST number if found in government sources, or "Not found"]
LICENSE_DETAILS: [extract any timber/forest licenses mentioned, or "Not found"]
DIRECTORS: [extract director names if found in government records, or "Not found"]
DESCRIPTION: [brief description focusing on wood/timber business activities based on all sources]
GOVERNMENT_VERIFIED: [YES if found in government sources, NO if only general/industry sources]
CONFIDENCE: [rate 1-10 based on quality, number of sources, and government verification]
RELEVANCE_NOTES: [explain industry relevance, location match, and source quality]

STRICT RULES:
1. Only extract information if INDUSTRY_RELEVANT = YES
2. Only extract information if LOCATION_RELEVANT = YES or UNKNOWN
3. If business is not wood/timber related, set all contact fields to "Not relevant - not wood/timber business"
4. If location doesn't match expected city/address, set all contact fields to "Not relevant - location mismatch"
5. Prioritize information from government sources over other sources
6. Mark GOVERNMENT_VERIFIED = YES only if found in .gov.in domains
7. Higher confidence for government-verified businesses
8. Include registration numbers and licenses for legitimacy verification

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
                    "max_tokens": 1200,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    extracted_info = result['choices'][0]['message']['content']
                    print(f"   ✅ Enhanced Groq extraction completed")
                    
                    # Check if we need second verification
                    needs_verification = await self.check_if_needs_verification(extracted_info, business_name, results_text, expected_city, expected_address)
                    
                    if needs_verification:
                        print(f"   🔍 Running second verification...")
                        extracted_info = await self.run_second_verification(extracted_info, business_name, results_text, expected_city, expected_address)
                    
                    result_data = {
                        'business_name': business_name,
                        'extracted_info': extracted_info,
                        'raw_search_results': search_results,
                        'government_sources_found': govt_sources,
                        'industry_sources_found': industry_sources,
                        'total_sources': len(search_results),
                        'research_date': datetime.now().isoformat(),
                        'method': 'Enhanced Tavily + Groq - Government + Industry Sources',
                        'status': 'success',
                        'expected_city': expected_city,
                        'expected_address': expected_address
                    }
                    
                    self.results.append(result_data)
                    
                    # Display results
                    print(f"   📋 Enhanced Results for {business_name}:")
                    print("-" * 60)
                    print(extracted_info)
                    print("-" * 60)
                    print(f"   📊 Sources: {govt_sources} govt, {industry_sources} industry, {len(search_results)} total")
                    
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
            "partial" in extracted_info.lower() or "similar" in extracted_info.lower(),
            "GOVERNMENT_VERIFIED: NO" in extracted_info and "gov.in" in results_text
        ]
        
        return any(ambiguous_indicators)
    
    async def run_second_verification(self, first_result, business_name, results_text, expected_city, expected_address):
        """Run second verification for ambiguous cases"""
        
        verification_prompt = f"""You are doing a SECOND VERIFICATION of comprehensive business research results.

BUSINESS: {business_name}
EXPECTED CITY: {expected_city if expected_city else 'Not provided'}
EXPECTED ADDRESS: {expected_address if expected_address else 'Not provided'}

FIRST ANALYSIS RESULT:
{first_result}

ORIGINAL COMPREHENSIVE SEARCH RESULTS:
{results_text}

SECOND VERIFICATION TASK:
1. Re-examine if this business is truly related to wood, timber, teak, lumber, plywood industry
2. Double-check location relevance - is the found city/address close to or matching the expected location?
3. Re-verify government sources presence and official business registration details
4. Look for any missed contact information or official registrations in the search results
5. Provide a more definitive assessment with higher confidence

Provide your FINAL VERIFIED result in the same enhanced format:

BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: [YES/NO after second verification]
LOCATION_RELEVANT: [YES/NO/UNCLEAR after careful location comparison]
PHONE: [verified phone number or "Not found"]
EMAIL: [verified email or "Not found"]
WEBSITE: [verified website or "Not found"]
ADDRESS: [verified address or "Not found"]
CITY: [verified city or "Not found"]
REGISTRATION_NUMBER: [verified registration/GST number or "Not found"]
LICENSE_DETAILS: [verified licenses or "Not found"]
DIRECTORS: [verified directors or "Not found"]
DESCRIPTION: [verified description of wood/timber activities]
GOVERNMENT_VERIFIED: [YES/NO after re-checking government sources]
CONFIDENCE: [rate 1-10 after second verification]
VERIFICATION_NOTES: [explain your second verification findings and final decision]

CRITICAL: Be more decisive in your YES/NO determinations after this second comprehensive review.
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
                    "max_tokens": 1200,
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
        """Enhanced fallback with comprehensive government research suggestions"""
        
        fallback_info = f"""
        BUSINESS_NAME: {business_name}
        INDUSTRY_RELEVANT: UNKNOWN
        LOCATION_RELEVANT: UNKNOWN
        PHONE: Research required
        EMAIL: Research required
        WEBSITE: Research required  
        ADDRESS: Research required
        CITY: Research required
        REGISTRATION_NUMBER: Research required
        LICENSE_DETAILS: Research required
        DIRECTORS: Research required
        DESCRIPTION: Business - requires manual verification for wood/timber relevance
        GOVERNMENT_VERIFIED: NO - manual verification needed
        CONFIDENCE: 1
        RELEVANCE_NOTES: Automated research failed - comprehensive manual verification needed

        COMPREHENSIVE MANUAL RESEARCH NEEDED:
        
        Government Sources:
        1. MCA Portal: https://www.mca.gov.in/ (Company registration details)
        2. GST Portal: https://gst.gov.in/ (GST registration and verification)
        3. State Forest Department websites (Timber trading licenses)
        4. Forest Survey of India: https://fsi.nic.in/ (Forest clearances)
        5. Central Pollution Control Board (Environmental clearances)
        6. Shop & Establishment license databases (Local municipal)
        7. SFAC Portal: https://sfac.in/ (Forest corporation registrations)
        
        Industry Sources:
        8. FIDR: https://fidr.org/ (Forest Industries Directory)
        9. Timber Traders Association directories (State-wise)
        10. Export-Import databases (DGFT if applicable)
        11. Chamber of Commerce member lists (CII, FICCI, ASSOCHAM)
        12. Plywood Manufacturers Association directories
        
        General Sources:
        13. Google: "{business_name}" + "wood" OR "timber" OR "teak" contact
        14. Business directories and Yellow Pages
        15. LinkedIn company profiles for wood/timber businesses
        """
        
        result = {
            'business_name': business_name,
            'extracted_info': fallback_info,
            'raw_search_results': [],
            'government_sources_found': 0,
            'industry_sources_found': 0,
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'method': 'Enhanced Manual Fallback',
            'status': 'manual_required'
        }
        
        self.results.append(result)
        
        print(f"   ⚠️  Enhanced manual research required for {business_name}")
        
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
        REGISTRATION_NUMBER: API billing error
        LICENSE_DETAILS: API billing error
        DIRECTORS: API billing error
        DESCRIPTION: Research stopped due to API billing/quota issue
        GOVERNMENT_VERIFIED: NO
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
            'government_sources_found': 0,
            'industry_sources_found': 0,
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'method': 'Billing Error',
            'status': 'billing_error'
        }
        
        self.results.append(result)
        
        print(f"   💳 Billing error occurred for {business_name}")
        
        return result
    
    async def research_from_dataframe(self, df, consignee_column='Consignee Name', city_column=None, address_column=None, max_businesses=None, enable_justdial=False):
        """Research businesses from DataFrame with enhanced comprehensive search and city/address verification"""
        
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
        print(f"🎯 Enhanced Strategy: General + Government + Industry sources")
        
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
        print(f"⚠️ Note: Enhanced search takes longer (~45-60 seconds per business)")
        
        # Research each business with comprehensive verification
        successful = 0
        government_verified = 0
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
                # Enhanced research with comprehensive sources
                result = await self.research_business_direct(
                    business_name, expected_city, expected_address
                )
                
                if result['status'] == 'success':
                    successful += 1
                    if result.get('government_sources_found', 0) > 0:
                        government_verified += 1
                elif result['status'] == 'manual_required':
                    manual_required += 1
                elif result['status'] == 'billing_error':
                    billing_errors += 1
                    print("💳 Stopping research due to billing error.")
                    break
                
                # Longer delay for comprehensive search
                await asyncio.sleep(4)
                
            except Exception as e:
                error_str = str(e).lower()
                if "billing" in error_str or "quota" in error_str:
                    print(f"💳 BILLING ERROR: {e}")
                    billing_errors += 1
                    break
                else:
                    print(f"❌ Unexpected error: {e}")
                    manual_required += 1
        
        # Return enhanced summary
        summary = {
            'total_processed': len(self.results),
            'successful': successful,
            'government_verified': government_verified,
            'manual_required': manual_required,
            'billing_errors': billing_errors,
            'success_rate': successful/len(self.results)*100 if self.results else 0,
            'government_verification_rate': government_verified/len(self.results)*100 if self.results else 0
        }
        
        return summary
    
    def get_results_dataframe(self):
        """Convert enhanced results to DataFrame"""
        
        if not self.results:
            return pd.DataFrame()
        
        csv_data = []
        for result in self.results:
            csv_row = self.parse_extracted_info_to_csv(result)
            csv_data.append(csv_row)
        
        return pd.DataFrame(csv_data)
    
    def save_csv_results(self, filename=None, filter_info=None):
        """Save enhanced research results to CSV file"""
        
        if not filename:
            if filter_info and filter_info.get('filter_summary'):
                # Use filter information for filename
                filter_summary = filter_info['filter_summary']
                safe_filter = "".join(c for c in filter_summary if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_filter = safe_filter.replace(' ', '_')[:50]  # Limit length
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enhanced_wood_timber_research_{safe_filter}_{timestamp}.csv"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enhanced_wood_timber_contacts_{timestamp}.csv"
        
        results_df = self.get_results_dataframe()
        
        # For browser download, return the data instead of saving to disk
        print(f"📁 Enhanced results prepared for download: {filename}")
        return filename, results_df
    
    def parse_extracted_info_to_csv(self, result):
        """Parse enhanced extracted info text into CSV fields"""
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
            'registration_number': self.extract_field_value(info, 'REGISTRATION_NUMBER:'),
            'license_details': self.extract_field_value(info, 'LICENSE_DETAILS:'),
            'directors': self.extract_field_value(info, 'DIRECTORS:'),
            'description': self.extract_field_value(info, 'DESCRIPTION:'),
            'government_verified': self.extract_field_value(info, 'GOVERNMENT_VERIFIED:'),
            'confidence': self.extract_field_value(info, 'CONFIDENCE:'),
            'relevance_notes': self.extract_field_value(info, 'RELEVANCE_NOTES:') or self.extract_field_value(info, 'VERIFICATION_NOTES:'),
            'status': result['status'],
            'govt_sources_found': result.get('government_sources_found', 0),
            'industry_sources_found': result.get('industry_sources_found', 0),
            'total_sources': result.get('total_sources', 0),
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
    Enhanced research of wood/timber businesses from a DataFrame with comprehensive government and industry sources
    
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
        
        # Enhanced research with comprehensive sources and verification
        summary = await researcher.research_from_dataframe(
            df, 
            consignee_column=consignee_column,
            city_column=city_column,
            address_column=address_column,
            max_businesses=max_businesses,
            enable_justdial=False  # Always disable enhanced features
        )
        
        # Get enhanced results
        results_df = researcher.get_results_dataframe()
        
        # Save to CSV with enhanced format
        csv_filename, results_df = researcher.save_csv_results(filter_info=filter_info)
        
        return results_df, summary, csv_filename, researcher
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None, None

# Email integration functions for Streamlit interface
async def send_curated_business_emails(researcher, selected_businesses=None, email_config=None, template_name='business_intro', email_variables=None, delay_seconds=2.0, progress_callback=None, status_callback=None):
    """
    Send curated emails to businesses with email addresses
    
    Args:
        researcher: StreamlitBusinessResearcher instance
        selected_businesses: DataFrame of selected businesses (if None, uses all with emails)
        email_config: Dictionary with email configuration
        template_name: Email template to use
        email_variables: Variables to populate in email template
        delay_seconds: Delay between emails to avoid rate limiting
        progress_callback: Function to call for progress updates
        status_callback: Function to call for status updates
    
    Returns:
        dict: Email campaign results
    """
    
    try:
        # Configure email if provided
        if email_config:
            success, message = researcher.configure_email(
                email_provider=email_config.get('provider', 'gmail'),
                email_address=email_config.get('email'),
                email_password=email_config.get('password'),
                sender_name=email_config.get('sender_name')
            )
            
            if not success:
                return {
                    'success': False,
                    'message': f"Email configuration failed: {message}",
                    'summary': {
                        'total_businesses': 0,
                        'emails_to_send': 0,
                        'emails_sent': 0,
                        'emails_failed': 0,
                        'success_rate': 0
                    }
                }
        
        # Send emails
        return await researcher.send_curated_emails(
            selected_businesses=selected_businesses,
            template_name=template_name,
            email_variables=email_variables,
            delay_seconds=delay_seconds,
            progress_callback=progress_callback,
            status_callback=status_callback
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Email sending failed: {str(e)}",
            'summary': {
                'total_businesses': 0,
                'emails_to_send': 0,
                'emails_sent': 0,
                'emails_failed': 0,
                'success_rate': 0
            }
        }
