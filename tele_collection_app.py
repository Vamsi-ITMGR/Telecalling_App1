import streamlit as st
import pandas as pd
import os
import time  # basic file locking retries
from datetime import date, datetime
import numpy as np
from io import BytesIO
import json
import plotly.express as px
from streamlit_option_menu import option_menu

# --- Configuration ---
DATA_FILE = "TeleCollectionData.csv"
UPDATE_FILE = "TeleCollectionUpdates.csv"
ASSIGNMENT_FILE = "assignments.json"
LOCK_FILE = ASSIGNMENT_FILE + ".lock"  # Lock file for assignments

# -----------------------------------------------------------------
# --- 1. USER DATABASE (EMBEDDED) ---
# -----------------------------------------------------------------
# Passwords are in PLAIN TEXT. Usernames are case-sensitive keys.
USERS_DATABASE = {
    "Nandhini": {"name": "Nandhini", "password": "pass@2025", "role": "Manager"},
    "Soumiya": {"name": "Soumiya", "password": "pass@123", "role": "Telecaller"},
    "Dhanalatha": {"name": "Dhanalatha", "password": "pass@123", "role": "Telecaller"},
    "Vaishnavi": {"name": "Vaishnavi", "password": "pass@123", "role": "Telecaller"},
    "Yesurani": {"name": "Yesurani", "password": "pass@123", "role": "Telecaller"},
    "Bharathi": {"name": "Bharathi", "password": "pass@123", "role": "Telecaller"},
}
# -----------------------------------------------------------------


# --- Key Column Names ---
BRANCH_COL = "Branch Name"
LOAN_ID_COL = "Loan Account Number"
CUST_NAME_COL = "Customer Name"
PRODUCT_NAME_COL = "Product Name"
OVERDUE_BUCKET_COL = "OverDueBucket"
TOTAL_OUTSTANDING_COL = "Total Outstanding"
OVERDUE_AMOUNT_COL = "Overdue Amount"
OVERDUE_DAYS_COL = "Overdue Days"
INSTALLMENT_AMOUNT_COL = "Installment Amount"
LAST_COLLECTED_DATE_COL = "Last Collected Date"
LOAN_AMOUNT_DISB_COL = "Loan Amount Disbursed"
MOBILE_COL = "Customer Mobile No"
ZONE_COL = "Zone Name"
REGION_COL = "Region Name"
ADDRESS_COL = "Address"
VILLAGE_COL = "Village"
DISTRICT_COL = "District"
PINCODE_COL = "PinCode"
FE_NAME_COL = "FEName"
BM_NAME_COL = "BMName"
COBORROWER_COL = "CoBorrower"
COBORROWER_MOBILE_COL = "CoBorrowerMobileNo"
PAID_AMOUNT_COL = "Paid Amount"
INSTALLMENT_END_DATE_COL = "Installment End Date"
TENURE_COL = "Tenure"
LOAN_DISBURSED_DATE_COL = "Loan Disbursed Date"
BALANCE_TENURE_COL = "Balance Tenure"

# --- Custom CSS (Stable) ---
def app_css():
    """CSS for the main application (after login)."""
    st.markdown(
        """
        <style>
            .main-header { font-size: 2.5em; color: #264653; font-weight: 600; padding-bottom: 5px; }
            [data-testid="stSidebar"] { background-color: #f7f9fb; border-right: 1px solid #e0e0e0; padding-top: 1rem; }
            [data-testid="stAppViewContainer"] > section { padding-top: 1rem; }
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
                 border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.08); background-color: white; transition: transform 0.2s;
            }
             div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:hover {
                  transform: translateY(-3px); box-shadow: 0 6px 10px rgba(0,0,0,0.1);
            }
            .stForm { border: 2px solid #2a9d8f; border-radius: 10px; padding: 30px; background-color: #f0fdfa; }
            .stForm [data-testid="stHeading"] { color: #264653; font-weight: bold; }
            .badge-low { background-color: #2a9d8f; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.9em; }
            .badge-high { background-color: #f9a03f; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.9em; }
            .badge-critical { background-color: #e76f51; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.9em; }
            .metric-box { border-left: 5px solid #264653; border-radius: 5px; padding: 10px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .metric-value { font-size: 1.8em; font-weight: bold; color: #2a9d8f; }
            .metric-label { font-size: 0.9em; color: #6c757d; margin-top: -10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def login_css():
    """CSS for the login page (Blue/Green Background)."""
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] > section {
                background-image: linear-gradient(to right, #00467F, #A5CC82);
            }
            .main-header {
                font-size: 2.2em;
                color: #FFFFFF;
                font-weight: 600;
                padding-bottom: 5px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }
            div[data-testid="stVerticalBlock"] div.st-emotion-cache-1r6slb0 {
                background-color: rgba(255, 255, 255, 0.9) !important;
                border-radius: 10px !important;
                padding: 2em !important;
                border: 1px solid #ccc;
            }
            [data-testid="stHeader"] {
                background-color: transparent;
            }
            .stTextInput label, .stSubheader, .stForm label {
                 color: #333 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- 2. AUTHENTICATION & ASSIGNMENT FUNCTIONS ---

def check_password(username, password):
    """Verifies a user's password."""
    user_data = USERS_DATABASE.get(username)
    if user_data and password == user_data.get("password"):
        return True, user_data.get("name"), user_data.get("role")
    return False, None, None

def get_all_users(role_filter=None):
    """Gets a list of all users, optionally filtered by role."""
    user_list = []
    for username, details in USERS_DATABASE.items():
        if not role_filter or details.get("role") == role_filter:
            user_list.append({"username": username, "name": details.get("name")})
    return user_list

@st.cache_resource(ttl=60)  # Cache for 1 minute
def load_assignments():
    """Loads telecaller assignments from the JSON file."""
    # Ensure file exists
    if not os.path.exists(ASSIGNMENT_FILE):
        try:
            with open(ASSIGNMENT_FILE, "w") as f:
                json.dump({}, f)
            return {}
        except IOError as e:
            st.error(f"Could not create assignment file: {e}")
            return {}
    # Read file content
    try:
        with open(ASSIGNMENT_FILE, "r") as f:
            content = f.read()
            # Handle empty file
            if not content.strip():
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        st.error(f"Error decoding {ASSIGNMENT_FILE}. Check format or delete to recreate.")
        return {}
    except Exception as e:
        st.error(f"Error reading {ASSIGNMENT_FILE}: {e}")
        return {}

def save_assignments(_assignments):
    """Saves assignments with basic file locking."""
    lock_acquired = False
    max_retries = 3
    retry_delay = 0.5  # seconds
    for attempt in range(max_retries):
        try:
            # Try to acquire lock
            lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(lock_fd)
            lock_acquired = True

            # Save data
            with open(ASSIGNMENT_FILE, "w") as f:
                json.dump(_assignments, f, indent=4)

            # clear cached resource
            try:
                load_assignments.clear()
            except Exception:
                pass
            return True  # Success

        except FileExistsError:
            if attempt < max_retries - 1:
                st.warning(f"Assignment file locked, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                st.error("Assignment file is currently locked by another process after multiple retries. Please try again.")
                return False
        except IOError as e:
            st.error(f"Failed to save assignments: {e}")
            return False
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return False
        finally:
            if lock_acquired and os.path.exists(LOCK_FILE):
                try:
                    os.remove(LOCK_FILE)
                except OSError:
                    pass  # Ignore error if lock removal fails
    return False  # Should not reach here unless retries failed

def get_user_assignments(username):
    """Gets the specific assignments for a single user."""
    assignments = load_assignments()
    return assignments.get(username, {"branches": [], "products": [], "loans": []})

# --- 3. CORE HELPER FUNCTIONS ---

def safe_currency(value):
    if pd.notna(value):
        try:
            return f"₹{float(value):,.2f}"
        except (ValueError, TypeError):
            pass
    return "N/A"

def overdue_badge_color(days):
    if pd.notna(days):
        try:
            days_int = int(float(days))  # Handle potential floats/strings
            if days_int >= 180:
                return f"<span class='badge-critical'>🔴 Critical ({days_int} days)</span>"
            elif days_int >= 90:
                return f"<span class='badge-high'>🟠 High ({days_int} days)</span>"
            else:
                return f"<span class='badge-low'>🟢 Low ({days_int} days)</span>"
        except (ValueError, TypeError):
            return "⚪ Invalid"
    return "⚪ N/A"

def render_metric(col, label, value, color_class):
    with col:
        st.markdown(
            f"""<div class='metric-box'><p class='metric-label'>{label}</p><p class='metric-value' style='color:{color_class}'>{value}</p></div>""",
            unsafe_allow_html=True,
        )

@st.cache_data(ttl=300)  # Cache master data for 5 minutes
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Master data file not found: {file_path}")
        return None
    with st.spinner(f"⏳ Loading master data from '{file_path}'..."):
        try:
            # Define which columns are numeric
            numeric_cols = [
                TOTAL_OUTSTANDING_COL,
                OVERDUE_AMOUNT_COL,
                OVERDUE_DAYS_COL,
                INSTALLMENT_AMOUNT_COL,
                LOAN_AMOUNT_DISB_COL,
            ]
            # Date columns (parse later if needed)
            date_cols = [INSTALLMENT_END_DATE_COL, LOAN_DISBURSED_DATE_COL, LAST_COLLECTED_DATE_COL]

            df = pd.read_csv(file_path, dtype=str, low_memory=False)
            if df.empty:
                st.warning(f"Master data file is empty: {file_path}")
                return pd.DataFrame()

            # Convert numeric columns
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    # create column if missing
                    df[col] = np.nan
                    st.warning(f"Numeric column '{col}' missing in master data. Added as NaN.")

            # Convert date columns to strings for safe display (we'll keep as string to avoid parsing issues)
            for col in date_cols:
                if col in df.columns:
                    # Try to parse to datetime, then format
                    try:
                        # Specify dayfirst=True to handle dd-mm-yyyy format
                        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")
                    except Exception:
                        df[col] = df[col].astype(str).fillna("N/A")
                else:
                    df[col] = "N/A"
                    st.warning(f"Date column '{col}' missing in master data. Added as 'N/A'.")

            # Categorical columns - ensure exist
            categorical_cols = [
                BRANCH_COL,
                LOAN_ID_COL,
                OVERDUE_BUCKET_COL,
                CUST_NAME_COL,
                PRODUCT_NAME_COL,
                REGION_COL,
                MOBILE_COL,
                ADDRESS_COL,
                VILLAGE_COL,
                DISTRICT_COL,
                COBORROWER_COL,
                COBORROWER_MOBILE_COL,
                TENURE_COL,
                BALANCE_TENURE_COL,
            ]
            for col in categorical_cols:
                if col in df.columns:
                    df[col] = df[col].fillna("N/A").astype(str)
                else:
                    df[col] = "N/A"
                    st.warning(f"Categorical column '{col}' missing in master data. Added as 'N/A'.")

            return df
        except pd.errors.EmptyDataError:
            st.error(f"Master data file is empty: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading master data from {file_path}: {e}")
            st.exception(e)
            return None

@st.cache_data(ttl=60)  # Cache updates data for 1 minute
def load_updates(file_path):
    if not os.path.exists(file_path):
        st.warning(f"Updates file not found: {file_path}. No past records loaded.")
        # create empty df with expected columns
        cols = [
            LOAN_ID_COL,
            BRANCH_COL,
            OVERDUE_BUCKET_COL,
            "Called Date",
            "Staff Name",
            "Customer Response",
            "Feedback Status",
            "Promise to Pay Date",
            "Payment Mode",
            PAID_AMOUNT_COL,
            "UPI/UTR Details",
            "Cash Received Date",
            "Cash Received By",
        ]
        return pd.DataFrame(columns=cols)

    with st.spinner(f"⏳ Loading follow-up records from '{file_path}'..."):
        try:
            if os.path.getsize(file_path) == 0:
                cols = [
                    LOAN_ID_COL,
                    BRANCH_COL,
                    OVERDUE_BUCKET_COL,
                    "Called Date",
                    "Staff Name",
                    "Customer Response",
                    "Feedback Status",
                    "Promise to Pay Date",
                    "Payment Mode",
                    PAID_AMOUNT_COL,
                    "UPI/UTR Details",
                    "Cash Received Date",
                    "Cash Received By",
                ]
                return pd.DataFrame(columns=cols)

            #updates_df = pd.read_csv(file_path)
            updates_df = pd.read_csv(file_path,encoding="cp1252",# Windows Excel encoding
            low_memory=False)

            # Convert dates safely
            for col in ["Promise to Pay Date", "Called Date", "Cash Received Date"]:
                if col in updates_df.columns:
                    # Specify dayfirst=True to handle dd-mm-yyyy format
                    updates_df[col] = pd.to_datetime(updates_df[col], errors="coerce", dayfirst=True)
                    #updates_df[col] = pd.to_datetime(updates_df[col], errors="coerce").dt.strftime("%d-%m-%Y")

            # Ensure essential text columns exist and are strings
            for col in ["Staff Name", "Feedback Status", OVERDUE_BUCKET_COL, LOAN_ID_COL, BRANCH_COL]:
                if col not in updates_df.columns:
                    updates_df[col] = "N/A"
                updates_df[col] = updates_df[col].fillna("N/A").astype(str)

            # Ensure Paid Amount exists and is numeric
            if PAID_AMOUNT_COL not in updates_df.columns:
                updates_df[PAID_AMOUNT_COL] = np.nan
            updates_df[PAID_AMOUNT_COL] = pd.to_numeric(updates_df[PAID_AMOUNT_COL], errors="coerce")

            return updates_df
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            st.exception(e)
            return pd.DataFrame()

@st.cache_data
def convert_df_to_csv(df_to_convert):
    if isinstance(df_to_convert, pd.DataFrame):
        return df_to_convert.to_csv(index=False).encode("utf-8")
    else:
        return "".encode("utf-8")

# --- Footer ---
def add_footer():
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey;'>@2025-Maximal Finance and Investments Limited</div>", unsafe_allow_html=True)

# --- 4. "PAGE" DEFINITIONS ---

def show_crm_page():
    """Renders the Telecaller CRM Page."""

    # --- 1. Load Data & User Assignments ---
    with st.spinner("Loading assigned data..."):
        df_master = load_data(DATA_FILE)
        if df_master is None or (isinstance(df_master, pd.DataFrame) and df_master.empty):
            st.error("Cannot load master data.")
            add_footer()
            st.stop()

        updates_df = load_updates(UPDATE_FILE)
        user_assignments = get_user_assignments(st.session_state.username)
        df_user_accessible = df_master.copy()
        
      
        # Apply assignment filters...
        if user_assignments.get("branches"):
            df_user_accessible = df_user_accessible[df_user_accessible[BRANCH_COL].isin(user_assignments["branches"])]
        if user_assignments.get("products"):
            df_user_accessible = df_user_accessible[df_user_accessible[PRODUCT_NAME_COL].isin(user_assignments["products"])]
        if user_assignments.get("loans"):
            df_user_accessible = df_user_accessible[df_user_accessible[LOAN_ID_COL].isin(user_assignments["loans"])]
    if df_user_accessible.empty and not df_master.empty:
        st.warning("No loans assigned or match assignments.")

    # --- 2. Sidebar Filters ---
    st.sidebar.title("🔎 **Customer Filters**")
    st.sidebar.markdown("Filter *assigned* portfolio.")
    available_branches = ["All"] + sorted(df_user_accessible[BRANCH_COL].dropna().unique()) if BRANCH_COL in df_user_accessible else ["All"]
    available_products = sorted(df_user_accessible[PRODUCT_NAME_COL].dropna().unique()) if PRODUCT_NAME_COL in df_user_accessible else []
    available_buckets = ["All"] + sorted(df_user_accessible[OVERDUE_BUCKET_COL].dropna().unique()) if OVERDUE_BUCKET_COL in df_user_accessible else ["All"]
    with st.sidebar.form("filter_form"):
        branch_selected = st.selectbox("**Branch Name**", available_branches)
        product_selected = st.multiselect("**Product Name(s)**", options=available_products, default=[])
        bucket_selected = st.selectbox("**Overdue Bucket**", available_buckets)
        loan_search = st.text_input("**Search Loan Account Number**")
        apply_button = st.form_submit_button("Apply Filters", width='stretch')

    # --- 3. Filter Logic ---
    df_filtered = df_user_accessible.copy()
    if BRANCH_COL in df_filtered and branch_selected != "All":
        df_filtered = df_filtered[df_filtered[BRANCH_COL] == branch_selected]
    if product_selected and PRODUCT_NAME_COL in df_filtered:
        df_filtered = df_filtered[df_filtered[PRODUCT_NAME_COL].isin(product_selected)]
    if OVERDUE_BUCKET_COL in df_filtered and bucket_selected != "All":
        df_filtered = df_filtered[df_filtered[OVERDUE_BUCKET_COL] == bucket_selected]
    if loan_search and LOAN_ID_COL in df_filtered:
        df_filtered = df_filtered[df_filtered[LOAN_ID_COL].astype(str).str.contains(loan_search, case=False, na=False)]

    # --- 4. Metrics ---
    st.subheader("**Your Assigned Portfolio Overview**")
    total_overdue = df_filtered[OVERDUE_AMOUNT_COL].sum() if OVERDUE_AMOUNT_COL in df_filtered else 0
    total_accounts = len(df_filtered)
    today = datetime.now().date()
    user_loans = df_user_accessible[LOAN_ID_COL].unique() if LOAN_ID_COL in df_user_accessible else []
    alert_df_all = pd.DataFrame()
    if not updates_df.empty and "Promise to Pay Date" in updates_df.columns and LOAN_ID_COL in updates_df.columns:
        updates_df_filtered = updates_df.dropna(subset=["Promise to Pay Date"])
        alert_df_all = updates_df_filtered[
            (updates_df_filtered["Promise to Pay Date"].dt.date <= today) & (updates_df_filtered[LOAN_ID_COL].isin(user_loans))
        ]

    metric_cols = st.columns(4)
    render_metric(metric_cols[0], "Filtered Overdue", safe_currency(total_overdue), "#e76f51")
    render_metric(metric_cols[1], "Filtered Accounts", f"{total_accounts:,}", "#264653")
    render_metric(metric_cols[2], "Your P2P Alerts", f"{len(alert_df_all):,}", "#f9a03f")
    st.markdown("---")

    # --- 5. P2P Alerts ---
    if not alert_df_all.empty:
        with st.expander(f"🚨 **View Your {len(alert_df_all)} Pending P2P Alerts**", expanded=False):
            alert_display_df = alert_df_all.sort_values(by="Promise to Pay Date", ascending=True)
            #st.dataframe(alert_display_df, width='stretch', height=200)
            st.dataframe(alert_display_df, width='stretch', height=200)
            csv_data = convert_df_to_csv(alert_display_df)
            if csv_data:
                st.download_button(
                    "⬇️ Download P2P List",
                    csv_data,
                    f'P2P_Alerts_{st.session_state.username}_{today.strftime("%Y%m%d")}.csv',
                    'text/csv',
                )
    elif not updates_df.empty:
        st.info("No pending P2P alerts.")

    # --- 6. Customer Cards & Form ---
    st.markdown("## **💳 Customer Overview and Action**")
    loan_list_options = sorted(df_filtered[LOAN_ID_COL].unique()) if LOAN_ID_COL in df_filtered else []
    loan_list_for_form = ["Select Loan Account to Update..."] + loan_list_options
    if not loan_list_options:
        st.warning("No loans match filters.")
        loan_selected_for_form = "Select Loan Account..."
    else:
        loan_selected_for_form = st.selectbox("**Select Loan**", loan_list_for_form, label_visibility="collapsed")
    st.markdown("---")

    customer_data_for_form = None
    display_df = pd.DataFrame()
    if loan_selected_for_form != "Select Loan Account to Update..." and loan_selected_for_form != "Select Loan Account...":
        display_df = df_filtered[df_filtered[LOAN_ID_COL] == loan_selected_for_form]
        if not display_df.empty:
            customer_data_for_form = display_df.iloc[0].to_dict()
        else:
            st.warning(f"Loan {loan_selected_for_form} not found.")
            display_df = pd.DataFrame()
    else:
        display_df = df_filtered.head(10)
        if len(df_filtered) > 10:
            st.info(f"Displaying first 10 of {len(df_filtered)} records.")
        elif len(df_filtered) == 0 and len(df_user_accessible) > 0:
            st.warning("No customers match filters.")

    # Display Cards
    if not display_df.empty:
        for idx, row in display_df.iterrows():
            with st.container():
                st.markdown(f"### **📋 {row.get(CUST_NAME_COL, 'N/A')} | Loan: `{row.get(LOAN_ID_COL, 'N/A')}`**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f"**🏦 Product:** {row.get(PRODUCT_NAME_COL, 'N/A')}\n\n**🏢 Branch:** {row.get(BRANCH_COL, 'N/A')}"
                    )
                with col2:
                    st.markdown(
                        f"**💰 Total Outstanding:** **{safe_currency(row.get(TOTAL_OUTSTANDING_COL))}**\n\n**⚠️ Overdue Amount:** **{safe_currency(row.get(OVERDUE_AMOUNT_COL))}**"
                    )
                with col3:
                    st.markdown(
                        f"**⏱️ DPD:** {overdue_badge_color(row.get(OVERDUE_DAYS_COL))}\n\n**📱 Mobile:** **{row.get(MOBILE_COL, 'N/A')}**",
                        unsafe_allow_html=True,
                    )
                with st.expander("📝 **Full Customer Details**"):
                    st.markdown(
                        f"**📍 Address:** {row.get(ADDRESS_COL, 'N/A')}, {row.get(VILLAGE_COL, 'N/A')}, {row.get(DISTRICT_COL, 'N/A')}"
                    )
                    st.markdown(f"**👥 Co-Borrower:** {row.get(COBORROWER_COL, 'N/A')} | Mobile: {row.get(COBORROWER_MOBILE_COL, 'N/A')}")
                    st.markdown(f"**📊 OD Bucket:** {row.get(OVERDUE_BUCKET_COL, 'N/A')}")
                    st.markdown(f"**📊 Loan Amount:** {row.get(LOAN_AMOUNT_DISB_COL,'N/A')}")
                    st.markdown(f"**📊 Tenure:** {row.get(TENURE_COL,'N/A')}")
                    st.markdown(f"**📊 EMI:** {row.get(INSTALLMENT_AMOUNT_COL,'N/A')}")
                    st.markdown(f"**📊 Loan End Date:** {row.get(INSTALLMENT_END_DATE_COL,'N/A')}")
                    st.markdown(f"**📊 Tenure Balance:** {row.get(BALANCE_TENURE_COL,'N/A')}")
                    st.markdown(f"**📊 Loan Disbursement Date:** {row.get(LOAN_DISBURSED_DATE_COL,'N/A')}")
    elif len(df_user_accessible) > 0:
        pass

    st.markdown("---")

    # --- Follow-Up Form ---
    st.markdown("## **✍️ Submit New Follow-Up Action**")
    if customer_data_for_form is None:
        st.info("👈 Select a loan above to submit.")
    else:
        with st.form("followup_form", clear_on_submit=True):
            st.markdown(f"**Loan:** **`{loan_selected_for_form}`**")
            col1, col2 = st.columns(2)
            with col1:
                called_date_today = date.today()
                st.date_input("**📅 Call Date**", value=called_date_today, disabled=True)
                st.text_input("**👨‍💼 Staff Name**", value=st.session_state.user_name, disabled=True)
            with col2:
                feedback_status = st.selectbox(
                    "**🗣️ Feedback Status*** ",
                    ["","Absconding Clients","Call Not Done","Call Not Lifted","Client  Not Respose",
                    "Client Respose","Death Clients","Loan Closed","Mobile Not Service","Mobile Switch off",
                    "Paid","Partially Paid","Promise to Pay","Refused to Pay","Tenure Mistakes",
                    "Will Call Back","Wrong Numbers","Other"]
                )

            # Sections always visible
            with st.container():
                st.markdown("**Promise to Pay Details**")
                promise_date = st.date_input("**⏳ P2P Date** (If status is 'Promise to Pay')", value=None)
            with st.container():
                st.markdown("**Payment Details** (If status is 'Paid')")
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    payment_mode = st.selectbox("**💳 Mode**", ["", "Cash", "UPI", "Bank Transfer", "Cheque"])
                with pc2:
                    cash_received_date = st.date_input("**📥 Received Date**", value=None)
                with pc3:
                    # Streamlit number_input requires default value; we handle validation later
                    paid_amount = st.number_input(f"**💰 {PAID_AMOUNT_COL}**", min_value=0.0, value=0.0, step=1.00, format="%.2f")
                upi_details = st.text_input("**🔗 UPI/Txn Ref**", placeholder="UTR, Txn ID")
                cash_received_by = st.text_input("**👤 Cash Received By**", placeholder="Staff Name")

            customer_response = st.text_area("**📝 Notes**", height=100)
            st.markdown("---")
            st.caption("Fields marked * required based on Status.")
            submit_button = st.form_submit_button("✅ Submit Follow-Up", width='stretch')

            if submit_button:
                # Validation
                errors = []
                if not feedback_status:
                    errors.append("Feedback Status")
                if feedback_status == "Promise to Pay" and not promise_date:
                    errors.append("Promise to Pay Date")
                if feedback_status == "Paid":
                    if not payment_mode:
                        errors.append("Payment Mode")
                    if not cash_received_date:
                        errors.append("Payment Received Date")
                    if paid_amount is None or paid_amount <= 0:
                        errors.append(f"{PAID_AMOUNT_COL} (> 0)")

                if errors:
                    st.session_state.form_message = {"type": "error", "text": f"⚠️ **Validation Failed!** Correct: {', '.join(errors)}"}
                    st.rerun()
                else:
                    # Save Logic
                    od_bucket = customer_data_for_form.get(OVERDUE_BUCKET_COL, "N/A")
                    new_entry = {
                        LOAN_ID_COL: loan_selected_for_form,
                        BRANCH_COL: customer_data_for_form.get(BRANCH_COL, "N/A"),
                        OVERDUE_BUCKET_COL: od_bucket,
                        "Called Date": called_date_today,
                        "Staff Name": st.session_state.user_name,
                        "Customer Response": customer_response,
                        "Feedback Status": feedback_status,
                        "Promise to Pay Date": promise_date if feedback_status == "Promise to Pay" else None,
                        "Payment Mode": payment_mode if feedback_status == "Paid" else "",
                        PAID_AMOUNT_COL: paid_amount if feedback_status == "Paid" else np.nan,
                        "UPI/UTR Details": upi_details
                        if (feedback_status == "Paid" and payment_mode in ["UPI", "Bank Transfer"])
                        else "",
                        "Cash Received Date": cash_received_date if feedback_status == "Paid" else None,
                        "Cash Received By": cash_received_by if (feedback_status == "Paid" and payment_mode == "Cash") else "",
                    }
                    new_entry_df = pd.DataFrame([new_entry])
                    file_exists = os.path.exists(UPDATE_FILE)
                    try:
                        # Format dates, handle None -> '' for CSV
                        for col in ["Called Date", "Promise to Pay Date", "Cash Received Date"]:
                            if col in new_entry_df.columns and pd.notna(new_entry_df[col].iloc[0]):
                                new_entry_df[col] = pd.to_datetime(new_entry_df[col]).dt.strftime("%Y-%m-%d")
                            else:
                                new_entry_df[col] = ""

                        if PAID_AMOUNT_COL in new_entry_df.columns:
                            new_entry_df[PAID_AMOUNT_COL] = pd.to_numeric(new_entry_df[PAID_AMOUNT_COL], errors="coerce").fillna("")

                        # Header check logic
                        header_needed = not file_exists or os.path.getsize(UPDATE_FILE) == 0
                        cols_to_ensure = [OVERDUE_BUCKET_COL, PAID_AMOUNT_COL]
                        if file_exists and not header_needed:
                            try:
                                existing_cols = pd.read_csv(UPDATE_FILE, nrows=0).columns.tolist()
                                missing_cols = [c for c in cols_to_ensure if c not in existing_cols]
                                if missing_cols:
                                    temp_df = pd.read_csv(UPDATE_FILE)
                                    for col in missing_cols:
                                        temp_df[col] = np.nan if col == PAID_AMOUNT_COL else "N/A"
                                    temp_df.to_csv(UPDATE_FILE, index=False)
                                    # After fixing header we still append new row normally
                            except Exception as read_err:
                                st.session_state.form_message = {"type": "warning", "text": f"Header check failed: {read_err}"}
                                st.rerun()
                        elif header_needed:
                            for col in cols_to_ensure:
                                if col not in new_entry_df.columns:
                                    new_entry_df[col] = np.nan if col == PAID_AMOUNT_COL else "N/A"

                        new_entry_df.to_csv(UPDATE_FILE, mode="a", header=header_needed, index=False)
                        try:
                            load_updates.clear()
                        except Exception:
                            pass
                        
                        # Set success message in session state
                        st.session_state.form_message = {"type": "success", "text": "✅ Follow-up saved successfully!"}
                        st.rerun()
                        
                    except Exception as e:
                        st.session_state.form_message = {"type": "error", "text": f"Save error: {e}"}
                        st.rerun()

        # Display message from session state if it exists
        if "form_message" in st.session_state:
            message = st.session_state.form_message
            if message["type"] == "success":
                st.success(message["text"])
            elif message["type"] == "error":
                st.error(message["text"])
            elif message["type"] == "warning":
                st.warning(message["text"])
            
            # Clear the message after displaying it
            del st.session_state.form_message

    add_footer()

def show_dashboard_page():
    """Renders the Manager Dashboard Page."""
    st.subheader("**Manager Dashboard: Team Performance**")
    df_master = load_data(DATA_FILE)
    df_updates = load_updates(UPDATE_FILE)
    if df_updates.empty:
        st.info("No follow-up data yet.")
        add_footer()
        st.stop()
    st.info(f"Dashboard based on **{len(df_updates):,}** total follow-ups.")

    # Merge data safely...
    df_merged = df_updates.copy()
    optional_master_cols = [PRODUCT_NAME_COL, OVERDUE_BUCKET_COL]

    if df_master is not None and not df_master.empty:
        if LOAN_ID_COL in df_master.columns:
            merge_cols = [LOAN_ID_COL] + [c for c in optional_master_cols if c in df_master.columns]
            if len(merge_cols) > 1:
                df_master_subset = df_master[merge_cols].drop_duplicates(subset=[LOAN_ID_COL]).copy()
                df_merged = pd.merge(df_updates, df_master_subset, on=LOAN_ID_COL, how="left")
        else:
            st.warning(f"Master data missing '{LOAN_ID_COL}'.")
    else:
        st.warning("Master data missing/invalid.")

    for col in optional_master_cols:
        if col not in df_merged.columns:
            df_merged[col] = "N/A"
        df_merged[col] = df_merged[col].fillna("N/A")

    if PAID_AMOUNT_COL not in df_merged.columns:
        df_merged[PAID_AMOUNT_COL] = np.nan
    df_merged[PAID_AMOUNT_COL] = pd.to_numeric(df_merged[PAID_AMOUNT_COL], errors="coerce").fillna(0)

    # Filters...
    st.markdown("#### **Filter Dashboard Data**")
    col1, col2 = st.columns([1, 2])
    with col1:
        staff_list = ["All"] + sorted(df_merged["Staff Name"].dropna().unique())
        staff_filter = st.selectbox("**Staff Name**", staff_list)
    with col2:
        valid_dates = df_merged["Called Date"].dropna()
        if not valid_dates.empty:
            min_date = pd.to_datetime(valid_dates.min()).date()
            max_date = pd.to_datetime(valid_dates.max()).date()
        else:
            min_date = date.today()
            max_date = date.today()
        date_range = st.date_input("**Call Date Range**", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    # Apply filters...
    df_filtered = df_merged.copy()
    if staff_filter != "All":
        df_filtered = df_filtered[df_filtered["Staff Name"] == staff_filter]
    if len(date_range) == 2 and date_range[0] and date_range[1]:
        try:
            start = pd.to_datetime(date_range[0])
            end = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
            df_filtered["Called Date"] = pd.to_datetime(df_filtered["Called Date"], errors="coerce")
            df_filtered = df_filtered.dropna(subset=["Called Date"])
            df_filtered = df_filtered[(df_filtered["Called Date"] >= start) & (df_filtered["Called Date"] < end)]
        except Exception as e:
            st.error(f"Date filter error: {e}")

    if df_filtered.empty:
        st.warning("No data for selected filters.")
        add_footer()
        st.stop()

    st.markdown("---")
    total_calls = len(df_filtered)
    total_p2p = len(df_filtered[df_filtered["Feedback Status"] == "Promise to Pay"])
    total_paid_status = len(df_filtered[df_filtered["Feedback Status"] == "Paid"])
    total_amount_paid = df_filtered.loc[df_filtered["Feedback Status"] == "Paid", PAID_AMOUNT_COL].sum()

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Total Calls", f"{total_calls:,}")
    with kpi_cols[1]:
        st.metric("Total P2P", f"{total_p2p:,}")
    with kpi_cols[2]:
        st.metric("Total Paid Status", f"{total_paid_status:,}")
    with kpi_cols[3]:
        st.metric(f"Total {PAID_AMOUNT_COL}", safe_currency(total_amount_paid))
    st.markdown("---")

    # Charts...
    col1, col2 = st.columns(2)
    try:
        with col1:
            st.markdown("#### **Call Responses**")
            status_counts = df_filtered["Feedback Status"].value_counts().reset_index()
            if not status_counts.empty:
                status_counts.columns = ["Status", "Count"]
                fig = px.pie(status_counts, names="Status", values="Count", title="Distribution", hole=0.3)
                config = {"displayModeBar": True,"responsive": True}  # makes chart stretch to container width
                st.plotly_chart(fig, config=config, width='stretch')
                #st.plotly_chart(fig, width='stretch')
            else:
                st.caption("No status data.")

            st.markdown("#### **Calls by Product**")
            prod_counts = df_filtered[PRODUCT_NAME_COL].value_counts().reset_index() if PRODUCT_NAME_COL in df_filtered else pd.DataFrame()
            if not prod_counts.empty:
                prod_counts.columns = ["Product", "Count"]
                fig = px.bar(prod_counts, x="Product", y="Count", title="Follow-ups")
                config = {"displayModeBar": True,"responsive": True}  # makes chart stretch to container width
                st.plotly_chart(fig, config=config, width='stretch')
                #st.plotly_chart(fig, width='stretch')
            else:
                st.caption("No product data.")
        with col2:
            st.markdown("#### **Calls by Staff**")
            staff_counts = df_filtered["Staff Name"].value_counts().reset_index()
            if not staff_counts.empty:
                staff_counts.columns = ["Staff", "Count"]
                fig = px.bar(staff_counts, x="Staff", y="Count", title="Total Calls")
                config = {"displayModeBar": True,"responsive": True}  # makes chart stretch to container width
                st.plotly_chart(fig, config=config, width='stretch')
                #st.plotly_chart(fig, width='stretch')
            else:
                st.caption("No staff data.")
            st.markdown("#### **Calls by OD Bucket**")
            bucket_counts = df_filtered[OVERDUE_BUCKET_COL].value_counts().reset_index() if OVERDUE_BUCKET_COL in df_filtered else pd.DataFrame()
            if not bucket_counts.empty:
                bucket_counts.columns = ["Bucket", "Count"]
                fig = px.bar(bucket_counts, x="Bucket", y="Count", title="Follow-ups")
                config = {"displayModeBar": True,"responsive": True}  # makes chart stretch to container width
                st.plotly_chart(fig, config=config, width='stretch')
                #st.plotly_chart(fig, width='stretch')
            else:
                st.caption("No bucket data.")
    except Exception as e:
        st.error(f"Chart error: {e}")
        st.exception(e)

    add_footer()

def show_admin_page():
    """Renders the Manager Admin Page."""
    st.subheader("**Manager Admin Panel: Assign Work**")
    df_master = load_data(DATA_FILE)
    if df_master is None or (isinstance(df_master, pd.DataFrame) and df_master.empty):
        st.error("Cannot load master data.")
        all_branches, all_products = [], []
    else:
        all_branches = sorted(df_master[BRANCH_COL].dropna().unique()) if BRANCH_COL in df_master else []
        all_products = sorted(df_master[PRODUCT_NAME_COL].dropna().unique()) if PRODUCT_NAME_COL in df_master else []
    telecallers = get_all_users(role_filter="Telecaller")
    all_assignments = load_assignments()
    if not telecallers:
        st.warning("No telecallers found.")
        add_footer()
        st.stop()

    # --- Current Assignments ---
    st.markdown("---")
    st.markdown("### **Current Assignment List**")
    st.caption("Read-only view.")
    for tc in telecallers:
        tc_name = tc.get("name", "?")
        tc_username = tc.get("username")
        if not tc_username:
            continue
        tc_assignments = all_assignments.get(tc_username, {})
        with st.expander(f"**{tc_name}** ({tc_username})"):
            branches = tc_assignments.get("branches", [])
            products = tc_assignments.get("products", [])
            loans = tc_assignments.get("loans", [])
            branches = branches if isinstance(branches, list) else []
            products = products if isinstance(products, list) else []
            loans = loans if isinstance(loans, list) else []
            display_branches = [b for b in branches if b in all_branches]
            display_products = [p for p in products if p in all_products]
            st.multiselect(f"Branches ({len(branches)})", display_branches, default=display_branches, disabled=True, key=f"d_br_{tc_username}")
            st.multiselect(f"Products ({len(products)})", display_products, default=display_products, disabled=True, key=f"d_pr_{tc_username}")
            st.text_area(f"Loans ({len(loans)})", "\n".join(loans), height=100, disabled=True, key=f"d_ln_{tc_username}")
    st.markdown("---")

    # --- Edit Form ---
    st.markdown("### **Edit Assignments**")
    telecaller_map = {tc["name"]: tc["username"] for tc in telecallers}
    if not telecaller_map:
        st.warning("No telecallers.")
        return
    selected_name = st.selectbox("Select Telecaller to **Edit**", telecaller_map.keys())
    if not selected_name:
        return
    selected_username = telecaller_map[selected_name]
    current_assignments = all_assignments.get(selected_username, {})
    default_branches = [b for b in (current_assignments.get("branches", []) if isinstance(current_assignments.get("branches"), list) else []) if b in all_branches]
    default_products = [p for p in (current_assignments.get("products", []) if isinstance(current_assignments.get("products"), list) else []) if p in all_products]
    default_loans = current_assignments.get("loans", []) if isinstance(current_assignments.get("loans"), list) else []

    with st.form("assignment_form"):
        st.markdown(f"#### **Editing:** **{selected_name}** ({selected_username})")
        assigned_branches = st.multiselect("**Branches** (Leave blank=All)", all_branches, default=default_branches)
        assigned_products = st.multiselect("**Products** (Leave blank=All)", all_products, default=default_products)
        st.markdown("**Specific Loan IDs** (Overrides Branch/Product)")
        loans_text = "\n".join(default_loans)
        assigned_loans_text = st.text_area("Loan IDs (comma or newline separated)", value=loans_text, height=150)
        st.markdown("---")
        save_button = st.form_submit_button("Save Assignments", width='stretch')
        if save_button:
            assigned_loans = [ln.strip() for item in assigned_loans_text.split(",") for ln in item.split("\n") if ln.strip()]
            all_assignments[selected_username] = {
                "branches": assigned_branches if assigned_branches is not None else [],
                "products": assigned_products if assigned_products is not None else [],
                "loans": assigned_loans,
            }
            if save_assignments(all_assignments):
                st.success("Assignments saved!")
                try:
                    load_data.clear()
                    load_assignments.clear()
                except Exception:
                    pass
                time.sleep(0.15)
                st.rerun()

    add_footer()

def show_login_page():
    """Renders the login page."""
    login_css()
    st.markdown('<p class="main-header">💸 Maximal Finance and Investments Limited</p>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color: gold; text-align: center;">Tele Collection CRM Login</h3>', unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        with st.container():
            img_col, form_col = st.columns([0.8, 1.2])
            with img_col:
                st.image("https://img.freepik.com/free-vector/contact-center-abstract-concept-illustration_335657-3131.jpg", width=250)
            with form_col:
                st.subheader("Welcome!")
                with st.form("login_form"):
                    username = st.text_input("Username", key="login_username")
                    password = st.text_input("Password", type="password", key="login_password")
                    login_button = st.form_submit_button("Login", width='stretch')
                    if login_button:
                        auth, name, role = check_password(username, password)
                        if auth:
                            st.session_state.update(authenticated=True, user_name=name, user_role=role, username=username)
                            st.success("Login Successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
    add_footer()

# --- 5. MAIN APP RUNNER ---

def main():
    """Main function to run the app."""
    st.set_page_config(page_title="📞 Tele Collection CRM", page_icon="💸", layout="wide", initial_sidebar_state="auto")

    # Default keys
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user_name", None)
    st.session_state.setdefault("user_role", None)
    st.session_state.setdefault("username", None)

    if not st.session_state.authenticated:
        show_login_page()
    else:
        app_css()
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown('<p class="main-header">💸 Maximal Finance and Investments Limited</p>', unsafe_allow_html=True)
        with col2:
            st.caption(f"Welcome, **{st.session_state.get('user_name','User')}** ({st.session_state.get('user_role','Role')})")
            if st.button("Logout", width='stretch'):
                keys_to_delete = list(st.session_state.keys())
                for key in keys_to_delete:
                    del st.session_state[key]
                st.rerun()

        # Menu
        menu_options = ["Telecaller CRM"]
        menu_icons = ["headset"]
        if st.session_state.get("user_role") == "Manager":
            menu_options.extend(["Manager Dashboard", "Manager Admin"])
            menu_icons.extend(["bar-chart-line-fill", "person-fill-gear"])

        selected_page = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#f0f2f6", "border-radius": "5px", "margin-bottom": "15px"},
                "icon": {"color": "#264653", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#0e0fed", "color": "white"},
            },
        )

        # Page routing
        if selected_page == "Telecaller CRM":
            show_crm_page()
        elif selected_page == "Manager Dashboard":
            if st.session_state.get("user_role") == "Manager":
                show_dashboard_page()
            else:
                st.error("Access Denied.")
                add_footer()
        elif selected_page == "Manager Admin":
            if st.session_state.get("user_role") == "Manager":
                show_admin_page()
            else:
                st.error("Access Denied.")
                add_footer()

if __name__ == "__main__":
    main()