# Research Status Tracking Feature

## Overview
The AI CSV Business Analyzer now includes research status tracking to prevent duplicate research for consignee names that have already been processed. This feature saves time, reduces API costs, and improves efficiency.

## Key Features

### 1. Automatic Duplicate Detection
- The system automatically tracks which businesses have been researched
- Prevents redundant API calls for the same consignee name
- Uses case-insensitive matching for business names

### 2. Research Status Cache
- Maintains an in-memory cache of research status for each business
- Tracks status: `completed`, `manual_required`, `billing_error`, `cached`
- Includes timestamp of original research

### 3. Enhanced Research Results Table
The research results now include additional columns for status tracking:

| Column | Description |
|--------|-------------|
| `research_status` | Status of the research operation |
| `research_method` | Method used for research |
| `research_sources_found` | Number of sources found |
| `research_govt_sources` | Number of government sources |
| `research_industry_sources` | Number of industry sources |
| `research_match_confidence` | Confidence level of the match |

### 4. Resumable Research Sessions
- Can resume research from where it left off
- Loads existing research status from previous CSV exports
- Skips already researched businesses automatically

## How It Works

### 1. First Research Session
```python
# When researching businesses for the first time
researcher = StreamlitBusinessResearcher()
summary = await researcher.research_from_dataframe(df, skip_researched=True)
```

### 2. Subsequent Sessions
```python
# The system automatically loads previous research status
# and skips already researched businesses
researcher.load_research_cache_from_dataframe(existing_df, 'business_name', 'research_status')
```

### 3. Status Checking
```python
# Check if a business has been researched
if researcher.is_already_researched("ABC Company"):
    print("Business already researched")
```

## Configuration Options

### Skip Researched Businesses (Default: True)
```python
# Skip businesses that have already been researched
await researcher.research_from_dataframe(df, skip_researched=True)

# Force research even for previously researched businesses
await researcher.research_from_dataframe(df, skip_researched=False)
```

### Force Re-research
```python
# Force research for a specific business even if cached
result = await researcher.research_business_direct(
    business_name, 
    force_research=True
)
```

## Benefits

### 1. Cost Savings
- Reduces API calls to Tavily and Groq
- Saves processing time
- Prevents unnecessary billing charges

### 2. Improved User Experience
- Faster research sessions
- Clear status reporting
- Progress tracking

### 3. Better Data Management
- Maintains research history
- Tracks research quality and sources
- Enables incremental research

## Status Codes

| Status | Description |
|--------|-------------|
| `completed` | Research completed successfully |
| `success` | Research found valid business information |
| `manual_required` | Automated research failed, manual verification needed |
| `billing_error` | API billing/quota issue occurred |
| `cached` | Result retrieved from previous research |
| `not_researched` | Business has not been researched yet |

## Example Usage

### 1. Basic Research with Duplicate Prevention
```python
# Import the module
from modules.streamlit_business_researcher import research_businesses_from_dataframe

# Research businesses (automatically skips duplicates)
results_df, summary, filename, researcher = await research_businesses_from_dataframe(
    df=your_dataframe,
    consignee_column='Consignee Name',
    max_businesses=50,
    skip_researched=True  # Default behavior
)

# Check summary for skipped businesses
print(f"Skipped {summary['skipped_duplicate']} already researched businesses")
```

### 2. View Research Status Summary
```python
# Get status summary
cache_summary = researcher.get_research_status_summary()
print(f"Total cached: {cache_summary['total_cached']}")
print(f"Completed: {cache_summary['completed']}")
print(f"Manual required: {cache_summary['manual_required']}")
```

### 3. Load Previous Research
```python
# Load existing research results
previous_df = pd.read_csv('previous_research_results.csv')
researcher.load_research_cache_from_dataframe(
    previous_df, 
    'business_name', 
    'research_status'
)
```

## Integration with CSV Export

When exporting research results, the CSV now includes:

- **Enhanced status tracking columns**
- **Research metadata (sources, confidence, dates)**
- **Method and verification information**
- **Cache and duplicate information**

## UI Improvements

### 1. Research Progress Display
- Shows number of businesses skipped (already researched)
- Displays cache statistics
- Progress indicators for new vs. cached results

### 2. Integration Interface
- Enhanced status breakdown showing cached vs. new results
- Better matching statistics
- Research coverage metrics

## Technical Implementation

### Cache Management
```python
# Internal cache structure
research_status_cache = {
    "normalized_business_name": {
        "status": "completed",
        "timestamp": "2024-01-15T10:30:00",
        "business_name": "Original Business Name"
    }
}
```

### Status Persistence
- Status is saved in the `research_status` column of exported CSV
- Automatically loaded when processing the same dataset
- Maintains research history across sessions

## Best Practices

### 1. Regular Exports
- Export research results regularly to persist status
- Use timestamped filenames for version control
- Keep backup copies of research data

### 2. Status Management
- Review manual_required businesses periodically
- Update API credentials to resolve billing_error status
- Use force_research sparingly to avoid unnecessary costs

### 3. Data Quality
- Verify cached results are still relevant
- Check for business name variations that might create duplicates
- Monitor research confidence levels

## Troubleshooting

### Clear Cache
```python
# Clear the research status cache if needed
researcher.clear_research_cache()
```

### Check Specific Business Status
```python
# Get detailed status for a business
status = researcher.get_research_status("Business Name")
print(f"Status: {status['status']}, Date: {status.get('timestamp')}")
```

### Force Research for Specific Business
```python
# Force research even if cached
result = await researcher.research_business_direct(
    "Business Name",
    force_research=True
)
```
