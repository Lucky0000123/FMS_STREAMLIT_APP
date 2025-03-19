import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import tempfile
import pythoncom
import datetime
from docx2pdf import convert as docx2pdf_convert
from mailmerge import MailMerge
from io import BytesIO
from utils import render_glow_line, load_data, switch_theme, load_lottie_json
import time
from streamlit_lottie import st_lottie
import concurrent.futures
from PyPDF2 import PdfMerger
import threading


# --------------------------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Driver Performance & Warning Letters",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize or load data
if 'df' not in st.session_state or st.session_state.df.empty:
    st.session_state.df = load_data()  # Assuming load_data handles loading the dataset and returns a DataFrame

# Use the loaded data
df = st.session_state.df
# --------------------------------------------------------------------
# LANGUAGE TOGGLE
# --------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state["language"] = "EN"

def toggle_language():
    st.session_state["language"] = "ZH" if st.session_state["language"] == "EN" else "EN"

# Create a row with two columns: left for JSON animation, right for the translation button
col_json, col_trans = st.columns([1.0, 1])
with col_trans:
    st.markdown("### Click here for Translation")
    translation_label = "切换中文" if st.session_state.get("language", "EN") == "EN" else "Click to Translate"
    st.button(translation_label, on_click=toggle_language)
with col_json:
    # Load and display the Lottie JSON animation (update the path as needed)
    lottie_json = load_lottie_json("assets/ani6.json")
    if lottie_json:
        st_lottie(lottie_json, speed=1, width=300, height=200)



# --------------------------------------------------------------------
# TRANSLATION HELPER
# --------------------------------------------------------------------
def t(en_text, zh_text):
    return zh_text if st.session_state["language"] == "ZH" else en_text

render_glow_line()

# --------------------------------------------------------------------
# PAGE TITLE
# --------------------------------------------------------------------
st.title(t("Driver Performance & Warning Letters", "驾驶员绩效与警告信"))
render_glow_line()
# --------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------
if "df" not in st.session_state or st.session_state.df.empty:
    st.error(t("No data loaded. Please load data on homepage.", "未加载数据，请在主页上传数据"))
    st.stop()

df = st.session_state.df.copy()
df["Shift Date"] = pd.to_datetime(df["Shift Date"]).dt.date

# --------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------
st.sidebar.header(t("📅 Date Range Filter", "📅 日期范围筛选"))
min_date, max_date = df["Shift Date"].min(), df["Shift Date"].max()
date_range = st.sidebar.date_input(
    t("Select Date Range", "选择日期范围"),
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
start_date, end_date = (date_range[0], date_range[1]) if len(date_range) == 2 else (date_range[0], date_range[0])
df_filtered = df[(df["Shift Date"] >= start_date) & (df["Shift Date"] <= end_date)]

# Save the date range in session_state as part of the selections
st.session_state["selections"] = {"dates": (start_date, end_date)}

# --------------------------------------------------------------------
# KPI CARDS
# --------------------------------------------------------------------
st.markdown("<h3 style='margin-bottom:20px;'>📊 Performance Overview</h3>", unsafe_allow_html=True)

# Calculate metrics
total_drivers = df["Driver"].nunique()
high_risk_pct = (df_filtered[df_filtered["Overspeeding Value"] >= 15]["Driver"].nunique() / df_filtered["Driver"].nunique() * 100) if df_filtered["Driver"].nunique() > 0 else 0
total_violations = df_filtered[df_filtered["Overspeeding Value"] >= 6].shape[0]

# Create cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-radius:10px;border:1px solid #eee;margin-bottom:20px">
        <h4 style="margin:0;color:#2a3f5f;">{t('Total Drivers with names (in Database)', '有姓名的司机总数（数据库中）')}</h4>
        <h1 style="margin:0;color:#1D5B79;">{total_drivers}</h1>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-radius:10px;border:1px solid #eee;margin-bottom:20px">
        <h4 style="margin:0;color:#2a3f5f;">{t('High/Extreme-Risk Drivers', '高风险/极端风险驾驶员')}</h4>
        <h1 style="margin:0;color:#FFA500;">{high_risk_pct:.1f}%</h1>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background:#f8f9fa;padding:20px;border-radius:10px;border:1px solid #eee;margin-bottom:20px">
        <h4 style="margin:0;color:#2a3f5f;">{t('Total Over speeding Violations', '超速违规总数')}</h4>
        <h1 style="margin:0;color:#F24C3D;">{total_violations}</h1>
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------------------------
# DRIVER PERFORMANCE CHARTS
# --------------------------------------------------------------------
render_glow_line()
st.markdown("<h3 style='margin-bottom:20px;'>📈 Top 10 Risky Drivers</h3>", unsafe_allow_html=True)

# Top 10 Drivers Chart
driver_stats = df_filtered.groupby("Driver")["Overspeeding Value"].mean().reset_index()
top_drivers = driver_stats.sort_values("Overspeeding Value", ascending=False).head(10)
fig1 = px.bar(top_drivers, x="Driver", y="Overspeeding Value", 
             title=t("Top 10 Risky Drivers", "风险最高的10名驾驶员"),
             color="Overspeeding Value", color_continuous_scale="OrRd")
st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------------------------
# TOP 15 DRIVERS BY WARNING LETTERS
# --------------------------------------------------------------------
render_glow_line()
st.subheader(t(" Top 15 Drivers with Maximum Warning Letters",
               " 收到警告信最多的前15名驾驶员"))

# Ensure "Driver" column is cleaned and remove blank names
df_filtered["Driver"] = df_filtered["Driver"].fillna("").astype(str).str.strip()
valid_drivers_df = df_filtered[(df_filtered["Overspeeding Value"] >= 6) & (df_filtered["Driver"] != "")]

# Ensure unique warning letters per (Driver, Shift Date, Shift)
letters_df = valid_drivers_df.drop_duplicates(subset=["Driver", "Shift Date", "Shift"])

# Group by Driver and count warning letters
top_letters = letters_df.groupby("Driver").size().reset_index(name="Letters")

# Sort by count and take top 15
top_letters = top_letters.sort_values("Letters", ascending=False).head(15)

# Generate the bar chart with a stylish color palette
fig_top15 = px.bar(
    top_letters,
    x="Driver",
    y="Letters",
    color="Letters",
    color_continuous_scale="oranges",  # 🔥 More vibrant color scheme
    title=t("Top 15 Drivers by Warning Letters (Selected Range)",
            "在所选范围内警告信最多的15名驾驶员"),
    text="Letters"  # Show count on bars
)

# Improve layout
fig_top15.update_traces(
    texttemplate='%{text}', 
    textposition='outside'
)
fig_top15.update_layout(
    title_x=0.5, 
    xaxis_title=t("Driver", "驾驶员"), 
    yaxis_title=t("Warning Letters", "警告信"),
    xaxis_tickangle=-45,
    plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=60, b=60)
)

# Show the chart
st.plotly_chart(fig_top15, use_container_width=True)

# --------------------------------------------------------------------
# WARNING LETTERS TABLE (ROW-WISE)
# --------------------------------------------------------------------
render_glow_line()
st.markdown(f"<h3 style='margin-bottom:20px;'>{t('📋 Warning Letters Summary', '📋 警告信汇总')}</h3>", unsafe_allow_html=True)

if not df_filtered.empty:
    # Only show rows with Overspeed >= 6
    warnings = df_filtered[df_filtered["Overspeeding Value"] >= 6]
    
    # Group by the original English column names
    warning_counts = (
        warnings.groupby(["Group", "Shift"])
        .size()
        .reset_index(name="Count")  # Temporary name, e.g. "Count"
    )
    
    # Rename columns for display using your translation function t()
    warning_counts.rename(
        columns={
            "Group": t("Group", "组别"),
            "Shift": t("Shift", "班次"),
            "Count": t("Warnings", "警告数量")
        },
        inplace=True
    )

    # Now that columns are renamed, you can safely set them as the index
    warning_display = warning_counts.set_index([t("Group", "组别"), t("Shift", "班次")]).T
    
    st.dataframe(warning_display, use_container_width=True)

else:
    st.info(t("No warnings in selected period", "所选期间无警告"))




# Optimized version of mailmerge_multiple_records to handle unnamed drivers more efficiently
def mailmerge_multiple_records(records, template_path="assets/warning_letter.docx"):
    """Process records in batches for better performance"""
    document = MailMerge(template_path)
    dict_list = []
    
    # Preprocess all records at once - huge performance improvement for large datasets
    # Process in chunks for very large datasets
    BATCH_SIZE = 50  # Adjust based on your system's memory capacity
    
    for i in range(0, len(records), BATCH_SIZE):
        batch = records.iloc[i:i+BATCH_SIZE]
        
        for _, row in batch.iterrows():
            # Format date fields just once
            start_time_raw = row.get("Start Time", "")
            try:
                dt_obj = pd.to_datetime(start_time_raw)
                incident_date = dt_obj.strftime("%Y-%m-%d")
                incident_time = dt_obj.strftime("%H:%M:%S")
            except:
                incident_date = str(start_time_raw)
                incident_time = str(start_time_raw)
            
            # Create dictionary with default values to avoid repeated checks
            dict_item = {
                "Driver_ID": str(row.get("Driver ID", "N/A")),
                "Driver": str(row.get("Driver", "Unknown Driver")).strip() or "Unknown Driver",
                "Group": str(row.get("Group", "Unknown Department")),
                "Start_Time": incident_time,
                "Shift_Date": incident_date,
                "Area": str(row.get("Area", "Unknown Location")),
                "Overspeeding_Value": str(row.get("Overspeeding Value", 0)),
                "Speed_Limit": str(row.get("Speed Limit", "N/A")),
                "Shift": str(row.get("Shift", "N/A")),
                "Max_SpeedKmh": str(row.get("Max Speed(Km/h)", "N/A")),
                "License_Plate": str(row.get("License Plate", "N/A"))
            }
            dict_list.append(dict_item)
    
    if dict_list:
        document.merge_pages(dict_list)
    return document

# Optimized version of convert_mailmerged_doc_to_pdf with better performance
def convert_mailmerged_doc_to_pdf(mailmerge_doc):
    """Convert document to PDF with optimized handling to reduce processing time"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        output_path_docx = tmp_docx.name
    
    # Write document only once
    mailmerge_doc.write(output_path_docx)
    output_path_pdf = output_path_docx.replace(".docx", ".pdf")
    
    # Initialize COM once per function call - critical for performance
    pythoncom.CoInitialize()
    try:
        docx2pdf_convert(output_path_docx, output_path_pdf)
    finally:
        pythoncom.CoUninitialize()
    
    # Read file into memory
    with open(output_path_pdf, "rb") as f:
        pdf_bytes = f.read()
    
    # Clean up immediately
    try:
        os.remove(output_path_docx)
        os.remove(output_path_pdf)
    except:
        pass
        
    return pdf_bytes

def overspeeding_warning_letters(df: pd.DataFrame):
    st.subheader("📋 Over-Speeding Violations & Warning Letters")

    if "selections" not in st.session_state:
        st.error("No sidebar selections found!")
        return

    selections = st.session_state["selections"]
    date_range = selections.get("dates", None)
    if not date_range or len(date_range) < 2:
        st.error("Please select a start and end date in the sidebar.")
        return

    start_date, end_date = date_range
    st.info(f"**Selected Date Range for Warning Letters:** {start_date} → {end_date}")

    overspeed_threshold = st.number_input(
        "Overspeeding Threshold (Km/h)",
        min_value=1,
        value=6,
        key="overspeed_threshold_warning"
    )

    required_cols = ["Shift Date", "Overspeeding Value", "Driver", "License Plate", "Shift", "Start Time"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        st.stop()

    df["Shift_Date_only"] = pd.to_datetime(df["Shift Date"]).dt.date
    df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
    df["License Plate"] = df["License Plate"].fillna("").astype(str).str.strip()

    filtered = df[
        (df["Shift_Date_only"] >= start_date) &
        (df["Shift_Date_only"] <= end_date) &
        (df["Overspeeding Value"] >= overspeed_threshold)
    ]

    # This button triggers the calculation and storage of named and unnamed drivers.
    if st.button("Check Over-Speeding Drivers"):
        st.write(f"**Total Over-Speeding Violations (≥ {overspeed_threshold} Km/h):** {len(filtered)}")
        st.dataframe(filtered, use_container_width=True)

        named_drivers = filtered[filtered["Driver"] != ""].drop_duplicates(subset=["Driver", "Shift_Date_only"])
        unnamed_drivers = filtered[filtered["Driver"].str.strip() == ""].drop_duplicates(
            subset=["License Plate", "Shift_Date_only", "Shift"]
        )

        st.write(f"Named Drivers (unique per driver/day): {len(named_drivers)}")
        st.write(f"Unnamed Drivers (unique per truck/shift): {len(unnamed_drivers)}")

        st.session_state["named_drivers"] = named_drivers
        st.session_state["unnamed_drivers"] = unnamed_drivers
    else:
        named_drivers = st.session_state.get("named_drivers", pd.DataFrame())
        unnamed_drivers = st.session_state.get("unnamed_drivers", pd.DataFrame())

    total_violations = len(filtered)
    named_count = len(named_drivers)
    unnamed_count = len(unnamed_drivers)
    total_letters = named_count + unnamed_count

    st.markdown(
        f"""
        <style>
            .summary-container {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #ddd;
                margin-bottom: 20px;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            }}
            .summary-title {{
                font-size: 26px;
                font-weight: 700;
                color: #2a3f5f;
                text-align: left;
                margin-bottom: 15px;
                border-bottom: 3px solid #FF8C42;
                padding-bottom: 5px;
            }}
            .summary-item {{
                font-size: 18px;
                font-weight: 500;
                color: #1D5B79;
                margin-bottom: 8px;
            }}
            .summary-value {{
                font-size: 22px;
                font-weight: bold;
                color: #F24C3D;
            }}
        </style>
        <div class="summary-container">
            <div class="summary-title">📄 Summary of Over-Speeding Letters</div>
            <div class="summary-item">Violations in Range: <span class="summary-value">{total_violations}</span></div>
            <div class="summary-item">Named Drivers (session): <span class="summary-value">{named_count}</span></div>
            <div class="summary-item">Unnamed Drivers (session): <span class="summary-value">{unnamed_count}</span></div>
            <div class="summary-item">Total Warning Letters: <span class="summary-value">{total_letters}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate PDF (Named Drivers)", key="gen_named_pdf"):
            if not named_drivers.empty:
                try:
                    # Use system-optimized number of workers
                    max_workers = min(8, os.cpu_count() or 4)
                    pdf_bytes = parallel_mailmerge_to_pdf(
                        named_drivers, 
                        template_path="assets/warning_letter.docx",
                        max_workers=max_workers
                    )
                    
                    if pdf_bytes:
                        # Use a timestamp in the filename for uniqueness
                        time_stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        st.download_button(
                            label="Download PDF (Named Drivers)",
                            data=pdf_bytes,
                            file_name=f"warning_letters_named_{time_stamp}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            else:
                st.warning("No named drivers found. Please click 'Check Over-Speeding Drivers' first.")

    
                    
    with col2:
        if st.button("Generate PDF (Unnamed Drivers)", key="gen_unnamed_pdf", help="Generate warning letters for drivers without names"):
            # Efficiently get unnamed drivers
            unnamed_drivers = filtered[filtered["Driver"].str.strip() == ""].drop_duplicates(
                subset=["License Plate", "Shift_Date_only", "Shift"]
            )
            
            if unnamed_drivers.empty:
                st.warning("No unnamed drivers found in the selected date range.")
            else:
                # Set up progress tracking with meaningful updates
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Use much faster and more realistic progress updates
                    # Step 1: Data preparation - 20%
                    status_text.write("Step 1/4: Preparing data...")
                    progress_bar.progress(20)
                    
                    # Ensure all required fields are filled with placeholders - only once
                    for col in required_cols:
                        if col in unnamed_drivers.columns:
                            unnamed_drivers[col] = unnamed_drivers[col].fillna("N/A")
                    
                    # Step 2: Template loading - 40%
                    status_text.write("Step 2/4: Creating document template...")
                    progress_bar.progress(40)
                    
                    # Step 3: Merging data - 60%
                    status_text.write(f"Step 3/4: Merging {len(unnamed_drivers)} records...")
                    progress_bar.progress(60)
                    doc_merged = mailmerge_multiple_records(unnamed_drivers)
                    
                    # Step 4: PDF conversion - 80%
                    status_text.write("Step 4/4: Converting to PDF...")
                    progress_bar.progress(80)
                    
                    # Convert to PDF - most time-consuming step
                    pdf_bytes = convert_mailmerged_doc_to_pdf(doc_merged)
                    
                    # Complete
                    progress_bar.progress(100)
                    status_text.write("✅ PDF generation complete!")
                    
                    # Show download button with timestamp in filename
                    time_stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        label="⬇️ Download PDF (Unnamed Drivers)",  # Added explicit label
                        data=pdf_bytes,
                        file_name=f"warning_letters_unnamed_{time_stamp}.pdf",
                        mime="application/pdf",
                        key="download_unnamed_pdf"  # Added unique key
                    )
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")
                    st.info("Try using 'Check Over-Speeding Drivers' button first to refresh the data.")

    render_glow_line()

# ----------------------------------------------------------------------------
# CALL THE WARNING LETTERS FUNCTION
# ----------------------------------------------------------------------------
if "df" in st.session_state and not st.session_state.df.empty:
    overspeeding_warning_letters(st.session_state.df)
else:
    st.error("No data available. Please load your dataset.")
st.markdown("<h3 style='margin-bottom:20px;'>🔍 " + t("Driver Event Analysis", "驾驶员事件分析") + "</h3>", unsafe_allow_html=True)

# Ensure driver names are sorted and unique
driver_list = sorted(df_filtered["Driver"].astype(str).unique())

# Dropdown to select driver
selected_driver = st.selectbox(t("Select Driver", "选择驾驶员"), driver_list)

# Show event counts in a table instead of a pie chart
if selected_driver:
    driver_data = df_filtered[df_filtered["Driver"] == selected_driver]
    event_counts = driver_data["Event Type"].value_counts().reset_index()
    event_counts.columns = [t("Event Type", "事件类型"), t("Count", "数量")]

    # Display table with event counts
    st.markdown(f"### {t('Event Breakdown for', '事件明细')} {selected_driver}")
    st.dataframe(event_counts, use_container_width=True)

# Optimized version with parallel processing
def parallel_mailmerge_to_pdf(records, template_path="assets/warning_letter.docx", max_workers=8):
    """Enhanced parallel processing with optimized batch handling"""
    if records.empty:
        return None

    # Create improved progress tracking
    col1, col2 = st.columns([2, 1])
    with col1:
        progress_bar = st.progress(0)
        status_text = st.empty()
    with col2:
        stats_text = st.empty()
    
    # Optimize chunk size based on total records
    total_records = len(records)
    chunk_size = min(25, max(5, total_records // (max_workers * 2)))
    chunks = [records[i:i + chunk_size] for i in range(0, total_records, chunk_size)]
    total_chunks = len(chunks)
    
    # Enhanced progress tracking
    progress_data = {
        "completed_chunks": 0,
        "completed_merges": 0,
        "start_time": time.time(),
        "total_pdfs": 0,
        "current_phase": "Initialization"
    }
    progress_lock = threading.Lock()

    def update_progress(phase=None, chunk_complete=False, merge_complete=False):
        with progress_lock:
            if chunk_complete:
                progress_data["completed_chunks"] += 1
            if merge_complete:
                progress_data["completed_merges"] += 1
            if phase:
                progress_data["current_phase"] = phase
            
            # Calculate progress and ETA
            elapsed = time.time() - progress_data["start_time"]
            if progress_data["completed_chunks"] > 0:
                avg_time_per_chunk = elapsed / progress_data["completed_chunks"]
                remaining_chunks = total_chunks - progress_data["completed_chunks"]
                eta = avg_time_per_chunk * remaining_chunks
                
                # Update progress displays
                total_progress = (progress_data["completed_chunks"] / total_chunks) * 100
                progress_bar.progress(int(total_progress))
                
                status_text.write(f"""
                🔄 {progress_data['current_phase']}
                - Chunk: {progress_data['completed_chunks']}/{total_chunks}
                - Records processed: {progress_data['completed_chunks'] * chunk_size}/{total_records}
                """)
                
                stats_text.markdown(f"""
                ⏱️ **Processing Stats:**
                - Elapsed: {elapsed:.1f}s
                - ETA: {eta:.1f}s
                - Speed: {(progress_data['completed_chunks'] * chunk_size / elapsed):.1f} records/s
                """)

    def process_chunk(chunk_data, chunk_id):
        """Process individual chunks with enhanced error handling"""
        try:
            update_progress(phase=f"Processing chunk {chunk_id + 1}/{total_chunks}")
            
            # Create temporary directory for this chunk
            chunk_dir = os.path.join(tempfile.mkdtemp(), f"chunk_{chunk_id}")
            os.makedirs(chunk_dir, exist_ok=True)
            
            # Initialize COM objects
            pythoncom.CoInitialize()
            
            # Process in smaller batches for better memory management
            pdf_paths = []
            sub_batch_size = 5
            
            for i in range(0, len(chunk_data), sub_batch_size):
                sub_batch = chunk_data[i:i + sub_batch_size]
                
                # Create mail merge document
                document = MailMerge(template_path)
                merge_data = []
                
                for _, row in sub_batch.iterrows():
                    try:
                        dt_obj = pd.to_datetime(row.get("Start Time", ""))
                        incident_date = dt_obj.strftime("%Y-%m-%d")
                        incident_time = dt_obj.strftime("%H:%M:%S")
                    except:
                        incident_date = incident_time = "N/A"
                    
                    merge_data.append({
                        "Driver_ID": str(row.get("Driver ID", "N/A")),
                        "Driver": str(row.get("Driver", "Unknown Driver")).strip() or "Unknown Driver",
                        "Group": str(row.get("Group", "Unknown Department")),
                        "Start_Time": incident_time,
                        "Shift_Date": incident_date,
                        "Area": str(row.get("Area", "Unknown Location")),
                        "Overspeeding_Value": str(row.get("Overspeeding Value", 0)),
                        "Speed_Limit": str(row.get("Speed Limit", "N/A")),
                        "Shift": str(row.get("Shift", "N/A")),
                        "Max_SpeedKmh": str(row.get("Max Speed(Km/h)", "N/A")),
                        "License_Plate": str(row.get("License Plate", "N/A"))
                    })
                
                if merge_data:
                    document.merge_pages(merge_data)
                    batch_docx = os.path.join(chunk_dir, f"batch_{i}.docx")
                    batch_pdf = os.path.join(chunk_dir, f"batch_{i}.pdf")
                    
                    document.write(batch_docx)
                    docx2pdf_convert(batch_docx, batch_pdf)
                    
                    os.remove(batch_docx)
                    pdf_paths.append(batch_pdf)
                    
                    with progress_lock:
                        progress_data["total_pdfs"] += 1
            
            update_progress(chunk_complete=True)
            return pdf_paths
            
        except Exception as e:
            st.error(f"Error in chunk {chunk_id}: {str(e)}")
            return []
        finally:
            pythoncom.CoUninitialize()
            
    # Process chunks in parallel with improved error handling
    update_progress(phase="Starting parallel processing...")
    all_pdf_paths = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(process_chunk, chunk, i): i 
            for i, chunk in enumerate(chunks)
        }
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            pdf_paths = future.result()
            all_pdf_paths.extend(pdf_paths)
    
    # Merge PDFs with progress updates
    if all_pdf_paths:
        update_progress(phase="Merging PDF documents...")
        progress_bar.progress(95)
        
        merger = PdfMerger()
        for i, pdf in enumerate(all_pdf_paths):
            merger.append(pdf)
            os.remove(pdf)
            
            # Update merge progress
            merge_progress = (i + 1) / len(all_pdf_paths)
            status_text.write(f"🔄 Merging PDFs: {i + 1}/{len(all_pdf_paths)}")
        
        final_pdf = tempfile.mktemp(suffix='.pdf')
        merger.write(final_pdf)
        merger.close()
        
        with open(final_pdf, 'rb') as f:
            pdf_bytes = f.read()
        
        os.remove(final_pdf)
        
        # Final status update
        progress_bar.progress(100)
        status_text.write("✅ PDF generation complete!")
        stats_text.markdown(f"""
        📊 **Final Stats:**
        - Total time: {(time.time() - progress_data['start_time']):.1f}s
        - Records processed: {total_records}
        - PDFs generated: {progress_data['total_pdfs']}
        """)
        
        return pdf_bytes
    
    return None
# End of file



