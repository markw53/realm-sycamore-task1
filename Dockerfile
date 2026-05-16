FROM node:20-slim

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Make "python" available
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install pytest globally
RUN pip3 install --no-cache-dir --break-system-packages pytest

# Copy source Python repo
WORKDIR /source
COPY source_repo/ /source/

# Clean unwanted artifacts inside the image
RUN rm -rf /source/.git /source/.venv && \
    find /source -type d -name "__pycache__" -exec rm -rf {} + && \
    find /source -type f -name "*.pyc" -delete && \
    find /source -type f -name ".DS_Store" -delete

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r /source/requirements.txt

# Verify source runs
RUN cd /source && python3 -m src.main

# Create target directory
RUN mkdir -p /target

# Copy translated TypeScript project into /target
COPY target/ /target/

# Install Node dependencies for the TS project
WORKDIR /target
RUN npm install

# Build the TypeScript project
RUN npx tsc
