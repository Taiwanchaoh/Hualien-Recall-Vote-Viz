# Recall Vote Visualization Dashboard

A Dash-based web application for analyzing 2024 legislative election and 2025 recall vote data for Fu Kun-chi (傅崐萁).

## Features

- Interactive choropleth maps showing voting data by region
- Scatter plots comparing different voting metrics
- Cross-analysis between 2024 legislative election and 2025 recall vote
- Real-time highlighting across all visualizations

## Docker Setup

### Prerequisites

- Docker
- Docker Compose (optional, for easier management)

### Quick Start with Docker Compose

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   Open your browser and navigate to `http://localhost:8050`

### Manual Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t recall-vote-viz .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8050:8050 recall-vote-viz
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8050`

### Development with Docker

For development, you can mount the source code and data directories:

```bash
docker run -p 8050:8050 \
  -v $(pwd):/app \
  -v $(pwd)/data:/app/data \
  recall-vote-viz
```

## Local Development

### Prerequisites

- Python 3.11+
- uv (Python package manager)

### Setup

1. **Install uv:**
   ```bash
   pip install uv
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run the application:**
   ```bash
   uv run python dashboard.py
   ```

## Data Sources

The application uses the following data files:
- `data/combined_data.geoparquet` - Combined voting data with geographic information

## Application Structure

- `dashboard.py` - Main Dash application entry point
- `map_data_presentaiton.py` - Visualization components and callbacks
- `utils.py` - Utility functions and configurations
- `data/` - Data files directory

## Docker Image Details

The Docker image includes:
- Python 3.11 slim base image
- GDAL and geospatial libraries for geopandas
- uv for dependency management
- Non-root user for security
- Health checks for monitoring

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using port 8050
   lsof -i :8050
   # Kill the process or use a different port
   docker run -p 8051:8050 recall-vote-viz
   ```

2. **Build fails due to GDAL:**
   - Ensure you have enough memory for the build
   - The Dockerfile includes all necessary system dependencies

3. **Data not loading:**
   - Verify `data/combined_data.geoparquet` exists
   - Check file permissions in the container

### Logs

View application logs:
```bash
docker-compose logs -f dash-app
```

Or for manual Docker:
```bash
docker logs <container_id>
```
