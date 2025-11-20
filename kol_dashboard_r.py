import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt
import calendar
import os
import base64
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
from streamlit_calendar import calendar as st_calendar

# -----------------------------------------------------------------
# 1. Page Config & CSS
# -----------------------------------------------------------------
st.set_page_config(
    page_title="MEDIT KOL Dashboard",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #111111;
            background-color: #F7F9FC;
        }
        
        /* KPI Card */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        div[data-testid="metric-container"] label {
            font-size: 1.1rem !important;
            color: #555 !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 2.5rem !important;
            color: #2D5AF5 !important;
            font-weight: 800 !important;
        }

        /* Content Card */
        .content-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #E0E0E0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
            margin-bottom: 20px;
        }
        
        /* Headers */
        h1 { font-size: 2.8rem !important; font-weight: 800 !important; color: #000 !important; margin-bottom: 1rem !important; }
        h2 { font-size: 1.8rem !important; font-weight: 700 !important; color: #111 !important; border-left: 5px solid #2D5AF5; padding-left: 15px; margin-top: 2rem !important; }
        h3 { font-size: 1.4rem !important; font-weight: 600 !important; color: #333 !important; }
        
        /* DataFrame */
        thead tr th {
            background-color: #2D5AF5 !important; 
            color: #FFFFFF !important; 
            font-size: 15px !important;
        }

        /* Sidebar Profile Card */
        .profile-card {
            background-color: #F0F7FF;
            border: 1px solid #2D5AF5;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .profile-name {
            color: #2D5AF5;
            font-size: 1.4rem;
            font-weight: 700;
            margin: 0;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# -----------------------------------------------------------------
# 2. Constants & Settings
# -----------------------------------------------------------------
GOOGLE_MAPS_API_KEY = "AIzaSyAVIHGVbAa47uwyQvo0OKW7Hu7M1DVrpYI" 

FILE_SETTINGS = {
    "FILE_PATH": "(KOL) DATA_251117.xlsx",
    "CONTRACT_TAB": "contracts",
    "TRACKING_TAB": "tracking"
}

YEAR = 2025 

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
MONTH_LIST_SORTED = list(MONTH_MAP.keys())

WEEK_START_DAY = {
    "1w": 1, "2w": 8, "3w": 15, "4w": 22, "5w": 29
}

ACTIVITY_TO_TASK_MAP = {
    'Lecture': 'Lecture', 'offline lecture': 'Lecture', 'ADF Lecture': 'Lecture',
    'Academy lectures': 'Lecture', 'Academy': 'Lecture',
    'Hands-on course': 'Lecture', 'Hands on training': 'Lecture', 'Skill up Seminar': 'Lecture',
    'case report': 'Case Report', 'Article case': 'Case Report', 'Clinical case report': 'Case Report',
    'T-series case report': 'Case Report',
    'Article': 'Article', 'Clinical Paper': 'Article',
    'Webinar': 'Webinar', 'Testimonial': 'Testimonial',
    'Contents creation': 'SNS Posting', 'ContentsCreation': 'SNS Posting',
    'social activities': 'SNS Posting', 'Social engagement': 'SNS Posting', 'Social Media': 'SNS Posting'
}

EVENT_COLORS = {
    'Lecture': '#2D5AF5', 'Case Report': '#00C4CC', 'SNS Posting': '#FF6B6B', 
    'Article': '#FF9F43', 'Webinar': '#A3CB38', 'Testimonial': '#6C5CE7'
}

COLOR_MEDIT_BLUE = "#2D5AF5"
COLOR_MEDIT_DARK = "#1A2B3C"
COLOR_MEDIT_LIGHT = "#E6F0FF"
COLOR_GREY_TEXT = "#555555"
COLOR_LIGHT_GREY = "#F0F0F0"
COLOR_ACCENT = "#00A9E0"
COLOR_DANGER = "#FF6B6B"
COLOR_BG_BAR = "#E9ECEF"
COLOR_TEXT = "#111111"
COLOR_PRIMARY = "#2D5AF5"

# -----------------------------------------------------------------
# 3. Helper Functions
# -----------------------------------------------------------------

def metric_card(title, value, delta_text=None, delta_type="neutral"):
    delta_color = "#888"
    if delta_type == "positive": delta_color = "#00C4CC"
    elif delta_type == "negative": delta_color = "#FF6B6B"
    
    delta_html = f'<div class="metric-delta" style="color:{delta_color}; margin-top:5px; font-size:0.9rem;">{delta_text}</div>' if delta_text else ""
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label" style="color:#666; font-weight:600; font-size:0.9rem;">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data(excel_file_path, contract_tab, tracking_tab):
    try:
        df_plan = pd.read_excel(excel_file_path, sheet_name=contract_tab, engine='openpyxl')
        df_actual = pd.read_excel(excel_file_path, sheet_name=tracking_tab, engine='openpyxl')
        
        df_plan = df_plan.dropna(subset=['KOL_ID'])
        df_actual = df_actual.dropna(subset=['KOL_ID'])
        df_plan['KOL_ID'] = pd.to_numeric(df_plan['KOL_ID'], errors='coerce').astype(int)
        df_actual['KOL_ID'] = pd.to_numeric(df_actual['KOL_ID'], errors='coerce').astype(int)
        df_plan['Contract Start'] = pd.to_datetime(df_plan['Contract Start'])
        df_plan['Contract End'] = pd.to_datetime(df_plan['Contract End'])
        df_plan['Frequency'] = pd.to_numeric(df_plan['Frequency'], errors='coerce')
        
        def find_col(df, options):
            for col in options:
                if col in df.columns: return col
            return None
        lat_col = find_col(df_plan, ['lat', 'Lat', 'Latitude'])
        lon_col = find_col(df_plan, ['lon', 'Lon', 'Longitude'])
        if lat_col and lon_col:
            df_plan['lat'] = pd.to_numeric(df_plan[lat_col], errors='coerce')
            df_plan['lon'] = pd.to_numeric(df_plan[lon_col], errors='coerce')
        else:
            df_plan['lat'] = np.nan
            df_plan['lon'] = np.nan
        return df_plan, df_actual
    except Exception as e:
        st.error(f"Data Load Error: {e}"); return None, None

@st.cache_data
def get_dashboard_data(df_plan, df_actual, _today):
    report_date = _today
    default_start = pd.to_datetime(f"{YEAR}-01-01")
    default_end = pd.to_datetime(f"{YEAR}-12-31")
    df_plan['Contract Start'] = df_plan['Contract Start'].fillna(default_start)
    df_plan['Contract End'] = df_plan['Contract End'].fillna(default_end)
    
    kol_master = df_plan.groupby('KOL_ID').agg(
        Name=('Name', 'first'), Area=('Area', 'first'), Country=('Country', 'first'), 
        Contract_Start=('Contract Start', 'min'), Contract_End=('Contract End', 'max'), 
        lat=('lat', 'first'), lon=('lon', 'first')
    ).reset_index()
    
    df_plan_grouped = df_plan.dropna(subset=['KOL_ID', 'Task', 'Frequency']).groupby(['KOL_ID', 'Task'], as_index=False)['Frequency'].sum().rename(columns={'Frequency': 'Target_Count'})
    df_plan_grouped['Target_Count'] = df_plan_grouped['Target_Count'].astype(int)
    df_plan_master = pd.merge(df_plan_grouped, kol_master, on='KOL_ID', how='left')

    df_actual_proc = df_actual.copy()
    df_actual_proc['Month_Num'] = df_actual_proc['Month'].map(MONTH_MAP)
    df_actual_proc['Day'] = df_actual_proc['Week'].astype(str).str.replace('w', '').astype(int).apply(lambda w: (w-1)*7 + 1)
    df_actual_proc['Year'] = YEAR
    df_actual_proc = df_actual_proc.dropna(subset=['Year', 'Month_Num', 'Day'])
    df_actual_proc['Activity_Date'] = pd.to_datetime(df_actual_proc[['Year', 'Month_Num', 'Day']].rename(columns={'Month_Num': 'Month'}))
    df_actual_to_date = df_actual_proc[df_actual_proc['Activity_Date'] <= report_date].copy()
    df_actual_to_date['Task'] = df_actual_to_date['Activity'].str.strip().map(ACTIVITY_TO_TASK_MAP)
    df_actual_counts = df_actual_to_date.dropna(subset=['Task', 'KOL_ID']).groupby(['KOL_ID', 'Task'], as_index=False).size().rename(columns={'size': 'Actual_Count'})

    df_dashboard = pd.merge(df_plan_master, df_actual_counts, on=['KOL_ID', 'Task'], how='left').fillna({'Actual_Count': 0})
    df_dashboard = df_dashboard.dropna(subset=['KOL_ID', 'Area', 'Country'])
    df_dashboard['KOL_ID'] = df_dashboard['KOL_ID'].astype(int)
    df_dashboard['Actual_Count'] = df_dashboard['Actual_Count'].astype(int)
    df_dashboard['Achievement_%'] = (df_dashboard['Actual_Count'] / df_dashboard['Target_Count']).replace([np.inf, -np.inf], 0).fillna(0) * 100
    
    df_dashboard['Total_Days'] = (df_dashboard['Contract_End'] - df_dashboard['Contract_Start']).dt.days
    df_dashboard['Elapsed_Days'] = (report_date - df_dashboard['Contract_Start']).dt.days.clip(lower=0)
    df_dashboard.loc[df_dashboard['Elapsed_Days'] > df_dashboard['Total_Days'], 'Elapsed_Days'] = df_dashboard['Total_Days']
    df_dashboard['Elapsed_%'] = 0.0
    valid = df_dashboard['Total_Days'] > 0
    df_dashboard.loc[valid, 'Elapsed_%'] = (df_dashboard.loc[valid, 'Elapsed_Days'] / df_dashboard.loc[valid, 'Total_Days']) * 100
    df_dashboard['Expected_Count'] = df_dashboard['Target_Count'] * (df_dashboard['Elapsed_%'] / 100.0)
    df_dashboard['Pacing_Progress_%'] = 0.0
    normal = df_dashboard['Expected_Count'] > 0
    df_dashboard.loc[normal, 'Pacing_Progress_%'] = (df_dashboard['Actual_Count'] / df_dashboard['Expected_Count']) * 100.0
    mask_ns = df_dashboard['Expected_Count'] == 0
    df_dashboard.loc[mask_ns & (df_dashboard['Actual_Count'] > 0), 'Pacing_Progress_%'] = 100.0
    
    def get_status(row):
        if row['Achievement_%'] >= 100: return "Completed"
        if row['Target_Count'] == 0: return "N/A"
        if row['Elapsed_%'] == 0 and row['Actual_Count'] == 0: return "Not Started"
        if row['Pacing_Progress_%'] >= 100: return "On Track"
        return "Delayed"
    df_dashboard['Status'] = df_dashboard.apply(get_status, axis=1)
    df_dashboard['Gap'] = (df_dashboard['Target_Count'] - df_dashboard['Actual_Count']).apply(lambda x: max(x, 0)).astype(int)
    return df_dashboard, df_actual_to_date, kol_master

def render_google_map(data):
    if data.empty: return "<div>No data</div>"
    map_data_json = data[['Name', 'lat', 'lon', 'Area', 'Country']].to_json(orient='records')
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
        <style> 
            #map {{ height: 500px; width: 100%; border-radius: 12px; border: 1px solid #E0E0E0; }} 
            .info-window {{ padding: 10px; color: #111; font-family: sans-serif; font-size: 14px; }}
            .info-title {{ color: #2D5AF5; font-weight: 700; font-size: 16px; margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                const locations = {map_data_json};
                const center = locations.length > 0 && locations[0].lat ? {{ lat: locations[0].lat, lng: locations[0].lon }} : {{ lat: 30, lng: 20 }};
                
                const map = new google.maps.Map(document.getElementById("map"), {{ 
                    zoom: 2, center: center, 
                    mapId: "DEMO_MAP_ID", mapTypeId: 'roadmap', disableDefaultUI: false 
                }});
                const infoWindow = new google.maps.InfoWindow();
                locations.forEach(loc => {{
                    if (loc.lat && loc.lon) {{
                        const marker = new google.maps.Marker({{ position: {{ lat: loc.lat, lng: loc.lon }}, map: map, title: loc.Name }});
                        marker.addListener("click", () => {{
                            infoWindow.setContent(`<div class="info-window"><div class="info-title">${{loc.Name}}</div><div>${{loc.Country}}</div></div>`);
                            infoWindow.open(map, marker);
                        }});
                    }}
                }});
            }}
            window.onload = initMap;
        </script>
    </body>
    </html>
    """
    return html_code

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border:none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def create_pie_chart(data, category_col, value_col, title):
    base = alt.Chart(data).encode(theta=alt.Theta(f"{value_col}:Q", stack=True)).properties(title=alt.Title(title, fontSize=16, color=COLOR_GREY_TEXT))
    pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(
        color=alt.Color(f"{category_col}:N", scale=alt.Scale(scheme='blues'), legend=None),
        order=alt.Order(f"{value_col}:Q", sort="descending"),
        tooltip=[category_col, value_col]
    )
    text = base.mark_text(radius=120).encode(
        text=alt.Text(f"{value_col}:Q", format=".0f"),
        order=alt.Order(f"{value_col}:Q", sort="descending"),
        color=alt.value(COLOR_TEXT)
    )
    return pie + text

def create_simple_bar(data, x, y, title):
    base = alt.Chart(data).encode(x=alt.X(x, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y(y, title=None))
    bar = base.mark_bar(color=COLOR_PRIMARY, cornerRadius=3).encode(tooltip=[x, y])
    text = base.mark_text(dy=-10, color=COLOR_TEXT).encode(text=alt.Text(y, format=',.0f'))
    return (bar + text).properties(title=alt.Title(title, fontSize=16, color=COLOR_GREY_TEXT), height=250).interactive()

def create_horizontal_bar(data, y_col, x_col, title, color_col, x_title, row_col=None):
    chart = alt.Chart(data).mark_bar(cornerRadius=2, color=COLOR_MEDIT_BLUE).encode(
        x=alt.X(f"{x_col}:Q", title=x_title, axis=alt.Axis(grid=False, labelColor=COLOR_GREY_TEXT, titleColor=COLOR_GREY_TEXT, labelFontSize=12)),
        y=alt.Y(f"{y_col}:N", sort="-x", axis=alt.Axis(labelColor=COLOR_TEXT, titleColor=COLOR_GREY_TEXT, labelFontSize=13, title=None)),
        tooltip=[y_col, color_col, x_col]
    ).properties(title=alt.Title(title, color=COLOR_GREY_TEXT, fontSize=16)).interactive()
    
    if row_col:
        chart = chart.encode(
            row=alt.Row(f"{row_col}:N", header=alt.Header(titleOrient="top", labelOrient="top", titleColor=COLOR_GREY_TEXT, labelColor=COLOR_GREY_TEXT, labelFontSize=14, titleFontSize=14), sort='ascending')
        )
    return chart

def create_pacing_donut(percent, title):
    vis_val = min(percent / 100.0, 1.0)
    source = pd.DataFrame({"category": ["A", "B"], "value": [vis_val, 1-vis_val]})
    base = alt.Chart(source).encode(theta=alt.Theta("value", stack=True))
    pie = base.mark_arc(outerRadius=60, innerRadius=45).encode(
        color=alt.Color("category", scale={"domain": ["A", "B"], "range": [COLOR_MEDIT_BLUE, COLOR_LIGHT_GREY]}, legend=None),
    )
    text = alt.Chart(pd.DataFrame({'value': [f"{percent:.1f}%"]})).mark_text(
        align='center', fontSize=24, fontWeight=700, color=COLOR_MEDIT_BLUE
    ).encode(text='value')
    return (pie + text).properties(title=alt.Title(title, fontSize=14, color=COLOR_GREY_TEXT, offset=10)).configure_view(strokeWidth=0)

def create_donut_chart(percent, title):
    percent = max(0, min(percent, 1.0))
    source = pd.DataFrame({"category": ["A", "B"], "value": [percent, 1-percent]})
    base = alt.Chart(source).encode(theta=alt.Theta("value", stack=True))
    pie = base.mark_arc(outerRadius=60, innerRadius=45).encode(
        color=alt.Color("category", scale={"domain": ["A", "B"], "range": [COLOR_MEDIT_BLUE, COLOR_LIGHT_GREY]}, legend=None),
        order=alt.Order("category", sort="descending")
    )
    text = alt.Chart(pd.DataFrame({'value': [f"{percent:.1%}"]})).mark_text(
        align='center', fontSize=24, fontWeight=700, color=COLOR_MEDIT_BLUE
    ).encode(text='value')
    return (pie + text).properties(title=alt.Title(title, fontSize=14, color=COLOR_GREY_TEXT, offset=10)).configure_view(strokeWidth=0)

# -----------------------------------------------------------------
# 4. Main Application
# -----------------------------------------------------------------

with st.sidebar:
    st.image("https://medit-web-gcs.s3.ap-northeast-2.amazonaws.com/files/2023-01-31/0d273f0d-e461-4c6e-82f5-19e09d17208d/MEDIT_CI_Dark.png", width=160)
    st.markdown("<br>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Executive Dashboard", "Admin Dashboard"], label_visibility="collapsed")
    
    st.divider()
    st.subheader("Settings")
    selected_month_name = st.select_slider("As-of-Month:", options=MONTH_LIST_SORTED, value="November")
    selected_month_num = MONTH_MAP[selected_month_name]
    last_day = calendar.monthrange(YEAR, selected_month_num)[1]
    TODAY = pd.to_datetime(datetime.date(YEAR, selected_month_num, last_day))
    st.caption(f"Base Date: {TODAY.strftime('%Y-%m-%d')}")
    
    st.divider()
    st.subheader("KOL Profile Look-up")
    
    try:
        df_plan_raw, df_actual_raw = load_data(FILE_SETTINGS["FILE_PATH"], FILE_SETTINGS["CONTRACT_TAB"], FILE_SETTINGS["TRACKING_TAB"])
        if df_plan_raw is not None:
            df_dashboard, _, kol_master = get_dashboard_data(df_plan_raw, df_actual_raw, TODAY)
            kol_list_sorted = sorted(df_dashboard['Name'].unique())
            selected_kol = st.selectbox("Select KOL:", options=kol_list_sorted, index=None, placeholder="Search Name...", label_visibility="collapsed")

            if selected_kol:
                kol_data = df_dashboard[df_dashboard['Name'] == selected_kol].reset_index(drop=True)
                if not kol_data.empty:
                    kol_info = kol_data.iloc[0]
                    
                    st.markdown(f"""
                    <div class="profile-card">
                        <h4 class="profile-name">{kol_info['Name']}</h4>
                        <p style="font-size:0.9rem; color:#555; margin-top:5px;">{kol_info['Country']} | {kol_info['Area']}</p>
                        <p style="font-size:0.85rem; color:#888; margin-top:2px;">
                           Contract: {kol_info['Contract_Start'].strftime('%y.%m.%d')} ~ {kol_info['Contract_End'].strftime('%y.%m.%d')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.progress(min(kol_info['Elapsed_%']/100, 1.0), text=f"Contract Elapsed: {kol_info['Elapsed_%']:.1f}%")

                    pdf_filename = f"{kol_info['Name']}.pdf"
                    pdf_path = os.path.join("profiles", pdf_filename)
                    if os.path.exists(pdf_path):
                        with st.expander("📄 View Profile (PDF)", expanded=False):
                            show_pdf(pdf_path)
                    else:
                        st.caption(f"No PDF Found ({pdf_filename})")
                    
                    st.dataframe(kol_data[['Task', 'Status', 'Pacing_Progress_%']].style.format({'Pacing_Progress_%': '{:.0f}%'}), use_container_width=True, hide_index=True)
            expiry_date_limit = TODAY + pd.Timedelta(days=30)
    except Exception: pass

if df_plan_raw is None: st.stop()
df_dashboard, df_actual_to_date, kol_master = get_dashboard_data(df_plan_raw, df_actual_raw, TODAY)

if page == "Executive Dashboard":
    
    # 1. KPI Cards
    total_target = df_dashboard['Target_Count'].sum()
    total_actual = df_dashboard['Actual_Count'].sum()
    annual_perc = (total_actual / total_target) * 100 if total_target > 0 else 0
    
    cumulative_pacing = []
    for month_name, month_num in MONTH_MAP.items():
        month_end_day = calendar.monthrange(YEAR, month_num)[1]
        report_date = pd.to_datetime(datetime.date(YEAR, month_num, month_end_day))
        avg_pacing_perc = 0.0
        if report_date <= TODAY:
            df_tmp, _, _ = get_dashboard_data(df_plan_raw, df_actual_raw, report_date)
            in_prog = df_tmp[df_tmp['Status'].isin(['On Track', 'Delayed'])]
            if not in_prog.empty: avg_pacing_perc = in_prog['Pacing_Progress_%'].mean()
        cumulative_pacing.append({'Month': month_name, 'Pacing': avg_pacing_perc})
    df_pacing_trend = pd.DataFrame(cumulative_pacing)
    current_pacing = df_pacing_trend.loc[df_pacing_trend['Month'] == selected_month_name, 'Pacing'].values[0]
    delayed = len(df_dashboard[df_dashboard['Status'] == 'Delayed'])
    expiring = len(kol_master[(kol_master['Contract_End'] > TODAY) & (kol_master['Contract_End'] <= expiry_date_limit)])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: metric_card("Total KOLs", f"{len(kol_master)}")
    with col2: metric_card("Avg. Pacing", f"{current_pacing:.1f}%", "Target: 100%")
    with col3: metric_card("Delayed Tasks", f"{delayed}", "Needs Attention", "negative")
    with col4: metric_card("Expiring Contracts", f"{expiring}", "Next 30 Days")
    
    st.markdown("---")
    
    # 2. Main Charts (3 Columns)
    st.markdown("### 📊 Performance Trends")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("**📆 Monthly Activity**")
        monthly_vol = df_actual_raw.groupby('Month')['Activity'].count().reindex(MONTH_LIST_SORTED).fillna(0).reset_index()
        st.altair_chart(create_simple_bar(monthly_vol, 'Month', 'Activity', ''), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("**🌍 Regional Distribution**")
        region_dist = df_dashboard.groupby('Area')['Target_Count'].sum().reset_index()
        st.altair_chart(create_pie_chart(region_dist, 'Area', 'Target_Count', ''), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("**⚠️ Status Breakdown**")
        status_counts = df_dashboard['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        chart3 = alt.Chart(status_counts).mark_bar(cornerRadius=3).encode(
            x=alt.X('Count', title=None), y=alt.Y('Status', sort='-x', title=None), 
            color=alt.Color('Status', scale=alt.Scale(domain=['Completed', 'On Track', 'Delayed', 'Not Started'], range=[COLOR_MEDIT_BLUE, COLOR_ACCENT, COLOR_DANGER, COLOR_BG_BAR]), legend=None)
        ).properties(height=250)
        st.altair_chart(chart3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # 3. Map & Calendar
    m1, m2 = st.columns([3, 2])
    with m1:
        st.markdown("### 🗺️ Global Activity Map")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        df_map = kol_master.dropna(subset=['lat', 'lon'])
        if not df_map.empty: components.html(render_google_map(df_map), height=400)
        else: st.info("No location data found.")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f"### 📅 {selected_month_name} Schedule")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        monthly_schedule = df_actual_raw[(df_actual_raw['Month'] == selected_month_name) & (df_actual_raw['KOL_ID'].isin(df_dashboard['KOL_ID']))].copy()
        if not monthly_schedule.empty:
            calendar_events = []
            for _, row in monthly_schedule.iterrows():
                try:
                    month_num = MONTH_MAP[row['Month']]
                    start_day = WEEK_START_DAY.get(str(row['Week']), 1)
                    start_date = f"{YEAR}-{month_num:02d}-{start_day:02d}"
                    end_day = min(start_day+6, calendar.monthrange(YEAR, month_num)[1])
                    end_date = f"{YEAR}-{month_num:02d}-{end_day:02d}"
                    color = EVENT_COLORS.get(ACTIVITY_TO_TASK_MAP.get(row['Activity'].strip(), 'Other'), '#888')
                    calendar_events.append({"title": f"{row['Name']}", "start": start_date, "end": end_date, "backgroundColor": color, "borderColor": color, "allDay": True})
                except: continue
            st_calendar(events=calendar_events, options={"initialDate": f"{YEAR}-{selected_month_num:02d}-01", "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"}, "height": 400})
        else: st.info("No activities scheduled.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # 4. Delayed List
    st.markdown("### ⚠️ Delayed Tasks")
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    df_inc = df_dashboard[df_dashboard['Status'] != 'Completed'].sort_values(by='Pacing_Progress_%')
    def highlight_pacing(val):
        color = '#FFF5F5' if val < 100 else '#F0F9FF'
        return f'background-color: {color}'
    st.dataframe(df_inc[['Name', 'Task', 'Status', 'Pacing_Progress_%', 'Gap']].style.applymap(highlight_pacing, subset=['Pacing_Progress_%']).format({'Pacing_Progress_%': '{:.1f}%'}), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Admin Page ---
elif page == "Admin Dashboard":
    st.title("Admin Data View")
    st.markdown("#### 📂 Activity Log")
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    f_area = c1.selectbox("Area", ["All"] + sorted(df_actual_raw['Area'].dropna().unique().tolist()))
    f_month = c2.selectbox("Month", ["All"] + MONTH_LIST_SORTED)
    df_log = df_actual_raw.copy()
    if f_area != "All": df_log = df_log[df_log['Area'] == f_area]
    if f_month != "All": df_log = df_log[df_log['Month'] == f_month]
    st.dataframe(df_log, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)