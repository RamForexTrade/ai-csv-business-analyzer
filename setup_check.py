#!/usr/bin/env python3
"""
Local Development Setup Verification Script
Run this to verify your local environment is properly configured
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly',
        'numpy',
        'dotenv',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment_file():
    """Check if .env file exists and has required keys"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Create .env file with your API keys:")
        print("   GROQ_API_KEY=your_groq_key")
        print("   TAVILY_API_KEY=your_tavily_key")
        return False
    
    print("✅ .env file exists")
    
    # Check if keys are present (without showing values)
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    if groq_key and len(groq_key) > 10:
        print("✅ GROQ_API_KEY configured")
    else:
        print("❌ GROQ_API_KEY missing or invalid")
        return False
    
    if tavily_key and len(tavily_key) > 10:
        print("✅ TAVILY_API_KEY configured")
    else:
        print("❌ TAVILY_API_KEY missing or invalid")
        return False
    
    return True

def main():
    """Run all checks"""
    print("🔍 AI CSV Business Analyzer - Local Development Setup Check")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 60)
    print("📊 SETUP SUMMARY:")
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 LOCAL DEVELOPMENT ENVIRONMENT READY!")
        print("🚀 You can now run: streamlit run ai_csv_analyzer.py")
    else:
        print("\n⚠️  Please fix the failing checks above before continuing")

if __name__ == "__main__":
    main()
