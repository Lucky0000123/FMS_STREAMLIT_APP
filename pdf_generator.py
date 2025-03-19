import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from datetime import datetime
import numpy as np
from PIL import Image as PILImage
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import base64
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Try to import leafmap for satellite heatmap
try:
    import leafmap.foliumap as leafmap
    import folium
    HAS_LEAFMAP = True
except ImportError:
    HAS_LEAFMAP = False

# Try to import webdriver_manager for automated Chrome driver installation
try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

def get_safe_colormap(name="viridis", fallback="viridis"):
    """Get a colormap, with fallback if not available"""
    try:
        # First try using seaborn's color palette
        if name == "rocket":
            return sns.color_palette("rocket", as_cmap=True)
        else:
            return plt.cm.get_cmap(name)
    except (AttributeError, ValueError):
        # If that fails, fall back to a standard matplotlib colormap
        return plt.cm.get_cmap(fallback)

def create_dashboard_styled_charts(df):
    """Create charts that match the dashboard styling."""
    charts = []
    
    # 1. Average speeding line chart
    if "Overspeeding Value" in df.columns and "Shift Date" in df.columns:
        avg_speeding = df.groupby('Shift Date')['Overspeeding Value'].mean().reset_index()
        
        if len(avg_speeding) >= 2:
            plt.figure(figsize=(10, 5))
            plt.style.use('ggplot')
            
            # Calculate trend line
            x_numeric = np.arange(len(avg_speeding))
            y_values = avg_speeding['Overspeeding Value']
            trend_coeffs = np.polyfit(x_numeric, y_values, 1)
            trend_line = np.polyval(trend_coeffs, x_numeric)
            
            # Plot average speeding value line
            plt.plot(avg_speeding['Shift Date'], avg_speeding['Overspeeding Value'], 
                   marker='o', markersize=8, linewidth=3, color='#1f77b4', 
                   label="Average Speeding Value")
            
            # Plot trend line
            plt.plot(avg_speeding['Shift Date'], trend_line, 
                   linestyle='--', linewidth=2, color='#ff7f0e', 
                   label="Trend Line")
            
            plt.title("Average Speeding Values Over Time", fontsize=16, fontweight='bold')
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Average Speeding Value (Km/h)", fontsize=12)
            plt.tight_layout()
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            charts.append({"name": "Average Speeding Values", "image": img_buffer})
            plt.close()
    
    # 2. Event Distribution Chart
    if "Event Type" in df.columns:
        plt.figure(figsize=(10, 6))
        plt.style.use('ggplot')
        
        event_counts = df['Event Type'].value_counts()
        colors = plt.cm.viridis(np.linspace(0, 1, len(event_counts)))
        
        bars = plt.barh(event_counts.index, event_counts.values, color=colors)
        
        # Add value labels to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{width:.0f}', 
                    ha='left', va='center', fontweight='bold')
        
        plt.title('Event Distribution by Type', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Events', fontsize=12)
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        charts.append({"name": "Event Distribution", "image": img_buffer})
        plt.close()

        # Map Visualization Screenshot
        try:
            # Capture map visualization from dashboard
            map_screenshot = capture_element_screenshot('map_visualization')
            if map_screenshot:
                img_buffer = io.BytesIO(map_screenshot)
                charts.append({
                    "name": "Geospatial Analysis", 
                    "image": img_buffer,
                    "description": "Heatmap showing event density across locations"
                })
        except Exception as e:
            print(f"Error capturing map screenshot: {e}")
            # Fallback to existing heatmap
            charts.append(create_fallback_heatmap(df))
    
    # 4. Top 10 Drivers Chart
    if 'Driver' in df.columns and len(df) > 0:
        plt.figure(figsize=(10, 6))
        plt.style.use('ggplot')
        
        driver_events = df.groupby('Driver')['Event Type'].count().sort_values(ascending=False).head(10)
        colors = get_safe_colormap("rocket", "viridis")(np.linspace(0, 0.8, len(driver_events)))
        
        bars = plt.barh(driver_events.index, driver_events.values, color=colors)
        
        # Add value labels to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{width:.0f}', 
                    ha='left', va='center', fontweight='bold')
        
        plt.title('Top 10 Drivers by Number of Events', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Events', fontsize=12)
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        charts.append({"name": "Top 10 Drivers", "image": img_buffer})
        plt.close()
    
    # 5. Speeding Events Analysis
    if "Event Type" in df.columns:
        plt.figure(figsize=(10, 5))
        plt.style.use('ggplot')
        
        speeding_df = df[df['Event Type'] == 'Speeding']
        if 'Speed' in speeding_df.columns and len(speeding_df) > 0:
            sns.histplot(data=speeding_df, x='Speed', bins=20, color='red', kde=True)
            plt.title('Distribution of Speeding Events', fontsize=16, fontweight='bold')
            plt.xlabel('Speed (km/h)', fontsize=12)
            plt.ylabel('Number of Events', fontsize=12)
        else:
            plt.text(0.5, 0.5, "No speeding data available", 
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        charts.append({"name": "Speeding Distribution", "image": img_buffer})
        plt.close()
    
    return charts

def capture_all_dashboard_elements():
    """Capture all visible dashboard elements using JavaScript."""
    try:
        # Inject JavaScript to capture all chart elements
        js_code = """
        async function captureAllElements() {
            const elements = document.querySelectorAll('.stplot, .element-container:has(canvas), .element-container:has(.user-chart)');
            const results = [];
            
            for (let i = 0; i < elements.length; i++) {
                try {
                    const element = elements[i];
                    const rect = element.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 50) {  // Only capture visible elements
                        const canvas = await html2canvas(element, {
                            logging: false,
                            scale: 2,
                            useCORS: true
                        });
                        results.push(canvas.toDataURL('image/png'));
                    }
                } catch (e) {
                    console.error('Failed to capture element:', e);
                }
            }
            return results;
        }
        
        return await captureAllElements();
        """
        
        # Run JavaScript and get results
        chart_images = st.session_state.get('_streamlit_app_js_eval', {}).get('eval', lambda x: [])(js_code)
        
        # Convert base64 images to bytes
        image_bytes = []
        for img_data in chart_images:
            if img_data.startswith('data:image/png;base64,'):
                img_bytes = base64.b64decode(img_data.split(',')[1])
                image_bytes.append(img_bytes)
        
        return image_bytes
    except Exception as e:
        print(f"Error capturing dashboard elements: {str(e)}")
        return []

def capture_full_dashboard():
    """Capture the full dashboard using Selenium (if available)."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Try to get the current URL from session state or use default
        current_url = st.session_state.get('current_url', 'http://localhost:8502')
        
        print(f"Attempting to capture dashboard at URL: {current_url}")
        
        # Set up the WebDriver with improved error handling
        if HAS_WEBDRIVER_MANAGER:
            # Use webdriver_manager for automatic chromedriver installation
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Try using system Chrome directly
            driver = webdriver.Chrome(options=chrome_options)
            
        # Navigate to the dashboard
        driver.get(current_url)
        
        # Wait for dashboard to load
        print("Waiting for dashboard to load...")
        time.sleep(10)  # Increased wait time for better loading
        
        # Scroll through the page to ensure all elements are rendered
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            height = driver.execute_script("return document.body.scrollHeight")
            for i in range(0, height, 300):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            print("Scrolled through page to load all elements")
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
        
        try:
            # Try to find KPI cards first - they're a good indicator the page is loaded
            kpi_elements = driver.find_elements(By.CLASS_NAME, "kpi-card")
            if kpi_elements:
                print(f"KPI cards found - {len(kpi_elements)} cards detected")
            
            # Also look for other indicators that content is loaded
            metrics = driver.find_elements(By.CSS_SELECTOR, ".stMetric, .css-1xarl3l")
            if metrics:
                print(f"Metrics found - {len(metrics)} metrics detected")
        except Exception as e:
            print(f"Warning - could not check for KPI cards: {str(e)}")
        
        # Capture full page screenshot
        screenshot = driver.get_screenshot_as_png()
        print("Captured full page screenshot")
        
        # Try to capture individual KPI elements
        kpi_screenshots = []
        try:
            # Look for KPI containers with various selectors
            kpi_selectors = [
                ".kpi-card", 
                ".stMetric", 
                ".css-1xarl3l", 
                ".element-container:has(.css-50eq8u)",
                ".element-container:has(.css-1wivap2)"
            ]
            
            for selector in kpi_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector {selector}")
                    for element in elements:
                        try:
                            kpi_screenshots.append(element.screenshot_as_png())
                        except Exception as e:
                            print(f"Error capturing element with selector {selector}: {str(e)}")
        except Exception as e:
            print(f"Error capturing KPI elements: {str(e)}")
        
        # Try to capture individual chart elements if possible
        chart_screenshots = []
        try:
            # Look for chart containers with various selectors
            chart_selectors = [
                ".element-container:has(canvas)",
                ".element-container:has(.js-plotly-plot)",
                ".element-container:has(.stplot)",
                ".element-container:has(.plot-container)",
                ".element-container:has(.user-chart)",
                ".element-container:has(.echarts-for-react)",
                ".stVegaLiteChart"
            ]
            
            for selector in chart_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} chart elements with selector {selector}")
                    for element in elements:
                        try:
                            element_image = element.screenshot_as_png()
                            if element_image:
                                chart_screenshots.append(element_image)
                        except Exception as e:
                            print(f"Error capturing chart with selector {selector}: {str(e)}")
        except Exception as e:
            print(f"Error capturing chart elements: {str(e)}")
        
        driver.quit()
        
        # Return the captures we found
        result = {
            "kpi_images": kpi_screenshots if kpi_screenshots else [],
            "chart_images": chart_screenshots if chart_screenshots else [screenshot]
        }
        
        print(f"Captured {len(result['kpi_images'])} KPI images and {len(result['chart_images'])} chart images")
        return result
    except Exception as e:
        print(f"Error capturing full dashboard: {str(e)}")
        return {"kpi_images": [], "chart_images": []}

def capture_kpi_row(driver):
    """Capture just the KPI row from the dashboard."""
    try:
        # Find the KPI row element using modern Selenium API
        kpi_elements = driver.find_elements(By.CLASS_NAME, 'kpi-card')
        if not kpi_elements:
            return None
        
        # Get the parent element containing all KPIs
        parent = kpi_elements[0].find_element(By.XPATH, './..')
        while parent and (parent.get_attribute('class') is None or 'row' not in parent.get_attribute('class')):
            parent = parent.find_element(By.XPATH, './..')
        
        if parent:
            return parent.screenshot_as_png()
        return None
    except Exception as e:
        print(f"Error capturing KPI row: {str(e)}")
        return None

def create_kpi_values(df):
    """Create KPI values directly from dataframe data."""
    kpi_data = []
    
    # Total events
    total_events = len(df)
    kpi_data.append({"title": "Total Events", "value": f"{total_events:,}", "unit": "events", "color": "#1D5B79"})
    
    # Speeding events
    if "Event Type" in df.columns:
        speeding_events = len(df[df["Event Type"] == "Speeding"])
        speeding_pct = (speeding_events / total_events * 100) if total_events > 0 else 0
        kpi_data.append({"title": "Speeding Events", "value": f"{speeding_events:,}", 
                         "unit": f"({speeding_pct:.1f}%)", "color": "#FF6B6B"})
    
    # Average speed
    if "Speed" in df.columns:
        avg_speed = df["Speed"].mean() if len(df) > 0 else 0
        kpi_data.append({"title": "Average Speed", "value": f"{avg_speed:.1f}", "unit": "km/h", "color": "#2E8B57"})
    
    # Unique drivers
    if "Driver" in df.columns:
        unique_drivers = df["Driver"].nunique()
        kpi_data.append({"title": "Unique Drivers", "value": f"{unique_drivers:,}", "unit": "drivers", "color": "#4A90E2"})
    
    # High risk events
    if "Risk Level" in df.columns:
        high_risk = len(df[df["Risk Level"] == "High"])
        high_risk_pct = (high_risk / total_events * 100) if total_events > 0 else 0
        kpi_data.append({"title": "High Risk Events", "value": f"{high_risk:,}", 
                        "unit": f"({high_risk_pct:.1f}%)", "color": "#E74C3C"})
    
    # Date range - updated to be more prominent
    if "Date" in df.columns or "Shift Date" in df.columns:
        date_col = "Date" if "Date" in df.columns else "Shift Date"
        if len(df) > 0:
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            if pd.notna(min_date) and pd.notna(max_date):
                min_date_str = pd.to_datetime(min_date).strftime('%b %d, %Y')
                max_date_str = pd.to_datetime(max_date).strftime('%b %d, %Y')
                # Split date range into two lines for better visibility
                date_range = f"{min_date_str}\nto\n{max_date_str}"
                kpi_data.append({
                    "title": "Date Range", 
                    "value": date_range, 
                    "unit": "", 
                    "color": "#8E44AD",
                    "font_size": 18,
                    "line_spacing": 18  # Changed from 1.2 to fixed value
                })
    
    return kpi_data

def create_dashboard_report(df, kpi_images, chart_images, filters=None):
    """Generate a PDF report with title, logo, KPIs and charts."""
    
    if not os.path.exists('reports'):
        os.makedirs('reports')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/safety_report_{timestamp}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Create custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=36,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1D5B79'),
        alignment=1,  # Center alignment
        spaceAfter=30,
        leading=40
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        fontName='Helvetica',
        textColor=colors.HexColor('#2E8B57'),
        alignment=1,
        spaceAfter=20
    )
    
    # First page header with larger logo and styled title
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        img = PILImage.open(logo_path)
        aspect_ratio = img.width / img.height
        desired_width = 2.5 * inch  # Increased width
        logo_height = desired_width / aspect_ratio
        header_table_data = [[
            Image(logo_path, width=desired_width, height=logo_height),
            Paragraph(
                "Fleet Safety Dashboard Report",
                title_style
            ),
            ""  # Empty cell for balance
        ]]
        
        header_table = Table(header_table_data, colWidths=[2.7*inch, 6*inch, 2.7*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_table)
    
    # Add timestamp
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        subtitle_style
    ))
    story.append(Spacer(1, 20))
    
    # Add filter information if provided
    if filters:
        filter_text = []
        for key, value in filters.items():
            if value and value != "All":
                filter_text.append(f"{key}: {value}")
        
        if filter_text:
            filter_para = Paragraph(
                "Filters Applied: " + " | ".join(filter_text),
                ParagraphStyle(
                    'FilterStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=colors.HexColor('#666666'),
                    alignment=1
                )
            )
            story.append(filter_para)
            story.append(Spacer(1, 20))
    
    # Add KPI section with styled title
    story.append(Paragraph(
        "Key Performance Indicators",
        ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2E8B57'),
            alignment=1,
            spaceAfter=20
        )
    ))
    
    # Add KPIs - first try with images, then fall back to generated text KPIs
    if kpi_images:
        try:
            # Create rows of 3 KPIs each
            kpi_rows = []
            current_row = []
            for i, kpi_image in enumerate(kpi_images[:6]):  # Limit to 6 KPIs per page
                try:
                    img_byte_arr = io.BytesIO()
                    PILImage.open(io.BytesIO(kpi_image)).save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    current_row.append(Image(img_byte_arr, width=3*inch, height=2*inch))
                except Exception as e:
                    print(f"Error processing KPI image, skipping: {e}")
                    continue
                if len(current_row) == 3 or i == len(kpi_images) - 1:
                    while len(current_row) < 3:
                        current_row.append("")
                    kpi_rows.append(current_row)
                    current_row = []
            if kpi_rows:
                kpi_table = Table(kpi_rows, colWidths=[3*inch, 3*inch, 3*inch])
                kpi_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(kpi_table)
            else:
                # No valid KPI images, fall back to text KPIs
                kpi_images = []
        except Exception as e:
            print(f"Error creating KPI table from images: {e}")
            # Fall back to generated KPIs
            kpi_images = []
    
    # If no KPI images, generate text-based KPIs
    if not kpi_images:
        try:
            # Generate KPI values from data
            kpi_data = create_kpi_values(df)
            
            # Create KPI cards
            kpi_rows = []
            current_row = []
            
            # Create title and value styles
            kpi_title_style = ParagraphStyle(
                'KPITitle',
                parent=styles['Normal'],
                fontSize=12,
                alignment=1,
                textColor=colors.HexColor('#555555')
            )
            
            # Divide KPIs into rows of 3
            for i, kpi in enumerate(kpi_data):
                # Create KPI card with custom font size for date range
                kpi_value_style = ParagraphStyle(
                    f'KPIValue_{i}',
                    parent=styles['Heading3'],
                    fontSize=kpi.get('font_size', 22),
                    alignment=1,
                    textColor=colors.HexColor(kpi["color"]),
                    fontName='Helvetica-Bold',
                    leading=kpi.get('line_spacing', 18)  # Ensure default value
                )
                
                kpi_unit_style = ParagraphStyle(
                    f'KPIUnit_{i}',
                    parent=styles['Normal'],
                    fontSize=10,
                    alignment=1,
                    textColor=colors.HexColor('#777777')
                )
                
                # Build KPI card content
                kpi_card_content = [
                    [Paragraph(kpi["title"], kpi_title_style)],
                    [Paragraph(kpi["value"], kpi_value_style)],
                    [Paragraph(kpi["unit"], kpi_unit_style)]
                ]
                
                # Create KPI card table with border
                kpi_card = Table(kpi_card_content, colWidths=[2.8*inch])
                kpi_card.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F9F9')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                current_row.append(kpi_card)
                
                if len(current_row) == 3 or i == len(kpi_data) - 1:
                    while len(current_row) < 3:
                        current_row.append("")
                    kpi_rows.append(current_row)
                    current_row = []
            
            if kpi_rows:
                # Create the final KPI grid
                kpi_grid = Table(kpi_rows, colWidths=[3*inch, 3*inch, 3*inch])
                kpi_grid.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(kpi_grid)
        except Exception as e:
            print(f"Error creating text-based KPI cards: {e}")
    
    # Add a page break before charts
    story.append(PageBreak())
    
    # Generate the dashboard-styled charts
    dashboard_charts = create_dashboard_styled_charts(df)
    
    # First add any captured chart images from the dashboard
    if chart_images:
        story.append(Paragraph(
            "Dashboard Analytics",
            ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=24,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#2E8B57'),
                alignment=1,
                spaceAfter=10  # Reduced spacing
            )
        ))
        
        for chart_image in chart_images:
            try:
                img_byte_arr = io.BytesIO()
                PILImage.open(io.BytesIO(chart_image)).save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                img = Image(img_byte_arr, width=8*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 10))  # Reduced spacing
            except Exception as e:
                print(f"Error processing chart image, skipping: {e}")
    
    # Then add our custom dashboard-styled charts
    if dashboard_charts:
        story.append(Paragraph(
            "Analytics & Insights",
            ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=24,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#2E8B57'),
                alignment=1,
                spaceAfter=10
            )
        ))
        
        # Add charts in 2-column layout with descriptions
        for chart in dashboard_charts:
            # Create main content table with 2 columns (70/30 split)
            chart_table = Table([
                [
                    # Left column: Chart image (larger size)
                    Image(chart["image"], width=6.5*inch, height=5*inch),
                    # Right column: Description
                    Table([
                        [Paragraph("Key Insights:", styles['Heading3'])],
                        [Paragraph("- Trend analysis over time", styles['Normal'])],
                        [Paragraph("- Peak event hours", styles['Normal'])],
                        [Paragraph("- High-risk locations", styles['Normal'])],
                        [Spacer(1, 0.2*inch)],
                        [Paragraph("Data Summary:", styles['Heading3'])],
                        [Paragraph(f"Records: {len(df):,}", styles['Normal'])],
                        [Paragraph(f"Time Range: {df['Date'].min()} to {df['Date'].max()}", styles['Normal'])]
                    ], colWidths=[2.5*inch])
                ]
            ], colWidths=[6.5*inch, 2.5*inch])
            
            chart_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(chart_table)
            story.append(Spacer(1, 0.5*inch))
    
    # Build PDF
    try:
        doc.build(story)
    except Exception as pdf_e:
        print(f"Error building PDF: {pdf_e}")
        raise
    return filename

def capture_element_screenshot(element_id):
    """Capture specific dashboard element by ID"""
    try:
        # Get current Streamlit URL from runtime config
        port = st.runtime.get_instance().config.server.port
        address = st.runtime.get_instance().config.server.address
        current_url = f"http://{address}:{port}"
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # New headless mode
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        # Use browserless/chrome for more reliable captures
        if HAS_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            
        driver.get(current_url)
        
        # Wait for map container with aggressive retries
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"#{element_id}"))
            )
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f"#{element_id}"))
            )
        except Exception as e:
            print(f"Element not found: {element_id}, trying alternative selectors")
            # Fallback to common map container classes
            map_element = driver.find_element(By.CSS_SELECTOR, ".stDeckGlJsonChart, .element-container")
        
        # Force full render
        driver.execute_script("document.body.style.zoom = '80%'")
        time.sleep(1)
        driver.execute_script("window.dispatchEvent(new Event('resize'))")
        time.sleep(2)
        
        screenshot = map_element.screenshot_as_png
        driver.quit()
        return screenshot
        
    except Exception as e:
        print(f"Error capturing {element_id}: {str(e)}")
        return None

def capture_matching_elements(pattern):
    """Capture all elements matching a pattern in their key."""
    screenshots = []
    for key in st.session_state:
        if pattern in str(key).lower():
            try:
                if hasattr(st.session_state[key], '_native') and hasattr(st.session_state[key]._native, 'screenshot'):
                    img = st.session_state[key]._native.screenshot()
                    if img:
                        screenshots.append(img)
            except Exception as e:
                print(f"Error capturing {key}: {str(e)}")
    return screenshots

def find_streamlit_elements():
    """Find all potential streamlit elements that could be charts or KPIs."""
    element_keys = []
    for key in st.session_state:
        try:
            if hasattr(st.session_state[key], '_native') and hasattr(st.session_state[key]._native, 'screenshot'):
                element_keys.append(key)
        except:
            pass
    return element_keys

def generate_dashboard_report(df, filters=None):
    """Generate report with actual dashboard content."""
    try:
        # Try to ensure required packages are available
        try:
            import pkg_resources
            required_packages = ['selenium', 'matplotlib', 'seaborn', 'plotly', 'pillow', 'reportlab']
            for package in required_packages:
                try:
                    pkg_resources.require(package)
                except pkg_resources.DistributionNotFound:
                    print(f"Warning: {package} not found. Charts may not render correctly.")
        except Exception as e:
            print(f"Could not check package requirements: {str(e)}")
            
        # Create reports directory if it doesn't exist
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        # Try multiple capture methods
        
        # 1. First try Streamlit-native element capture
        print("STEP 1: Trying Streamlit-native element capture...")
        all_elements = find_streamlit_elements()
        print(f"Found {len(all_elements)} potential chart elements")
        
        # Collect KPI screenshots - try to capture all KPI cards in one go
        kpi_images = capture_matching_elements('kpi')
        
        # Look for KPI matches if none found directly
        if not kpi_images:
            # Try other common KPI indicators
            kpi_candidates = ['metric', 'stat', 'card', 'summary', 'indicator']
            for candidate in kpi_candidates:
                candidate_images = capture_matching_elements(candidate)
                if candidate_images:
                    kpi_images.extend(candidate_images)
                    print(f"Found {len(candidate_images)} KPIs with pattern '{candidate}'")
        
        # Collect chart screenshots
        chart_patterns = ['chart', 'plot', 'graph', 'fig', 'map', 'viz']
        chart_images = []
        
        for pattern in chart_patterns:
            pattern_matches = capture_matching_elements(pattern)
            chart_images.extend(pattern_matches)
            print(f"Found {len(pattern_matches)} {pattern} elements")
        
        # Try to capture all remaining elements as potential charts if we found few
        if len(chart_images) < 3:
            for key in all_elements:
                if all(pattern not in str(key).lower() for pattern in chart_patterns + ['kpi', 'metric', 'stat']):
                    img = capture_element_screenshot(key)
                    if img:
                        chart_images.append(img)
        
        print(f"STEP 1 RESULTS: Found {len(kpi_images)} KPI images and {len(chart_images)} chart images")
        
        # 2. If the first method didn't yield enough results, try Selenium capture
        if len(chart_images) < 2 or len(kpi_images) < 2:
            print("STEP 2: Trying Selenium-based capture...")
            try:
                selenium_capture = capture_full_dashboard()
                
                # Add any KPI images we found
                if selenium_capture["kpi_images"]:
                    print(f"Adding {len(selenium_capture['kpi_images'])} KPI images from Selenium")
                    kpi_images.extend(selenium_capture["kpi_images"])
                
                # Add any chart images we found
                if selenium_capture["chart_images"] and len(selenium_capture["chart_images"]) > 0:
                    print(f"Adding {len(selenium_capture['chart_images'])} chart images from Selenium")
                    chart_images.extend(selenium_capture["chart_images"])
            except Exception as e:
                print(f"Selenium capture failed: {str(e)}")
        
        print(f"FINAL CAPTURE RESULTS: {len(kpi_images)} KPI images and {len(chart_images)} chart images")
        
        # Always create charts from data as a backup
        print("Generating data-based charts as backup...")
        generated_charts = create_dashboard_styled_charts(df)
        print(f"Generated {len(generated_charts)} charts from data")
        
        # Alert user if we're using fallback charts
        if not kpi_images or not chart_images:
            print("Using fallback data-generated charts")
            st.warning("Some dashboard elements couldn't be captured. The report will include data-generated charts.")
        
        # Create the final report with both captured and generated data
        print("Creating final report...")
        filename = create_dashboard_report(df, kpi_images, chart_images, filters)
        
        print(f"Report saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try a final fallback approach - just generate charts from data
        try:
            print("Attempting fallback report generation with data-only charts")
            if not os.path.exists('reports'):
                os.makedirs('reports')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/safety_report_{timestamp}_fallback.pdf"
            
            generated_charts = create_dashboard_styled_charts(df)
            if generated_charts:
                doc = SimpleDocTemplate(
                    filename,
                    pagesize=landscape(letter),
                    rightMargin=30,
                    leftMargin=30,
                    topMargin=30,
                    bottomMargin=30
                )
                
                story = []
                styles = getSampleStyleSheet()
                
                # Create a nicer header even in fallback mode
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=36,
                    fontName='Helvetica-Bold',
                    textColor=colors.HexColor('#1D5B79'),
                    alignment=1,
                    spaceAfter=30,
                    leading=40
                )
                
                logo_path = "assets/logo.png"
                if os.path.exists(logo_path):
                    img = PILImage.open(logo_path)
                    aspect_ratio = img.width / img.height
                    desired_width = 2.5 * inch  # Increased width
                    logo_height = desired_width / aspect_ratio
                    header_table_data = [[
                        Image(logo_path, width=desired_width, height=logo_height),
                        Paragraph("Fleet Safety Dashboard Report", title_style),
                        ""  # Empty cell for balance
                    ]]
                    
                    header_table = Table(header_table_data, colWidths=[2.7*inch, 6*inch, 2.7*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(header_table)
                else:
                    story.append(Paragraph("Fleet Safety Dashboard Report", title_style))
                
                story.append(Spacer(1, 20))
                
                # Add timestamp
                subtitle_style = ParagraphStyle(
                    'CustomSubtitle',
                    parent=styles['Heading2'],
                    fontSize=18,
                    fontName='Helvetica',
                    textColor=colors.HexColor('#2E8B57'),
                    alignment=1,
                    spaceAfter=20
                )
                
                story.append(Paragraph(
                    f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                    subtitle_style
                ))
                story.append(Spacer(1, 20))
                story.append(PageBreak())
                
                # Add charts in the preferred order
                chart_order = ["Average Speeding Values", "Event Distribution", "Event Location Heatmap", "Top 10 Drivers", "Speeding Distribution"]
                for chart_name in chart_order:
                    for chart in generated_charts:
                        if chart["name"] == chart_name:
                            img = Image(chart["image"], width=8*inch, height=4*inch)
                            story.append(Paragraph(
                                chart_name,
                                ParagraphStyle(
                                    'ChartTitle',
                                    parent=styles['Heading3'],
                                    fontSize=18,
                                    fontName='Helvetica-Bold',
                                    textColor=colors.HexColor('#2E8B57'),
                                    alignment=1,
                                    spaceAfter=10
                                )
                            ))
                            story.append(img)
                            story.append(Spacer(1, 20))
                
                doc.build(story)
                print(f"Successfully created fallback report: {filename}")
                return filename
        except Exception as fallback_error:
            print(f"Even fallback approach failed: {str(fallback_error)}")
        
        return None

def generate_report(df, selected_dates=None, selected_plate=None):
    """Wrapper function to generate the report."""
    try:
        filters = {}
        if selected_dates:
            filters['Date Range'] = f"{selected_dates[0]} to {selected_dates[1]}"
        if selected_plate and selected_plate != "All":
            filters['License Plate'] = selected_plate
            
        return generate_dashboard_report(df, filters)
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None

def create_fallback_heatmap(df):
    """Create a fallback heatmap using matplotlib in case capturing the dashboard map fails."""
    import matplotlib.pyplot as plt
    import io
    
    # Determine latitude and longitude columns
    lat_col = "Start Lat" if "Start Lat" in df.columns else None
    lon_col = "Start Lng" if "Start Lng" in df.columns else None
    if lat_col is None or lon_col is None:
        return {"name": "Fallback Heatmap", "image": None}
    
    # Filter data for speeding events with valid coordinates
    heat_df = df[df['Event Type'] == 'Speeding'].dropna(subset=[lat_col, lon_col])
    if heat_df.empty:
        return {"name": "Fallback Heatmap", "image": None}
    
    plt.figure(figsize=(8,6))
    plt.hist2d(heat_df[lat_col], heat_df[lon_col], bins=50, cmap='hot')
    plt.colorbar()
    plt.title("Fallback Heatmap")
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return {"name": "Fallback Heatmap", "image": buf} 