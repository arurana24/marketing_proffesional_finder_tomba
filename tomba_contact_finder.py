import streamlit as st
import pandas as pd
import requests
import time
import random
from urllib.parse import urlparse
from io import BytesIO
from duckduckgo_search import DDGS

# ==========================================
# PAGE CONFIGURATIONS & INTERFACE
# ==========================================
st.set_page_config(
    page_title="India Influencer Marketing Finder",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 India Influencer Marketing Lead Finder")
st.markdown("Combines specialized B2B directory lookups with deep open-source web indexing to isolate target leads.")
st.markdown("---")

# ==========================================
# CORE EXTRACTION REQUISITES
# ==========================================
def clean_domain(input_string):
    """Strips away protocols, www, sub-directories, and spacing safely"""
    raw_string = str(input_string).strip().lower()
    if not raw_string.startswith(('http://', 'https://')):
        raw_string = 'http://' + raw_string
    try:
        parsed_url = urlparse(raw_string)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return input_string

def fetch_fallback_public_leads(company_name, target_domain, status_container, existing_emails):
    """Mines public search indexes natively using direct vector array parsing"""
    status_container.info(f"🔄 Deploying open-source search scraper engine for: **{company_name}**...")
    keyword_filters = ["Marketing", "Influencer", "Manager", "Founder", "Partnerships"]
    fallback_leads = []
    
    try:
        with DDGS() as ddgs:
            for keyword in keyword_filters:
                query = f"site:linkedin.com/in/ {company_name} India {keyword}"
                time.sleep(random.uniform(2.0, 3.5))  # Paced intervals to limit IP flagging risks
                
                try:
                    search_results = ddgs.text(query, max_results=15)
                    
                    # FIXED: Fixed indentation error context logic constraints here
                    if not search_results:
                        continue
                        
                    for item in search_results:
                        profile_url = item.get("href", "").split("?")[0]
                        raw_title = item.get("title", "")
                        
                        if "linkedin.com/in/" not in profile_url:
                            continue
                            
                        parsed_title = raw_title.split("-")
                        name = parsed_title[0].replace("| LinkedIn", "").replace("...", "").strip() if len(parsed_title) > 0 else "Team Member"
                        designation = parsed_title[1].strip() if len(parsed_title) > 1 else f"{keyword} Associate"
                        
                        # Clean special layout characters from Name elements
                        name = name.split(",")[0].split("|")[0].strip()
                        
                        # Calculate mathematical email prediction formulas
                        email_prefix = name.lower().replace(" ", ".")
                        clean_company = company_name.lower().replace(" ", "").replace(".com", "")
                        guessed_email = f"{email_prefix}@{clean_company}.com"
                        
                        if guessed_email not in existing_emails:
                            existing_emails.add(guessed_email)
                            fallback_leads.append({
                                "Name": name,
                                "Designation": designation,
                                "Company": company_name.title(),
                                "Corporate Email": guessed_email,
                                "LinkedIn URL": profile_url,
                                "Source": "Public Index Scraper Fallback"
                            })
                except Exception:
                    continue
    except Exception as e:
        status_container.warning(f"⚠️ Scraping engine warning skipped: {str(e)}")
        
    return fallback_leads

def fetch_all_possible_contacts(company_domain, api_key, status_container):
    target_domain = clean_domain(company_domain)
    company_name = target_domain.split('.')[0]
    
    all_compiled_leads = []
    existing_emails = set()
    india_keywords = ["india", "mumbai", "delhi", "bengaluru", "bangalore", "pune", "hyderabad", "chennai", "gurugram", "gurgaon", "noida"]
    
    current_page = 1
    organization_name = company_name.title()
    
    # Check if domain uses an explicit Indian extension (.in, .co.in, etc.)
    is_indian_tld = target_domain.endswith(('.in', '.co.in', '.net.in', '.org.in', '.ind.in'))
    
    # --- PHASE 1: TOMBA API PIPELINE ---
    if api_key:
        status_container.info(f"📡 Phase 1/2: Querying structural API registries for **{target_domain}**")
        while True:
            url = f"https://api.tomba.io/v1/domain-search?domain={target_domain}&page={current_page}"
            headers = {
                "X-Tomba-Key": api_key,
                "Accept": "application/json"
            }
            try:
                time.sleep(0.6)
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code in [400, 401, 403] or response.status_code != 200:
                    break
                    
                data = response.json().get("data", {})
                emails_data = data.get("emails", [])
                
                if not emails_data:
                    break
                    
                for contact in emails_data:
                    raw_position = contact.get("position") or "Executive / Team Member"
                    first = contact.get("first_name") or ""
                    last = contact.get("last_name") or ""
                    full_name = f"{first} {last}".strip() or "Company Associate"
                    email_val = contact.get("email", "N/A")
                    
                    # Apply geolocation safety checks dynamically
                    is_india = False
                    if is_indian_tld or any(brand in target_domain for brand in ["mcaffeine", "beyoung", "nykaa", "mamaearth"]):
                        is_india = True
                    else:
                        if contact.get("country") and "in" in str(contact["country"]).lower():
                            is_india = True
                        if any(kw in raw_position.lower() for kw in india_keywords):
                            is_india = True
                            
                    if is_india and email_val not in existing_emails:
                        existing_emails.add(email_val)
                        all_compiled_leads.append({
                            "Name": full_name,
                            "Designation": raw_position,
                            "Company": organization_name,
                            "Corporate Email": email_val,
                            "LinkedIn URL": contact.get("linkedin") if contact.get("linkedin") else "N/A",
                            "Source": f"Tomba.io API (Page {current_page})"
                        })
                current_page += 1
            except Exception:
                break
                
    # --- PHASE 2: FALLBACK UNBLOCKED SEARCH SWEEP ---
    fallback_records = fetch_fallback_public_leads(company_name, target_domain, status_container, existing_emails)
    all_compiled_leads.extend(fallback_records)
    
    status_container.success(f"🏁 Processing Matrix Complete! Compiled {len(all_compiled_leads)} unique rows cleanly.")
    return all_compiled_leads

# ==========================================
# STREAMLIT CONTROL PANEL SIDEBAR
# ==========================================
st.sidebar.header("🔑 Authentication Setup")
user_api_key = st.sidebar.text_input(
    "Tomba.io Private API Key", 
    type="password", 
    help="Optional parameter. Leave blank to bypass directory networks and use open web mining directly."
)
target_company = st.sidebar.text_input("Company Domain", placeholder="e.g., mcaffeine.com, beyoung.in")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Output Configuration Filters")
show_email = st.sidebar.checkbox("Show Corporate Email", value=True)
show_designation = st.sidebar.checkbox("Show Designation", value=True)
show_source = st.sidebar.checkbox("Show Lead Engine Source Tag", value=True)
show_linkedin = st.sidebar.checkbox("Show LinkedIn Profile Link", value=True)

# ==========================================
# MAIN EXECUTION ENGINE
# ==========================================
if st.sidebar.button("Launch Hybrid Search", type="primary"):
    if not target_company:
        st.error("❌ Please provide a target company domain.")
    else:
        status_box = st.empty()
        with st.spinner("Processing background matrix queries..."):
            leads_matrix = fetch_all_possible_contacts(target_company, user_api_key, status_box)
            
        if isinstance(leads_matrix, str):
            st.error(leads_matrix)
        elif not leads_matrix:
            st.warning("⚠️ No contacts found matching criteria details.")
        else:
            df = pd.DataFrame(leads_matrix)
            master_df = df.copy()
            
            # Map dynamic layout configurations cleanly
            display_columns = ["Name", "Company"]
            if show_designation: display_columns.insert(1, "Designation")
            if show_email: display_columns.append("Corporate Email")
            if show_source: display_columns.append("Source")
            if show_linkedin: display_columns.append("LinkedIn URL")
            
            # Render structured interactive display dataframe
            st.subheader(f"📊 Aggregated Contact Preview (Total Extracted: {len(df)})")
            st.dataframe(df[display_columns], use_container_width=True)
            
            # Parse Excel file using memory bytes arrays natively
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                master_df.to_excel(writer, index=False, sheet_name="Aggregated Leads Matrix")
            
            st.markdown("---")
            st.download_button(
                label="Download Complete Roster as Excel",
                data=excel_buffer.getvalue(),
                file_name=f"{clean_domain(target_company).split('.')[0]}_hybrid_leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
