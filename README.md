# FMS Safety Dashboard

A comprehensive Fleet Management System (FMS) Safety Dashboard application built with Streamlit to provide safety analytics and driver performance monitoring.

## Features

- **Multi-source Data Loading**: Connects to SQL Server, uploaded Excel files, network shares, or sample data
- **Driver Performance Analysis**: Monitor driver behavior and identify high-risk drivers
- **Safety Analytics**: Visualize safety events, speeding incidents, and risk levels
- **PDF Report Generation**: Generate comprehensive reports for individual drivers or the entire fleet
- **Multilingual Support**: English and Chinese language support
- **Flexible Filtering**: Filter data by date range, vehicle group, driver, and more
- **Database Diagnostics**: Troubleshoot database connection issues with built-in diagnostic tools

## Getting Started

### Prerequisites

- Python 3.8 or higher
- ODBC Driver for SQL Server (if using SQL Server)
- Internet connection for loading some assets

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fms-safety-dashboard.git
cd fms-safety-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database connection (optional):
   - Create a `.streamlit/secrets.toml` file with the following content:
   ```toml
   [sql]
   host = "YOUR_SQL_SERVER"
   port = 1433
   database = "FMS_DB"
   username = "your_username"
   password = "your_password"
   driver = "ODBC Driver 17 for SQL Server"
   ```
   - Or use Windows Authentication:
   ```toml
   [sql]
   host = "YOUR_SQL_SERVER"
   database = "FMS_DB"
   driver = "ODBC Driver 17 for SQL Server"
   trusted_connection = "yes"
   ```

### Running the Application

```bash
streamlit run 1_🏭_Homepage.py
```

## Data Source Configuration

The dashboard can use data from multiple sources:

1. **SQL Server Database**: Configure connection details in `.streamlit/secrets.toml`
2. **Uploaded Excel File**: Upload an Excel file through the user interface
3. **Network Share**: Configure the network path in `utils.py`
4. **Sample Data**: Included sample data for demonstration purposes

## Application Structure

- `1_🏭_Homepage.py`: Main dashboard with KPIs and visualizations
- `pages/2_🌏_Geo_Analysis.py`: Geospatial analysis of safety events
- `pages/3_👨‍💼_Driver_Performance.py`: Driver performance analysis and reporting
- `pages/4_⚙️_Settings.py`: Database configuration and system diagnostics
- `utils.py`: Utility functions for data loading and processing
- `config.py`: Application configuration settings
- `translations.py`: Multilingual support
- `pdf_generator.py`: PDF report generation functions

## Troubleshooting

If you encounter database connection issues:

1. Navigate to the Settings & Diagnostics page
2. Check that your ODBC drivers are installed correctly
3. Verify your SQL Server credentials
4. Test the connection directly from the Settings page
5. Check the logs for detailed error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) - The web framework used
- [Plotly](https://plotly.com/) - For interactive visualizations
- [ReportLab](https://www.reportlab.com/) - For PDF generation
- [PyODBC](https://github.com/mkleehammer/pyodbc) - For SQL Server connectivity 