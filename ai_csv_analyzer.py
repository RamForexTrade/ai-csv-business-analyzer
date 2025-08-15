import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import requests
import json
import warnings
import os
import re
import sys
import asyncio
import tempfile
import io

# Handle environment variables for both local and Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file if running locally
except ImportError:
    # dotenv not available (e.g., on Streamlit Cloud)
    pass

# Import web scraping module
from modules.web_scraping_module import perform_web_scraping

# Import simplified data explorer
from data_explorer_new import create_data_explorer

warnings.filterwarnings('ignore')

# Helper function to get environment variables from either .env or Streamlit secrets
def get_env_var(key, default=None):
    """Get environment variable from .env file (local) or Streamlit secrets (cloud)"""
    # First try regular environment variables (from .env or system)
    value = os.getenv(key)
    if value:
        return value

    # Then try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return default

# Page configuration
st.set_page_config(
    page_title="AI-Powered CSV Data Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for better dark/light mode support
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Better contrast for both light and dark modes */
    .user-message {
        background: rgba(33, 150, 243, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
        color: var(--text-color);
    }

    .ai-message {
        background: rgba(76, 175, 80, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4caf50;
        color: var(--text-color);
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .user-message {
            background: rgba(33, 150, 243, 0.2);
            color: #e0e0e0;
        }

        .ai-message {
            background: rgba(76, 175, 80, 0.2);
            color: #e0e0e0;
        }
    }

    /* Streamlit dark theme support */
    .stApp[data-theme="dark"] .user-message {
        background: rgba(33, 150, 243, 0.2);
        color: #ffffff;
    }

    .stApp[data-theme="dark"] .ai-message {
        background: rgba(76, 175, 80, 0.2);
        color: #ffffff;
    }

    /* Light theme support */
    .stApp[data-theme="light"] .user-message {
        background: rgba(33, 150, 243, 0.1);
        color: #000000;
    }

    .stApp[data-theme="light"] .ai-message {
        background: rgba(76, 175, 80, 0.1);
        color: #000000;
    }

    .data-insight {
        background: rgba(255, 152, 0, 0.1);
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #ff9800;
        margin: 10px 0;
    }

    .identifier-warning {
        background: rgba(255, 193, 7, 0.1);
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #ffc107;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def detect_identifier_columns(df):
    """
    Detect columns that should be treated as identifiers (like HS codes) rather than numeric values
    """
    identifier_columns = []
    identifier_patterns = [
        # HS codes and trade-related identifiers
        r'.*hs.*code.*', r'.*harmonized.*', r'.*tariff.*', r'.*commodity.*code.*',
        # Product/item identifiers
        r'.*product.*code.*', r'.*item.*code.*', r'.*sku.*', r'.*barcode.*', r'.*upc.*',
        # General ID patterns
        r'.*\\bid\\b.*', r'.*identifier.*', r'.*ref.*', r'.*code.*', r'.*key.*',
        # Postal/geographic codes
        r'.*zip.*', r'.*postal.*', r'.*country.*code.*', r'.*region.*code.*',
        # Other common identifiers
        r'.*serial.*', r'.*batch.*', r'.*lot.*'
    ]

    for col in df.columns:
        col_lower = col.lower()

        # Check if column name matches identifier patterns
        is_identifier_by_name = any(re.match(pattern, col_lower) for pattern in identifier_patterns)

        # Check data characteristics for likely identifiers
        if df[col].dtype in ['int64', 'float64'] or df[col].dtype == 'object':
            sample_values = df[col].dropna().astype(str).head(100)

            if len(sample_values) > 0:
                # Check for patterns that suggest identifiers
                has_leading_zeros = any(val.startswith('0') and len(val) > 1 for val in sample_values if val.isdigit())
                has_fixed_length = len(set(len(str(val)) for val in sample_values)) <= 3  # Most values have similar length
                mostly_unique = df[col].nunique() / len(df) > 0.8  # High uniqueness ratio
                contains_non_numeric = any(not str(val).replace('.', '').isdigit() for val in sample_values)

                # HS codes are typically 4-10 digits
                looks_like_hs_code = all(
                    len(str(val).replace('.', '')) >= 4 and
                    len(str(val).replace('.', '')) <= 10
                    for val in sample_values[:10] if str(val).replace('.', '').isdigit()
                )

                is_identifier_by_data = (
                    has_leading_zeros or
                    (has_fixed_length and mostly_unique) or
                    (looks_like_hs_code and col_lower in ['hs_code', 'hs', 'code', 'tariff_code']) or
                    (contains_non_numeric and not df[col].dtype in ['datetime64[ns]'])
                )

                if is_identifier_by_name or is_identifier_by_data:
                    identifier_columns.append(col)

    return identifier_columns

def smart_csv_loader(uploaded_file):
    """
    Intelligently load CSV with proper data type detection for identifiers
    """
    # First pass: read with default types to analyze structure
    try:
        df_preview = pd.read_csv(uploaded_file, nrows=1000)
        uploaded_file.seek(0)  # Reset file pointer

        # Detect identifier columns
        identifier_cols = detect_identifier_columns(df_preview)

        # Create dtype dictionary to force string types for identifiers
        dtype_dict = {}
        for col in identifier_cols:
            dtype_dict[col] = str

        # Read the full file with proper dtypes
        df = pd.read_csv(uploaded_file, dtype=dtype_dict)

        # Additional processing for identifier columns
        for col in identifier_cols:
            # Ensure identifiers are treated as strings
            df[col] = df[col].astype(str)
            # Clean up common issues
            df[col] = df[col].str.strip()  # Remove whitespace
            df[col] = df[col].replace('nan', np.nan)  # Handle 'nan' strings

        # Basic column name cleaning
        df.columns = df.columns.str.strip()

        # Try to parse date columns automatically
        for col in df.columns:
            if col not in identifier_cols and any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass

        return df, identifier_cols

    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None, []

def smart_excel_loader(uploaded_file, sheet_name=None):
    """
    Intelligently load Excel with proper data type detection for identifiers
    - Supports selecting a specific sheet
    - Preserves identifier-like columns (e.g., HS codes) as strings
    """
    try:
        # Ensure we can read the file multiple times
        if hasattr(uploaded_file, 'read') and not isinstance(uploaded_file, io.BytesIO):
            # Read once to bytes so we can seek freely
            bytes_data = uploaded_file.read()
        elif isinstance(uploaded_file, io.BytesIO):
            uploaded_file.seek(0)
            bytes_data = uploaded_file.read()
        else:
            # Fallback (e.g., raw bytes)
            bytes_data = uploaded_file

        # Preview read (first 1000 rows) to detect identifier columns
        preview_buffer = io.BytesIO(bytes_data)
        df_preview = pd.read_excel(preview_buffer, sheet_name=sheet_name, nrows=1000)

        # Detect identifier columns
        identifier_cols = detect_identifier_columns(df_preview)

        # Create dtype dictionary to force string types for identifiers
        dtype_dict = {col: str for col in identifier_cols}

        # Full read with proper dtypes
        full_buffer = io.BytesIO(bytes_data)
        df = pd.read_excel(full_buffer, sheet_name=sheet_name, dtype=dtype_dict)

        # Additional processing for identifier columns
        for col in identifier_cols:
            # Ensure identifiers are treated as strings
            df[col] = df[col].astype(str)
            # Clean up common issues
            df[col] = df[col].str.strip()
            df[col] = df[col].replace('nan', np.nan)

        # Basic column name cleaning
        df.columns = df.columns.str.strip()

        # Try to parse date columns automatically (excluding identifiers)
        for col in df.columns:
            if col not in identifier_cols and any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass

        return df, identifier_cols
    except Exception as e:
        st.error(f"Error loading Excel: {str(e)}")
        return None, []


class GenericDataAI:
    """Generic AI assistant for CSV data analysis"""

    def __init__(self):
        self.data_summary = {}
        self.column_insights = {}
        self.identifier_columns = []
        # Load API keys from environment (works for both local .env and Streamlit secrets)
        self.groq_api_key = get_env_var('GROQ_API_KEY')
        

    def analyze_dataset(self, df, identifier_cols=None):
        """Dynamically analyze any dataset to understand its structure and content"""
        if identifier_cols:
            self.identifier_columns = identifier_cols

        analysis = {
            "basic_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            },
            "column_types": {},
            "data_insights": {},
            "sample_data": df.head(3).to_dict('records'),
            "missing_data": df.isnull().sum().to_dict(),
            "numeric_summary": {},
            "categorical_summary": {},
            "identifier_summary": {}
        }

        # Analyze each column
        for col in df.columns:
            dtype = str(df[col].dtype)
            analysis["column_types"][col] = dtype

            # Handle identifier columns specially
            if col in self.identifier_columns:
                value_counts = df[col].value_counts().head(10)
                analysis["identifier_summary"][col] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": value_counts.to_dict(),
                    "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else "N/A",
                    "sample_values": df[col].dropna().head(5).tolist()
                }

            # Numeric columns (excluding identifiers)
            elif df[col].dtype in ['int64', 'float64', 'int32', 'float32'] and col not in self.identifier_columns:
                analysis["numeric_summary"][col] = {
                    "min": float(df[col].min()) if not df[col].empty else 0,
                    "max": float(df[col].max()) if not df[col].empty else 0,
                    "mean": float(df[col].mean()) if not df[col].empty else 0,
                    "std": float(df[col].std()) if not df[col].empty else 0,
                    "unique_count": int(df[col].nunique())
                }

            # Categorical/text columns (excluding identifiers)
            elif (df[col].dtype == 'object' or df[col].dtype.name == 'category') and col not in self.identifier_columns:
                value_counts = df[col].value_counts().head(10)
                analysis["categorical_summary"][col] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": value_counts.to_dict(),
                    "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else "N/A"
                }

            # Date columns (try to detect)
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']) or dtype == 'datetime64[ns]':
                if df[col].dtype == 'object':
                    # Try to parse dates
                    try:
                        parsed_dates = pd.to_datetime(df[col], errors='coerce')
                        if not parsed_dates.isna().all():
                            analysis["data_insights"][f"{col}_date_range"] = {
                                "earliest": str(parsed_dates.min()),
                                "latest": str(parsed_dates.max()),
                                "span_days": (parsed_dates.max() - parsed_dates.min()).days if parsed_dates.notna().any() else 0
                            }
                    except:
                        pass

        self.data_summary = analysis
        return analysis

    def generate_data_context(self, df, question=""):
        """Generate context about the data for AI"""
        if not self.data_summary:
            self.analyze_dataset(df, self.identifier_columns)

        context = f"""
DATASET OVERVIEW:
- Dataset has {self.data_summary['basic_info']['rows']:,} rows and {self.data_summary['basic_info']['columns']} columns
- Memory usage: {self.data_summary['basic_info']['memory_usage']}
- Columns: {', '.join(self.data_summary['basic_info']['column_names'])}

COLUMN TYPES:"""

        for col, dtype in self.data_summary['column_types'].items():
            col_type = "identifier" if col in self.identifier_columns else dtype
            context += f"\\n- {col}: {col_type}"

        # Identifier columns summary
        if self.data_summary['identifier_summary']:
            context += "\\n\\nIDENTIFIER COLUMNS (HS Codes, Product Codes, etc.):"
            for col, stats in self.data_summary['identifier_summary'].items():
                context += f"\\n- {col}: {stats['unique_count']} unique values, most common: '{stats['most_common']}'"
                context += f"\\n  Sample values: {', '.join(map(str, stats['sample_values'][:3]))}"

        context += "\\n\\nNUMERIC COLUMNS SUMMARY:"
        for col, stats in self.data_summary['numeric_summary'].items():
            context += f"\\n- {col}: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}, unique={stats['unique_count']}"

        context += "\\n\\nCATEGORICAL COLUMNS SUMMARY:"
        for col, stats in self.data_summary['categorical_summary'].items():
            top_value = list(stats['top_values'].keys())[0] if stats['top_values'] else 'N/A'
            context += f"\\n- {col}: {stats['unique_count']} unique values, most common: '{top_value}'"

        context += "\\n\\nSAMPLE DATA (first 3 rows):"
        for i, row in enumerate(self.data_summary['sample_data']):
            context += f"\\nRow {i+1}: {row}"

        if any(keyword in question.lower() for keyword in ['trend', 'time', 'date', 'change']):
            context += "\\n\\nDATE/TIME INSIGHTS:"
            for key, info in self.data_summary['data_insights'].items():
                if 'date_range' in key:
                    context += f"\\n- {key}: {info['earliest']} to {info['latest']} ({info['span_days']} days)"

        return context

    def get_ai_response(self, question, df, provider="Groq"):
        """Get AI response for the question using Groq only (simplified)"""
        # Try DataFrame Agent first
        handled, agent_answer = self.dataframe_agent(question, df)
        if handled:
            return agent_answer

        # Use Groq for AI analysis
        return self.get_groq_response(question, df)

    def get_groq_response(self, question, df):
        """Get response using Groq API"""
        if not self.groq_api_key:
            return "Groq API key not found in environment variables. Please add GROQ_API_KEY to your .env file."

        try:
            context = self.generate_data_context(df, question)

            prompt = f"""You are a data analyst. Answer questions about this dataset:

{context}

Question: {question}

Provide specific insights based on the data shown above. Note that identifier columns (like HS codes) are categorical, not numeric. Focus on text-based analysis and insights."""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500,
                    "temperature": 0.2
                }
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"GenAI API error: {response.status_code}. Please check your API key in .env file."

        except Exception as e:
            return f"GenAI error: {str(e)[:100]}..."

    def dataframe_agent(self, question: str, df: pd.DataFrame):
        """
        Lightweight DataFrame agent to handle Excel-like operations via natural language.

        Supports:
        - Filtering: "filter where Country = US and Amount > 1000"
        - Counting: "count rows", "how many rows for Country=US"
        - Grouping: "group by Country and count", "sum Amount by Country"
        - Aggregations: min/max/mean/sum over columns with optional conditions
        - Sorting: "top 10 by Amount", "bottom 5 records"
        - Unique values: "unique values in Country", "distinct categories"
        - Simple display: "show me data", "list columns"

        Returns (handled: bool, answer: str)
        """
        try:
            q = (question or "").strip().lower()
            if len(q) < 3:
                return False, ""

            triggers = [
                "filter", "where", "count", "how many", "group by", "sum", "average", "avg",
                "mean", "min", "max", "top", "bottom", "sort", "largest", "smallest",
                "show", "list", "find", "get", "unique", "distinct"
            ]
            if not any(t in q for t in triggers):
                return False, ""

            def resolve_col(name: str):
                if not name:
                    return None
                key = re.sub(r"[^a-z0-9]", "", str(name).lower())
                for c in df.columns:
                    cand = re.sub(r"[^a-z0-9]", "", str(c).lower())
                    if cand == key or cand.startswith(key) or key in cand:
                        return c
                return None

            def safe_to_markdown(df_subset):
                """Convert DataFrame to markdown with fallback to string if tabulate not available"""
                try:
                    return df_subset.to_markdown(index=False)
                except ImportError:
                    return df_subset.to_string(index=False)

            def parse_conditions(text: str):
                # Handle parentheses for OR groups
                if "(" in text and ")" in text:
                    # Extract OR groups in parentheses
                    or_groups = re.findall(r"\\(([^)]+)\\)", text)
                    clauses, joiners = [], []

                    for group in or_groups:
                        # Parse OR conditions within the group
                        or_tokens = re.split(r"\\s+or\\s+", group)
                        for token in or_tokens:
                            m = re.search(r"([^<>=!]+)\\s*(==|=|>=|<=|>|<|!=|contains|starts with|ends with)\\s*(.+)", token, flags=re.I)
                            if m:
                                col_raw, op, val_raw = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                                col = resolve_col(col_raw)
                                if col:
                                    val = val_raw.strip().strip('\'"')
                                    try:
                                        if isinstance(val, str) and val.lower() in ("true", "false"):
                                            v = True if val.lower() == "true" else False
                                        else:
                                            v = float(val)
                                    except Exception:
                                        v = val
                                    clauses.append((col, op.lower(), v))
                                    if len(clauses) > 1:
                                        joiners.append("or")
                    return clauses, joiners

                # Original logic for simple conditions
                tokens = re.split(r"\\s+(and|or)\\s+", text)
                clauses, joiners = [], []
                for t in tokens:
                    if t in ("and", "or"):
                        joiners.append(t)
                        continue
                    m = re.search(r"([^<>=!]+)\\s*(==|=|>=|<=|>|<|!=|contains|starts with|ends with)\\s*(.+)", t, flags=re.I)
                    if not m:
                        m2 = re.search(r"([^<>=!]+)\\s+(.+)", t)
                        if not m2:
                            continue
                        col_raw, val_raw, op = m2.group(1).strip(), m2.group(2).strip(), "=="
                    else:
                        col_raw, op, val_raw = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                    col = resolve_col(col_raw)
                    if not col:
                        continue
                    val = val_raw.strip().strip('\'"')
                    try:
                        if isinstance(val, str) and val.lower() in ("true", "false"):
                            v = True if val.lower() == "true" else False
                        else:
                            v = float(val)
                    except Exception:
                        v = val
                    clauses.append((col, op.lower(), v))
                return clauses, joiners

            def apply_filter(df0: pd.DataFrame, clauses, joiners):
                if not clauses:
                    return df0

                # Create masks for each condition
                masks = []
                for col, op, v in clauses:
                    s = df0[col]
                    if op in ("=", "=="):
                        masks.append(s.astype(str).str.lower() == str(v).lower())
                    elif op == "!=":
                        masks.append(s.astype(str).str.lower() != str(v).lower())
                    elif op == ">":
                        masks.append(pd.to_numeric(s, errors='coerce') > (v if isinstance(v, (int, float)) else np.nan))
                    elif op == ">=":
                        masks.append(pd.to_numeric(s, errors='coerce') >= (v if isinstance(v, (int, float)) else np.nan))
                    elif op == "<":
                        masks.append(pd.to_numeric(s, errors='coerce') < (v if isinstance(v, (int, float)) else np.nan))
                    elif op == "<=":
                        masks.append(pd.to_numeric(s, errors='coerce') <= (v if isinstance(v, (int, float)) else np.nan))
                    elif op == "contains":
                        masks.append(s.astype(str).str.contains(str(v), case=False, na=False))
                    elif op == "starts with":
                        masks.append(s.astype(str).str.lower().str.startswith(str(v).lower()))
                    elif op == "ends with":
                        masks.append(s.astype(str).str.lower().str.endswith(str(v).lower()))
                    else:
                        masks.append(s.astype(str).str.lower() == str(v).lower())

                if not masks:
                    return df0

                # Combine masks using joiners
                final_mask = masks[0]
                for i in range(1, len(masks)):
                    joiner = joiners[i-1] if i-1 < len(joiners) else "and"
                    if joiner == "or":
                        final_mask = final_mask | masks[i]
                    else:
                        final_mask = final_mask & masks[i]

                return df0[final_mask]

            cond_text = ""
            m_cond = re.search(r"(?:where|filter)\\s+(.+?)(?:\\s+(?:then|and then|group by|sum|count|top|bottom)|\\s*$)", q)
            if m_cond:
                cond_text = m_cond.group(1)

            clauses, joiners = parse_conditions(cond_text) if cond_text else ([], [])
            df_work = apply_filter(df, clauses, joiners) if clauses else df

            if "how many" in q or q.startswith("count") or " count " in q or "give me the count" in q or q.endswith("count"):
                filter_text = " after filter" if clauses and len(clauses) > 0 else ""
                return True, f"Total rows{filter_text}: {len(df_work):,}"

            # Unique/distinct values
            m_unique = re.search(r"(?:unique|distinct)\\s+(?:values?\\s+(?:in\\s+|of\\s+|from\\s+)?)?([a-z0-9 _\\-]+)", q)
            if m_unique:
                unique_col = resolve_col(m_unique.group(1))
                if unique_col:
                    try:
                        unique_vals = df_work[unique_col].dropna().unique()
                        if len(unique_vals) <= 20:
                            return True, f"Unique values in {unique_col}: {', '.join(map(str, unique_vals))}"
                        else:
                            return True, f"Found {len(unique_vals)} unique values in {unique_col}. First 20: {', '.join(map(str, unique_vals[:20]))}"
                    except Exception:
                        pass

            m_group = re.search(r"group by\\s+([a-z0-9 _\\-]+)", q)
            group_col = resolve_col(m_group.group(1)) if m_group else None
            m_agg = re.search(r"(sum|average|avg|mean|min|max)\\s+of\\s+([a-z0-9 _\\-]+)", q)
            agg_func, agg_col = (m_agg.group(1), resolve_col(m_agg.group(2))) if m_agg else (None, None)

            if group_col:
                if agg_col:
                    func_map = {"sum": "sum", "average": "mean", "avg": "mean", "mean": "mean", "min": "min", "max": "max"}
                    func = func_map.get(agg_func or "count", "count")
                    try:
                        res = df_work.groupby(group_col)[agg_col].agg(func).reset_index().head(50)
                        return True, safe_to_markdown(res)
                    except Exception:
                        pass
                try:
                    res = df_work.groupby(group_col).size().reset_index(name='count').head(50)
                    return True, safe_to_markdown(res)
                except Exception:
                    pass

            m_top = re.search(r"top\\s+(\\d+)?\\s*([a-z0-9 _\\-]+)?", q)
            m_bottom = re.search(r"bottom\\s+(\\d+)?\\s*([a-z0-9 _\\-]+)?", q)
            if m_top or m_bottom:
                n = int((m_top or m_bottom).group(1) or 5)
                sort_col = resolve_col(((m_top or m_bottom).group(2) or '').strip())
                if sort_col:
                    sorted_df = df_work.sort_values(by=sort_col, ascending=bool(m_bottom)).head(n)
                    return True, safe_to_markdown(sorted_df)
                return True, safe_to_markdown(df_work.head(n))

            if agg_col:
                try:
                    s = pd.to_numeric(df_work[agg_col], errors='coerce')
                    if agg_func in ("average", "avg", "mean"):
                        val = s.mean()
                    elif agg_func == "sum":
                        val = s.sum()
                    elif agg_func == "min":
                        val = s.min()
                    elif agg_func == "max":
                        val = s.max()
                    else:
                        val = s.count()
                    filter_text = " after filter" if clauses and len(clauses) > 0 else ""
                    return True, f"{agg_func or 'count'} of {agg_col}{filter_text}: {val:.4g}"
                except Exception:
                    pass

            # Handle filter-only queries (without count/aggregation)
            if ("filter" in q or "include only" in q) and clauses and len(clauses) > 0:
                # Show filtered results
                if len(df_work) <= 50:
                    return True, f"Filtered results ({len(df_work)} rows):\\n\\n{safe_to_markdown(df_work)}"
                else:
                    return True, f"Filtered results ({len(df_work)} rows, showing first 20):\\n\\n{safe_to_markdown(df_work.head(20))}"

            # Simple "show me" queries
            if any(phrase in q for phrase in ["show me", "list", "display"]) and not any(t in q for t in ["filter", "where", "group", "sum", "count"]):
                if "columns" in q or "column" in q:
                    return True, f"Available columns: {', '.join(df.columns)}"
                else:
                    return True, safe_to_markdown(df.head(10))

            if any(t in q for t in triggers):
                sample_cols = ", ".join([str(c) for c in list(df.columns)[:6]])
                return True, (
                    "Try: 'filter where Country = US and Amount > 1000 then sum of Amount', "
                    "'group by Country and count', 'unique values in Column', or "
                    f"'show me top 10'. Columns include: {sample_cols}"
                )

            return False, ""
        except Exception as e:
            return True, f"Agent error: {str(e)}"

def create_data_overview(df, ai_assistant, identifier_cols):
    """Create an overview of the loaded dataset"""
    st.subheader("📊 Dataset Overview")

    # Show identifier detection results
    if identifier_cols:
        st.markdown(f"""
        <div class="identifier-warning">
            <strong>🔑 Identifier Columns Detected:</strong><br>
            The following columns are being treated as identifiers (not numeric): <strong>{', '.join(identifier_cols)}</strong><br>
            <em>This includes HS codes, product codes, and other ID fields.</em>
        </div>
        """, unsafe_allow_html=True)

    # Get analysis
    analysis = ai_assistant.analyze_dataset(df, identifier_cols)

    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rows", f"{analysis['basic_info']['rows']:,}")

    with col2:
        st.metric("Total Columns", analysis['basic_info']['columns'])

    with col3:
        numeric_cols = len(analysis['numeric_summary'])
        st.metric("Numeric Columns", numeric_cols)

    with col4:
        categorical_cols = len(analysis['categorical_summary'])
        identifier_cols_count = len(analysis['identifier_summary'])
        st.metric("Categorical + ID Columns", categorical_cols + identifier_cols_count)

    # Data insights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**🔑 Identifier Columns:**")
        if analysis['identifier_summary']:
            for col, stats in list(analysis['identifier_summary'].items())[:5]:
                with st.expander(f"{col} (Identifier)"):
                    st.write(f"Unique values: {stats['unique_count']}")
                    st.write(f"Most common: {stats['most_common']}")
                    st.write(f"Sample values: {', '.join(map(str, stats['sample_values'][:3]))}")
        else:
            st.write("No identifier columns detected.")

    with col2:
        st.write("**📈 Numeric Columns:**")
        if analysis['numeric_summary']:
            for col, stats in list(analysis['numeric_summary'].items())[:5]:
                with st.expander(f"{col}"):
                    st.write(f"Min: {stats['min']:.2f}")
                    st.write(f"Max: {stats['max']:.2f}")
                    st.write(f"Mean: {stats['mean']:.2f}")
                    st.write(f"Unique values: {stats['unique_count']}")
        else:
            st.write("No purely numeric columns found.")

    with col3:
        st.write("**📝 Categorical Columns:**")
        if analysis['categorical_summary']:
            for col, stats in list(analysis['categorical_summary'].items())[:5]:
                with st.expander(f"{col}"):
                    st.write(f"Unique values: {stats['unique_count']}")
                    st.write(f"Most common: {stats['most_common']}")
                    if stats['top_values']:
                        st.write("Top values:")
                        for value, count in list(stats['top_values'].items())[:3]:
                            st.write(f"  • {value}: {count}")
        else:
            st.write("No text categorical columns found.")

    # Missing data analysis
    missing_data = {col: missing for col, missing in analysis['missing_data'].items() if missing > 0}
    if missing_data:
        st.write("**⚠️ Missing Data:**")
        missing_df = pd.DataFrame([
            {"Column": col, "Missing Count": missing, "Missing %": f"{(missing/len(df)*100):.1f}%"}
            for col, missing in missing_data.items()
        ])
        st.dataframe(missing_df, use_container_width=True)

def create_ai_chat_section(df, identifier_cols):
    """Create the AI chat interface for data analysis"""
    st.subheader("🤖 Chat with Your Data")

    # Initialize AI assistant
    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = GenericDataAI()

    ai_assistant = st.session_state.ai_assistant
    ai_assistant.identifier_columns = identifier_cols

    # Always use Groq as the provider (simplified)
    ai_provider = "Groq"

    # Dynamic example questions based on data
    if df is not None:
        columns = df.columns.tolist()
        numeric_cols = [col for col in df.select_dtypes(include=[np.number]).columns.tolist() if col not in identifier_cols]
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

        st.write("**💡 Suggested Questions for Your Data:**")

        example_questions = [
            "What's the overview of this dataset?",
            f"Analyze the distribution of {numeric_cols[0] if numeric_cols else 'numeric columns'}",
            f"What are the top values in {identifier_cols[0] if identifier_cols else categorical_cols[0] if categorical_cols else 'categorical columns'}?",
            "What correlations exist between numeric columns?",
            "Analyze the relationship between columns",
            f"What are the most common HS codes?" if any('hs' in col.lower() for col in identifier_cols) else "What are the most common identifier values?"
        ]

        cols = st.columns(3)
        for i, question in enumerate(example_questions):
            with cols[i % 3]:
                if st.button(f"📋 {question[:25]}...", key=f"example_{i}", help=question):
                    st.session_state.current_question = question

    # Chat interface
    st.markdown("---")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Question input
    user_question = st.text_area(
        "🎯 Ask anything about your data:",
        value=st.session_state.get('current_question', ''),
        height=80,
        placeholder="e.g., What are the top HS codes? Analyze correlations, Describe the relationship between X and Y"
    )

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ask_button = st.button("🤖 Analyze with AI", type="primary")

    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.current_question = ""
            st.rerun()

    with col3:
        if st.button("📊 Quick Stats"):
            st.session_state.current_question = "Give me a comprehensive overview and key insights about this dataset"

    # Process question
    if ask_button and user_question.strip():
        with st.spinner(f"🤔 AI is analyzing your data..."):
            try:
                response = ai_assistant.get_ai_response(user_question, df, "Groq")

                # Add to chat history
                st.session_state.chat_history.append({
                    "question": user_question,
                    "answer": response,
                    "provider": "Groq",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

                st.session_state.current_question = ""
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("💬 Analysis History")

        for chat in reversed(st.session_state.chat_history[-3:]):  # Show last 3
            # Process the answer to replace newlines with HTML breaks
            processed_answer = chat['answer'].replace('\\n', '<br>')

            st.markdown(f"""
            <div class="user-message">
                <strong>🙋 You ({chat['timestamp']}):</strong><br>
                {chat['question']}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="ai-message">
                <strong>🤖 AI Assistant:</strong><br>
                {processed_answer}
            </div>
            """, unsafe_allow_html=True)

def create_quick_viz(df, identifier_cols):
    """Create quick visualizations for any dataset"""
    st.subheader("📈 Quick Visualizations")

    # Separate true numeric columns from identifiers
    numeric_cols = [col for col in df.select_dtypes(include=[np.number]).columns.tolist() if col not in identifier_cols]
    categorical_cols = [col for col in df.select_dtypes(include=['object']).columns.tolist() if col not in identifier_cols]
    all_categorical = categorical_cols + identifier_cols
    all_columns = list(df.columns)

    if not numeric_cols and not all_categorical:
        st.warning("No suitable columns found for visualization.")
        return

    # Create sections for visualizations
    st.markdown("### 📊 Individual Column Analysis")
    col1, col2 = st.columns(2)

    with col1:
        if all_categorical:
            st.write("**Top Values Distribution**")
            selected_cat_col = st.selectbox("Select categorical/identifier column:", all_categorical, key="cat_viz")

            if selected_cat_col:
                value_counts = df[selected_cat_col].value_counts().head(15)
                fig = px.bar(
                    x=value_counts.values,
                    y=value_counts.index,
                    orientation='h',
                    title=f"Top 15 values in {selected_cat_col}",
                    labels={'x': 'Count', 'y': selected_cat_col}
                )
                if selected_cat_col in identifier_cols:
                    fig.update_layout(title=f"Top 15 {selected_cat_col} (Identifier Column)")
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        if numeric_cols:
            st.write("**Numeric Distribution**")
            selected_num_col = st.selectbox("Select numeric column:", numeric_cols, key="num_viz")

            if selected_num_col:
                fig = px.histogram(
                    df,
                    x=selected_num_col,
                    title=f"Distribution of {selected_num_col}",
                    nbins=30
                )
                st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap if multiple numeric columns
    if len(numeric_cols) > 1:
        st.markdown("---")
        st.markdown("### 🔥 Correlation Analysis")
        st.write("**Correlation Matrix (Numeric Columns Only)**")
        corr_matrix = df[numeric_cols].corr()
        fig = px.imshow(
            corr_matrix,
            title="Correlation Matrix of Numeric Columns",
            aspect="auto",
            color_continuous_scale="RdBu",
            zmin=-1, zmax=1
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🤖 AI-Powered CSV Data Analyzer</h1>', unsafe_allow_html=True)

    # File upload
    st.sidebar.title("📂 Upload Your Data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])

    df = None
    identifier_cols = []

    if uploaded_file is not None:
        filename = getattr(uploaded_file, 'name', '').lower()
        is_excel = filename.endswith('.xlsx') or filename.endswith('.xls')
        try:
            if is_excel:
                # Read bytes to allow repeated access and sheet discovery
                bytes_data = uploaded_file.getvalue()
                with st.sidebar:
                    try:
                        xl = pd.ExcelFile(io.BytesIO(bytes_data))
                        sheet_names = xl.sheet_names if xl.sheet_names else [None]
                    except Exception:
                        sheet_names = [None]
                    # Persist user selection across reruns
                    if 'excel_sheet' not in st.session_state or st.session_state.excel_sheet not in sheet_names:
                        st.session_state.excel_sheet = sheet_names[0]
                    st.session_state.excel_sheet = st.selectbox(
                        "Select sheet",
                        options=sheet_names,
                        index=sheet_names.index(st.session_state.excel_sheet) if st.session_state.excel_sheet in sheet_names else 0,
                        help="Choose which worksheet to analyze"
                    )
                df, identifier_cols = smart_excel_loader(io.BytesIO(bytes_data), sheet_name=st.session_state.excel_sheet)
            else:
                df, identifier_cols = smart_csv_loader(uploaded_file)
        except Exception as e:
            st.sidebar.error(f"Failed to load file: {str(e)}")
            df, identifier_cols = None, []

        if df is not None:
            st.sidebar.success(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            if identifier_cols:
                st.sidebar.info(f"🔑 Detected {len(identifier_cols)} identifier column(s)")

    if df is None:
        st.warning("Please upload a CSV or Excel file to begin analysis.")
        st.markdown("""
        ### 🚀 What this tool does:
        - **Upload any CSV or Excel file** and instantly start analyzing it
        - **Smart identifier detection** - HS codes, product codes, etc. are treated correctly
        - **Chat with your data** using AI powered by Groq
        - **Get automatic insights** about patterns, trends, and anomalies
        - **Generate visualizations** when you ask for them
        - **🔍 Business contact research** - AI-powered web scraping to find phone, email, website, and address
        - **No hardcoding** - works with any dataset automatically

        ### 💡 Example questions you can ask:
        - "What are the top HS codes?" (analyze identifiers)
        - "Analyze the distribution of values" (for numeric data)
        - "What correlations exist between columns?"
        - "Describe the distribution patterns"
        - "Analyze trends over time"
        """)
        return

    # Initialize AI assistant
    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = GenericDataAI()

    # Set identifier columns in AI assistant
    st.session_state.ai_assistant.identifier_columns = identifier_cols

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Chat",
        "📊 Data Overview", 
        "📈 Quick Viz",
        "📊 Data Explorer"
    ])

    # Always render all content - Streamlit handles tab display
    with tab1:
        create_ai_chat_section(df, identifier_cols)

    with tab2:
        create_data_overview(df, st.session_state.ai_assistant, identifier_cols)

    with tab3:
        create_quick_viz(df, identifier_cols)

    with tab4:
        create_data_explorer(df, identifier_cols)

if __name__ == "__main__":
    main()
