import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import urlparse
from io import BytesIO

# ==========================================
# PAGE CONFIGURATIONS & INTERFACE
# ==========================================
st.set_page_config(
    page_title="India Influencer Marketing Finder (Tomba Edition)",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 India Influencer Marketing Lead Finder — Tomba Engine")
st.markdown("Extract deep corporate directories across multiple pages simultaneously with unblocked pagination filters.")

# ==========================================
# CORE EXTRACTION REQUISITES
# ==========================================
def clean_domain(input_string):
    """Strips away protocols, www, sub-directories, and spacing to avoid errors"""
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

def fetch_all_tomba_contacts(company_domain, api_key, status_container):
    """Loops through Tomba.io pagination to drain all available records seamlessly"""
    target_domain = clean_domain(company_domain)
    organization_name = target_domain.split('.')[0].title()
    
    all_compiled_leads = []
    india_keywords = ["india", "mumbai", "delhi", "bengaluru", "bangalore", "pune", "hyderabad", "chennai", "gurugram", "gurgaon", "noida"]
    
    current_page = 1
    status_container.info(f"📡 Initiating deep multi-page directory crawl for: **{target_domain}**")
    
    while True:
        status_container.text(f"⏳ Crawling Page {current_page} from Tomba.io index...")
        
        # Tomba's native clean URL pagination structure
        url = f"https://api.tomba.io/v1/domain-search?domain={target_domain}&page={current_page}"
        
        headers = {
            "X-Tomba-Key": api_key,
            "Accept": "application/json"
        }
        
        try:
            time.sleep(1.0)  # Rate pacing protection delay
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code in [401, 403]:
                return "Authentication Failed: Invalid Tomba API Key permissions."
            if response.status_code != 200:
                status_container.warning(f"⚠️ Stopped paging at page {current_page}. Server Response: HTTP {response.status_code}")
                break
                
            data = response.json().get("data", {})
            emails_data = data.get("emails", [])
            
            # 🛑 BREAK CONDITION: If a page comes back completely empty, we have fully drained the database
            if not emails_data:
                status_container.success(f"🏁 Reached end of available directory. Total pages parsed: {current_page - 1}")
                break
                
            # Parse individual records in the current batch page
            for contact in emails_data:
                raw_position = contact.get("position") or "Executive / Team Member"
                first = contact.get("first_name") or ""
                last = contact.get("last_name") or ""
                full_name = f"{first} {last}".strip()
                if not full_name:
                    full_name = "Company Associate"
                    
                # Geographic mapping evaluation metrics
                is_india = False
                if "mcaffeine" in target_domain or "beyoung" in target_domain or "nykaa" in target_domain:
                    is_india = True
                else:
                    if contact.get("country"):
                        if "in" in str(contact["country"]).lower():
                            is_india = True
                    if any(kw in raw_position.lower() for kw in india_keywords):
                        is_india = True
                        
                if is_india:
                    all_compiled_leads.append({
                        "Name": full_name,
                        "Designation": raw_position,
                        "Company": organization_name,
                        "Corporate Email": contact.get("email", "N/A"),
                        "LinkedIn URL": contact.get("linkedin") if contact.get("linkedin") else "N/A",
                        "Source Page": current_page
                    })
            
            # Increment and move directly to the next page layout safely
            current_page += 1
            
        except Exception as e:
            status_container.error(f"❌ Exception error occurred on page {current_page}: {str(e)}")
            break
            
    return all_compiled_leads

# ==========================================
# STREAMLIT CONTROL PANEL SIDEBAR
# ==========================================
st.sidebar.header("🔑 Authentication Setup")
user_api_key = st.sidebar.text_input("Tomba.io Private API Key", type="password", help="Paste your private secret key token here.")
target_company = st.sidebar.text_input("Company Domain", placeholder="e.g., nykaa.com, mcaffeine.com")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Output Options")

show_email = st.sidebar.checkbox("Show Corporate Email", value=True)
show_designation = st.sidebar.checkbox("Show Designation", value=True)
show_linkedin = st.sidebar.checkbox("Show LinkedIn Links", value=True)
show_page = st.sidebar.checkbox("Show Source Page Metric", value=False)

# ==========================================
# MAIN EXECUTION ENGINE PIPELINE
# ==========================================
if st.sidebar.button("Launch Deep Harvest Run", type="primary"):
    if not user_api_key:
        st.error("❌ Please provide a valid Tomba.io API Key in the sidebar.")
    elif not target_company:
        st.error("❌ Please specify a target company domain.")
    else:
        status_box = st.empty()
        
        with st.spinner("Extracting multi-page directory structures natively..."):
            leads_matrix = fetch_all_tomba_contacts(target_company, user_api_key, status_box)
            
        if isinstance(leads_matrix, str):
            st.error(leads_matrix)
        elif not leads_matrix:
            st.warning("⚠️ No matching profiles or India-localized contacts found on Tomba's indexed records.")
        else:
            df = pd.DataFrame(leads_matrix)
            master_df = df.copy()
            
            # Form display columns arrays dynamically based on user controls
            display_columns = ["Name", "Company"]
            if show_designation: display_columns.insert(1, "Designation")
            if show_email: display_columns.append("Corporate Email")
            if show_linkedin: display_columns.append("LinkedIn URL")
            if show_page: display_columns.append("Source Page")
            
            st.subheader(f"📊 Extracted Contact Preview (Total Records Drained: {len(df)})")
            st.dataframe(df[display_columns], use_container_width=True)
            
            # Pack memory streams cleanly to handle seamless inline excel generation downloads
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                master_df.to_excel(writer, index=False, sheet_name="India Tomba Extract")
            excel_binaries = excel_buffer.getvalue()
            
            st.markdown("---")
            st.subheader("📥 Export Final Clean Asset")
            
            st.download_button(
                label="Download Complete Roster as Excel",
                data=excel_binaries,
                file_name=f"{clean_domain(target_company).split('.')[0]}_tomba_leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
