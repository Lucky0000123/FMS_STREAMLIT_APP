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

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose
- Git

### Deployment Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd FMS_ST
```

2. Build and start the Docker container:
```bash
docker-compose up --build
```

3. Access the dashboard:
- Open your web browser and navigate to `http://localhost:8501`
- The dashboard will be available on port 8501

### Docker Commands

- Start the application:
```bash
docker-compose up
```

- Start in detached mode:
```bash
docker-compose up -d
```

- Stop the application:
```bash
docker-compose down
```

- View logs:
```bash
docker-compose logs -f
```

- Rebuild the container:
```bash
docker-compose up --build
```

### Volume Mounts

The following directories are mounted as volumes:
- `./data`: For storing data files
- `./reports`: For storing generated reports
- `./assets`: For storing static assets

### Environment Variables

The following environment variables can be configured in the `docker-compose.yml` file:
- `STREAMLIT_SERVER_PORT`: Port for the Streamlit server (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `TZ`: Timezone (default: Asia/Jakarta)

### Troubleshooting

1. If the container fails to start:
```bash
docker-compose logs
```

2. To rebuild from scratch:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

3. If you need to access the container shell:
```bash
docker-compose exec fms-dashboard /bin/bash
```

### Notes

- The application requires a SQL Server connection. Make sure to configure the connection settings in the application.
- The dashboard is configured to run on port 8501 by default.
- Data persistence is handled through Docker volumes.
- The container will automatically restart unless explicitly stopped.

## Network Share Deployment

### Prerequisites

- Docker
- Docker Compose
- Network access to `\\10.211.10.2\Users\Administrator\streamlit_fms`
- SQL Server access (10.211.10.2)

### Deployment Steps

1. Clone the repository to the network share:
```bash
git clone <repository-url> \\10.211.10.2\Users\Administrator\streamlit_fms
cd \\10.211.10.2\Users\Administrator\streamlit_fms
```

2. Run the deployment script:
   - For Windows: Double-click `deploy.bat` or run it from Command Prompt
   - For Linux/Mac: Run `./deploy.sh`

3. Access the dashboard:
   - Open your web browser and navigate to `http://localhost:8502`
   - The dashboard will be available on port 8502

### Directory Structure

The application uses the following directories on the network share:
- `\\10.211.10.2\Users\Administrator\streamlit_fms\data`: For storing data files
- `\\10.211.10.2\Users\Administrator\streamlit_fms\reports`: For storing generated reports
- `\\10.211.10.2\Users\Administrator\streamlit_fms\assets`: For storing static assets

### Environment Variables

The following environment variables are configured in the `docker-compose.yml` file:
- `STREAMLIT_SERVER_PORT`: Port for the Streamlit server (default: 8502)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `TZ`: Timezone (default: Asia/Jakarta)
- `SQL_SERVER`: SQL Server address (10.211.10.2)
- `SQL_DATABASE`: Database name (FMS_DB)
- `SQL_USERNAME`: Database username
- `SQL_PASSWORD`: Database password

### Troubleshooting

1. If the container fails to start:
```bash
docker-compose logs
```

2. To rebuild from scratch:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

3. If you need to access the container shell:
```bash
docker-compose exec fms-dashboard /bin/bash
```

4. Network Share Access Issues:
   - Ensure you have proper permissions on the network share
   - Check if the network share is accessible
   - Verify the directory structure exists

### Notes

- The application is configured to run on port 8502
- Data persistence is handled through network share volumes
- The container will automatically restart unless explicitly stopped
- Make sure the SQL Server (10.211.10.2) is accessible from the Docker container

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