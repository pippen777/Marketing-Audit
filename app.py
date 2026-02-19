import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

# --- APP CONFIGURATION ---
st.set_page_config(page_title="STELLAR Diagnostic Engine", layout="wide", page_icon="🚀")

# --- SIDEBAR: API SETTINGS ---
with st.sidebar:
    st.header("🔑 API Settings")
    st.markdown("Enter your OpenRouter API key to enable automated LLM analysis.")
    openrouter_api_key = st.text_input("OpenRouter API Key", type="password")
    
    # Model selection (Defaults to a free model on OpenRouter, but you can switch to premium ones)
    llm_model = st.selectbox(
        "Select LLM Model", 
        [
            "meta-llama/llama-3-8b-instruct:free", 
            "anthropic/claude-3-haiku", 
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5"
        ]
    )
    st.markdown("---")
    st.markdown("**Note:** The LLM will automatically synthesize the extracted data into a Creative Briefing.")

# --- TITLE ---
st.title("🚀 STELLAR Method: 2026 Automated Diagnostic")
st.markdown("Extract Technical SEO, AEO/GEO readiness, and Core Web Vitals, then generate a strategic summary.")

# --- HELPER FUNCTIONS ---
def check_url_exists(base_url, path):
    url = f"{base_url.rstrip('/')}/{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, url
        return False, url
    except:
        return False, url

def get_pagespeed_vitals(url):
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile"
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        
        lighthouse = data.get('lighthouseResult', {})
        categories = lighthouse.get('categories', {})
        performance_score = categories.get('performance', {}).get('score', 0) * 100
        
        metrics = lighthouse.get('audits', {})
        lcp = metrics.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        cls = metrics.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')
        
        return {"score": round(performance_score), "lcp": lcp, "cls": cls}
    except Exception as e:
        return {"score": "Error", "lcp": "Error", "cls": "Error"}

def scrape_seo_basics(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string.strip() if soup.title else "Missing Title"
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag else "Missing Meta Description"
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else "Missing H1"
        
        return {"title": title, "desc": desc, "h1": h1}
    except:
        return {"title": "Error", "desc": "Error", "h1": "Error"}

def generate_llm_summary(api_key, model, data_dict):
    """Sends the scraped data to OpenRouter to generate the STELLAR Executive Summary"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # The "Designity" Style Prompt
    prompt = f"""
    You are an expert Digital Marketing Expert (DME) partnering with a Creative Director. 
    Review this website data based on the 2026 STELLAR framework.
    
    DATA EXTRACTED:
    - Target URL: {data_dict['url']}
    - Mobile Speed Score: {data_dict['score']}/100
    - Largest Contentful Paint (LCP): {data_dict['lcp']} (Standard: < 2.5s)
    - AI Sitemap (llms.txt) Present: {data_dict['llms']}
    - H1 (Value Prop): {data_dict['h1']}
    - Title Tag: {data_dict['title']}
    - Meta Description: {data_dict['desc']}

    TASK: Write a highly actionable, 3-paragraph Executive Summary for the Creative Director to present to the client.
    1. Paragraph 1: Evaluate the "Brand Soul" and Value Proposition based on their H1 and Meta Description. Are they selling "features" or "benefits"?
    2. Paragraph 2: Identify an "Integration Conflict." (e.g., If LCP is slow, explain how it kills the mobile UX and wastes paid ad spend). Address their GEO/AI-readiness based on the llms.txt finding.
    3. Paragraph 3: Provide a clear "Creative Briefing" directive for Phase 1 (Foundation) to fix these specific issues.

    Tone: Candid, strategic, authoritative, and direct. Use bullet points for the Phase 1 directive.
    """
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ Error connecting to OpenRouter: {str(e)}"


# --- MAIN APP UI ---
target_url = st.text_input("Enter Target URL (e.g., https://example.com):", placeholder="https://...")

if st.button("Run Complete STELLAR Audit"):
    if not target_url.startswith("http"):
        st.error("Please include https:// in your URL.")
    else:
        with st.spinner("Initiating STELLAR diagnostic scan... (This takes ~15 seconds to pull Google PageSpeed data)"):
            
            # 1. GEO / AEO Readiness
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

            # 2. Technical Domain
            st.header("2. Technical Performance (Mobile)")
            vitals = get_pagespeed_vitals(target_url)
            
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(label="Mobile Speed Score", value=f"{vitals['score']} / 100")
            with col5:
                st.metric(label="Largest Contentful Paint (LCP)", value=vitals['lcp'])
            with col6:
                st.metric(label="Cumulative Layout Shift (CLS)", value=vitals['cls'])

            # 3. Language & Strategy
            st.header("3. Language & Strategy Signals")
            seo_data = scrape_seo_basics(target_url)
            
            st.text_area("Page Title (L1 - Headline Check)", value=seo_data['title'], height=68)
            st.text_area("Meta Description (L2 - CTA / Hook)", value=seo_data['desc'], height=68)
            st.text_area("Primary H1 (S1 - Value Prop)", value=seo_data['h1'], height=68)
            
            st.success("✅ Diagnostic Data Extraction Complete.")

            # 4. LLM Synthesis via OpenRouter
            st.header("🧠 Automated LLM Synthesis (Creative Brief)")
            if not openrouter_api_key:
                st.warning("⚠️ Enter your OpenRouter API Key in the left sidebar to generate the AI Executive Summary.")
            else:
                with st.spinner(f"Generating strategy using {llm_model}..."):
                    
                    # Compile data dict for the LLM
                    extracted_data = {
                        "url": target_url,
                        "score": vitals['score'],
                        "lcp": vitals['lcp'],
                        "cls": vitals['cls'],
                        "llms": "Found" if has_llms else "Missing",
                        "h1": seo_data['h1'],
                        "title": seo_data['title'],
                        "desc": seo_data['desc']
                    }
                    
                    llm_response = generate_llm_summary(openrouter_api_key, llm_model, extracted_data)
                    
                    st.markdown("### STELLAR Executive Summary")
                    st.info(llm_response)
