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
        
        # MANUAL OVERRIDE (For bot-blocking sites)
        with st.expander("🛠️ Advanced: Manual HTML Override (Bypass Bot Blockers)"):
            st.markdown("If the target site blocks scrapers (returns 'Error'), paste the page's raw HTML here.")
            target_html = st.text_area("Paste Raw HTML source code here:")
            
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

def scrape_seo_basics(url, raw_html=""):
    """Scrapes Title, Description, and H1 either from a URL or raw HTML"""
    try:
        # If raw HTML is provided, bypass the request and parse the text directly
        if raw_html.strip():
            html_content = raw_html
        else:
            response = requests.get(url, headers=HEADERS, timeout=5)
            html_content = response.text
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = soup.title.string.strip() if soup.title and soup.title.string else "N/A"
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else "N/A"
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else "N/A"
        
        return title, desc, h1
    except:
        return "Error", "Error", "Error"

def analyze_site(url, role, raw_html=""):
    """Runs the full suite for a single URL"""
    llms = check_file(url, "llms.txt")
    robots = check_file(url, "robots.txt")
    sitemap = check_file(url, "sitemap.xml")
    
    # Pass the raw HTML to the scraper if it exists
    title, desc, h1 = scrape_seo_basics(url, raw_html)
    
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
    Review this competitive landscape data based on the 2026 STELLAR framework.
    
    DATA (JSON Format):
    {json.dumps(all_data, indent=2)}

    TASK: Write a highly actionable Competitive Executive Summary. 
    
    STRICT GUARDRAILS FOR OUTPUT:
    - NEVER use generic marketing buzzwords like "Elevate", "Tailored", "Synergy", or "Transform".
    - You must cite authoritative 2025/2026 Conversion Rate Optimization (CRO) best practices (e.g., CXL, Nielsen Norman Group, HubSpot) to justify your creative decisions.
    
    FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

    ### 1. The Landscape & The White Space
    [Write 1 paragraph comparing the Target Client's messaging to the competitors. Identify the strategic gap the client can exploit to stand out. Note any broken SEO/GEO tags among competitors.]

    ### 2. Phase 1 Creative Brief (Homepage Hero Redesign)
    Provide the redesign directives for the Target Client using this exact structure:

    **Headline (H1)**
    * **Current:** [Insert Client's Current H1]
    * **Proposed:** [Write a punchy, benefit-driven H1 focused on revenue/growth/solutions]
    * **Strategic Rationale:** [Explain the psychology behind the change. Cite a UX/CRO best practice, such as CXL's "Clarity trumps persuasion" or Nielsen Norman Group's scanning behaviors.]

    **Subheadline (H2)**
    * **Current:** [Insert Client's Current Meta Description / Subhead]
    * **Proposed:** [Write a 1-2 sentence subhead that handles objections and expands on the H1]
    * **Strategic Rationale:** [Explain why this reduces bounce rate using industry best practices.]

    **Call to Action (CTA)**
    * **Current:** [Identify the implied or missing CTA]
    * **Proposed:** [Write a high-value, low-friction CTA. e.g., "Get Your Free Audit" instead of "Learn More"]
    * **Strategic Rationale:** [Explain how action-oriented, first-person CTAs reduce friction and increase CTR.]
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
                
                # If it's the target client, pass the raw HTML (if provided)
                if roles[i] == "🎯 Target Client":
                    data = analyze_site(url, roles[i], raw_html=target_html)
                else:
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
