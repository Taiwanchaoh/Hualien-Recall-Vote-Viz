# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for geopandas and other geospatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgdal-dev \
    libgeotiff-dev \
    libtiff-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libhdf5-dev \
    libnetcdf-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock .python-version ./

# Copy application files
COPY dashboard.py map_data_presentaiton.py utils.py ./

# Copy data directory
COPY data/ ./data/

# Install dependencies using uv
RUN uv sync --frozen

# Expose port 8050 (Dash default)
EXPOSE 8050

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Set the default command to run the Dash app
CMD ["uv", "run", "python", "dashboard.py"] 