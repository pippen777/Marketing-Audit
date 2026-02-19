import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- APP CONFIGURATION ---
st.set_page_config(page_title="STELLAR 2026 Diagnostic Engine", layout="wide")
st.title("🚀 STELLAR Method: 2026 Automated Diagnostic")
st.markdown("Enter a URL to automatically extract Technical SEO, AEO/GEO readiness, and Core Web Vitals.")

# --- HELPER FUNCTIONS ---
def check_url_exists(base_url, path):
    """Checks if a specific file exists on the server (like llms.txt)"""
    url = f"{base_url.rstrip('/')}/{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, url
        return False, url
    except:
        return False, url

def get_pagespeed_vitals(url):
    """Fetches real Core Web Vitals from the free Google PageSpeed API"""
    # Using the free endpoint (no API key needed for basic usage)
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile"
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        
        # Extracting metrics safely
        lighthouse = data.get('lighthouseResult', {})
        categories = lighthouse.get('categories', {})
        performance_score = categories.get('performance', {}).get('score', 0) * 100
        
        metrics = lighthouse.get('audits', {})
        lcp = metrics.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        cls = metrics.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')
        
        return {
            "score": round(performance_score),
            "lcp": lcp,
            "cls": cls
        }
    except Exception as e:
        return {"score": "Error", "lcp": "Error", "cls": "Error"}

def scrape_seo_basics(url):
    """Scrapes Title, Description, and H1 for the Language/Leads Domain"""
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "Missing Title"
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'] if desc_tag else "Missing Meta Description"
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else "Missing H1"
        
        return {"title": title, "desc": desc, "h1": h1}
    except:
        return {"title": "Error", "desc": "Error", "h1": "Error"}


# --- MAIN APP UI ---
target_url = st.text_input("Enter Target URL (e.g., https://example.com):", placeholder="https://...")

if st.button("Run STELLAR Audit"):
    if not target_url.startswith("http"):
        st.error("Please include https:// in your URL.")
    else:
        with st.spinner("Initiating STELLAR diagnostic scan..."):
            
            # 1. GEO / AEO Readiness (AI Sitemaps)
            st.header("1. GEO / AI-Readiness (AEO)")
            col1, col2, col3 = st.columns(3)
            
            has_llms, llms_url = check_url_exists(target_url, "llms.txt")
            has_robots, robots_url = check_url_exists(target_url, "robots.txt")
            has_sitemap, sitemap_url = check_url_exists(target_url, "sitemap.xml")
            
            with col1:
                st.metric(label="AI Sitemap (llms.txt)", value="Found ✅" if has_llms else "Missing ❌")
            with col2:
                st.metric(label="Robots.txt", value="Found ✅" if has_robots else "Missing ❌")
            with col3:
                st.metric(label="Standard Sitemap", value="Found ✅" if has_sitemap else "Missing ❌")

            # 2. Technical Domain (Core Web Vitals)
            st.header("2. Technical Performance (Mobile)")
            st.info("Fetching live data from Google PageSpeed Insights API...")
            
            vitals = get_pagespeed_vitals(target_url)
            
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(label="Mobile Speed Score", value=f"{vitals['score']} / 100")
            with col5:
                st.metric(label="Largest Contentful Paint (LCP)", value=vitals['lcp'], delta="Target: < 2.5s", delta_color="inverse")
            with col6:
                st.metric(label="Cumulative Layout Shift (CLS)", value=vitals['cls'])

            # 3. Strategy & Language (Basic SEO Extraction)
            st.header("3. Language & Strategy Signals")
            seo_data = scrape_seo_basics(target_url)
            
            st.text_area("Page Title (L1 - Headline Check)", value=seo_data['title'], height=68)
            st.text_area("Meta Description (L2 - CTA / Hook)", value=seo_data['desc'], height=68)
            st.text_area("Primary H1 (S1 - Value Prop)", value=seo_data['h1'], height=68)
            
            st.success("✅ Diagnostic Data Extraction Complete. Ready for LLM Synthesis.")
            
            # Future integration placeholder
            st.markdown("---")
            st.markdown("**Next Step for App Development:** Connect an LLM API (like OpenAI or Gemini) to pass this extracted data and automatically generate the 6-Month CaaS Roadmap.")
