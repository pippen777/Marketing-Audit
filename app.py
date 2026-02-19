import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

# --- APP CONFIGURATION ---
st.set_page_config(page_title="STELLAR Competitive Engine", layout="wide", page_icon="🚀")

# --- SIDEBAR: API SETTINGS ---
with st.sidebar:
    st.header("🔑 API Settings")
    st.markdown("Enter your OpenRouter API key for the Automated Strategy Brief.")
    openrouter_api_key = st.text_input("OpenRouter API Key", type="password")
    
    llm_model = st.selectbox(
        "Select LLM Model", 
        [
            "meta-llama/llama-3-8b-instruct:free", 
            "anthropic/claude-3-haiku", 
            "openai/gpt-4o-mini"
        ]
    )

# --- HEADER ---
st.title("🚀 STELLAR Method: Competitive Analysis Engine")
st.markdown("Instantly compare your client against 3 competitors to find messaging gaps and AI-readiness.")

# --- INPUT SECTION ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Target Client")
        target_url = st.text_input("Client URL:", placeholder="https://client.com")
    with col2:
        st.subheader("🛡️ Competitors")
        comp1_url = st.text_input("Competitor 1 URL:", placeholder="https://comp1.com")
        comp2_url = st.text_input("Competitor 2 URL:", placeholder="https://comp2.com")
        comp3_url = st.text_input("Competitor 3 URL:", placeholder="https://comp3.com")

# --- HELPER FUNCTIONS ---
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def check_file(base_url, path):
    """Checks if a file exists (like llms.txt)"""
    url = f"{base_url.rstrip('/')}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        return "✅ Found" if response.status_code == 200 else "❌ Missing"
    except:
        return "⚠️ Error"

def scrape_seo_basics(url):
    """Scrapes Title, Description, and H1"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string.strip() if soup.title and soup.title.string else "N/A"
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else "N/A"
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else "N/A"
        
        return title, desc, h1
    except:
        return "Error", "Error", "Error"

def analyze_site(url, role):
    """Runs the full suite for a single URL"""
    llms = check_file(url, "llms.txt")
    robots = check_file(url, "robots.txt")
    sitemap = check_file(url, "sitemap.xml")
    title, desc, h1 = scrape_seo_basics(url)
    
    return {
        "Role": role,
        "URL": url,
        "llms.txt (AI)": llms,
        "robots.txt": robots,
        "sitemap.xml": sitemap,
        "H1 (Value Prop)": h1,
        "Title Tag": title,
        "Meta Description": desc
    }

def generate_llm_summary(api_key, model, all_data):
    """Sends competitive data to LLM for strategic analysis"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
prompt = f"""
    You are an elite Digital Marketing Expert (DME) at a top agency, partnering with a Creative Director.
    Review this competitive landscape data based on the STELLAR framework.
    
    DATA (JSON Format):
    {json.dumps(all_data, indent=2)}

    TASK: Write a highly actionable, 3-paragraph Competitive Executive Summary.
    
    GUARDRAILS (STRICT):
    - NEVER use generic marketing buzzwords like "Elevate", "Tailored", "Synergy", or "Transform".
    - If suggesting copy, make it punchy, benefit-driven, and focused on revenue/growth.
    - If the client has an llms.txt file, frame it as a BACKEND technical advantage for Generative Engine Optimization (GEO). Do NOT suggest adding "AI" to their frontend marketing copy.
    - CTAs must be low-friction and action-oriented (e.g., "Get Your Free Audit", not "Learn More").

    1. Paragraph 1 (The Landscape): Compare the Target Client's H1 and Meta Description against the competitors. Who has the strongest "Benefit-Focus"? Point out if competitors have missing or broken SEO tags (like missing H1s).
    2. Paragraph 2 (The White Space): Identify a strategic messaging gap the client can exploit to stand out. 
    3. Paragraph 3 (Creative Directive): Provide a bulleted "Phase 1 Creative Brief" telling the copy and design team exactly how to update the Client's homepage Hero section to beat these competitors.

    Tone: Candid, authoritative, direct, and expert-level.
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

# --- MAIN EXECUTION ---
if st.button("Run Competitive Landscape Audit", type="primary"):
    urls_to_check = [url for url in [target_url, comp1_url, comp2_url, comp3_url] if url.strip()]
    
    if not target_url:
        st.error("⚠️ Please enter a Target Client URL.")
    elif len(urls_to_check) < 2:
        st.warning("⚠️ Enter at least 1 competitor URL for a true comparison.")
    else:
        with st.spinner("Scraping target and competitor websites..."):
            
            # Gather Data
            results = []
            roles = ["🎯 Target Client", "🛡️ Competitor 1", "🛡️ Competitor 2", "🛡️ Competitor 3"]
            
            for i, url in enumerate(urls_to_check):
                if not url.startswith("http"):
                    url = "https://" + url
                data = analyze_site(url, roles[i])
                results.append(data)
            
            df = pd.DataFrame(results)
            
            st.success("✅ Extraction Complete.")
            
            # --- DISPLAY 1: TECHNICAL & GEO READINESS ---
            st.header("1. Technical & AI Readiness (GEO)")
            st.markdown("Are the competitors optimizing for AI answer engines?")
            tech_df = df[["Role", "URL", "llms.txt (AI)", "robots.txt", "sitemap.xml"]]
            st.dataframe(tech_df, use_container_width=True, hide_index=True)
            
            # --- DISPLAY 2: MESSAGING COMPARISON ---
            st.header("2. Strategic Messaging Matrix")
            st.markdown("Side-by-side comparison of the primary 'Hooks'.")
            
            cols = st.columns(len(results))
            for i, res in enumerate(results):
                with cols[i]:
                    st.info(f"**{res['Role']}**\n\n{res['URL']}")
                    st.markdown("**H1 (Hero Hook):**")
                    st.write(f"*{res['H1 (Value Prop)']}*")
                    st.markdown("**Title Tag:**")
                    st.write(f"*{res['Title Tag']}*")
                    st.markdown("**Meta Description:**")
                    st.caption(res['Meta Description'])
            
            # --- DISPLAY 3: LLM SYNTHESIS ---
            st.header("🧠 Automated Strategy Brief")
            if not openrouter_api_key:
                st.warning("⚠️ Enter your OpenRouter API Key to generate the Competitive Strategy Brief.")
            else:
                with st.spinner("Analyzing competitive white space..."):
                    llm_response = generate_llm_summary(openrouter_api_key, llm_model, results)
                    st.markdown("### STELLAR Competitive Analysis")
                    st.success(llm_response)
