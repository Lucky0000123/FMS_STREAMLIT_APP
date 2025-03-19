import streamlit as st
from reportlab.pdfgen import canvas
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from datetime import datetime

# Load data directly from Excel file instead of using utils
def get_data():
    file_path = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame()

# Get the data
df = get_data()

# Function to create overspeeding chart
def generate_overspeeding_chart():
    if df.empty:
        # Create empty figure if data is not available
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14)
        ax.set_title('Top 10 Vehicles by Overspeeding Count')
        plt.tight_layout()
        return fig
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Check if 'Vehicle_No' and 'OverSpeeding_Count' columns exist
    if 'Vehicle_No' not in df.columns or 'OverSpeeding_Count' not in df.columns:
        # If columns don't exist, try to find similar columns
        vehicle_col = next((col for col in df.columns if 'vehicle' in col.lower() or 'equip' in col.lower()), None)
        speed_col = next((col for col in df.columns if 'speed' in col.lower()), None)
        
        if not vehicle_col or not speed_col:
            ax.text(0.5, 0.5, "Required columns not found in data", ha='center', va='center')
            plt.tight_layout()
            return fig
        
        # Use the found columns
        overspeeding_data = df.groupby(vehicle_col)[speed_col].sum().sort_values(ascending=False)
    else:
        # Use original column names
        overspeeding_data = df.groupby('Vehicle_No')['OverSpeeding_Count'].sum().sort_values(ascending=False)
    
    # Get top 10 vehicles
    top_overspeeding = overspeeding_data.head(10)
    
    # Create bar chart
    bars = ax.bar(top_overspeeding.index, top_overspeeding.values, color='crimson')
    
    # Add data labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    # Set title and labels
    ax.set_title('Top 10 Vehicles by Overspeeding Count')
    ax.set_xlabel('Vehicle Number')
    ax.set_ylabel('Overspeeding Count')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig

# Function to generate speeding events by day chart
def generate_speeding_events_chart(trend_days=30, shift_type="All"):
    if df.empty:
        return None
    
    # Setup translations dictionary (simplified version)
    translations = {
        "en": {
            "speeding_events_by_day": "Speeding Events by Day",
            "speeding_events_title": "Speeding Events Trend",
            "date": "Date",
            "risk_level": "Risk Level",
            "number_of_events": "Number of Events",
            "no_data_warning": "No data available for the selected filters"
        }
    }
    lang = "en"  # Default language
    
    # Process data for the chart
    try:
        df['Shift Date'] = pd.to_datetime(df['Shift Date'], errors='coerce')
        trend_end = pd.to_datetime('today')
        trend_start = trend_end - pd.DateOffset(days=trend_days)
        trend_df = df[(df['Shift Date'] >= trend_start) & 
                      (df['Shift Date'] <= trend_end) & 
                      (df['Event Type'] == 'Speeding')]
        
        if shift_type != "All":
            trend_df = trend_df[trend_df['Shift'] == shift_type]
        
        if not trend_df.empty:
            trend_data = trend_df.groupby(
                [pd.Grouper(key='Shift Date', freq='D'), 'Risk Level']
            ).size().unstack(fill_value=0).reset_index()
            
            for risk in ["Extreme", "High", "Medium"]:
                if risk not in trend_data.columns:
                    trend_data[risk] = 0
            
            trend_data["Total Events"] = trend_data[["Extreme", "High", "Medium"]].sum(axis=1)
            risk_colors = {'Extreme': '#FF0000', 'High': '#FFA500', 'Medium': '#FFFF00', 'N/A': '#808080'}
            
            fig = px.line(
                trend_data,
                x="Shift Date",
                y=trend_data.columns[1:-1],
                labels={'value': 'Number of Events'},
                color_discrete_map=risk_colors,
                line_shape="linear",
                template="plotly_white"
            )
            
            for i, trace in enumerate(fig.data):
                trace.update(fill='tozeroy' if i == 0 else 'tonexty', opacity=0.1,
                             line=dict(width=3),
                             mode='lines+markers', marker=dict(size=8, line=dict(width=1, color='black')))
            
            fig.update_traces(
                hovertemplate="<b>📅 " + translations[lang]["date"] + ": %{x}</b><br>🔥 " + 
                              translations[lang]["risk_level"] + ": %{fullData.name}<br>📊 " + 
                              translations[lang]["number_of_events"] + ": %{y}",
                hoverlabel=dict(bgcolor="white", font_size=13, font_color="black", font_family="Arial Black")
            )
            
            for i, date in enumerate(trend_data["Shift Date"]):
                fig.add_annotation(
                    x=date,
                    y=-5,
                    text=f" {trend_data['Total Events'][i]}",
                    showarrow=False,
                    font=dict(size=12, color="black"),
                    xshift=0,
                    yshift=-20
                )
            
            fig.update_layout(
                height=400,
                template="plotly_white",
                title_text=translations[lang]["speeding_events_title"],
                title_x=0.5,
                title_font=dict(size=24, family="Arial Black", color="#2a3f5f"),
                xaxis_title=translations[lang]["date"],
                yaxis_title=translations[lang]["number_of_events"],
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickformat="%b %d, %Y", showgrid=True,
                           gridcolor='rgba(200, 200, 200, 0.5)', linecolor='black', linewidth=2),
                yaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)',
                           linecolor='black', linewidth=2),
                legend=dict(title=translations[lang]["risk_level"], orientation="h", yanchor="bottom", y=-0.3,
                            font=dict(size=14, color="black")),
                margin=dict(l=20, r=20, t=60, b=80)
            )
            
            return fig
        
        return None
    except Exception as e:
        st.error(f"Error generating speeding events chart: {str(e)}")
        return None

# Function to create a PDF file with both charts
def create_pdf():
    # Get the overspeeding chart
    overspeeding_fig = generate_overspeeding_chart()
    
    # Get the speeding events chart
    speeding_events_fig = generate_speeding_events_chart()
    
    # Create PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter)
        elements = []
        
        # Save overspeeding chart as image and add to PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img1:
            overspeeding_fig.savefig(temp_img1.name, format="png")
            elements.append(Image(temp_img1.name, width=450, height=300))
        
        # If speeding events chart exists, save as image and add to PDF
        if speeding_events_fig:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img2:
                speeding_events_fig.write_image(temp_img2.name)
                elements.append(Image(temp_img2.name, width=450, height=300))
        
        # Build PDF
        doc.build(elements)
        return temp_pdf.name

# Streamlit UI
st.title("FMS Safety Dashboard")

# Show overspeeding chart
st.header("Top 10 Vehicles by Overspeeding Count")
st.pyplot(generate_overspeeding_chart())

# Show speeding events by day
st.header("Speeding Events by Day")
# Add filter options
trend_days = st.sidebar.slider("Number of days to show", min_value=7, max_value=90, value=30)
shift_options = ["All", "Day", "Night"]
shift_type = st.sidebar.selectbox("Shift Type", shift_options)

# Display speeding events chart
speeding_events_fig = generate_speeding_events_chart(trend_days, shift_type)
if speeding_events_fig:
    st.plotly_chart(speeding_events_fig, use_container_width=True, key="main_speeding_trend")
else:
    st.warning("No data available for the selected filters")

# Button to download the PDF
if st.button("Download PDF Report"):
    pdf_file = create_pdf()
    with open(pdf_file, "rb") as f:
        st.download_button("Click to Download", f, file_name="safety_report.pdf", mime="application/pdf")