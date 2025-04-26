FROM miktex/miktex:latest as miktex-base

# Create a multi-stage build with MiKTeX and Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for LaTeX and PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    ghostscript \
    xz-utils \
    libfontconfig1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy MiKTeX binaries from the miktex-base image
COPY --from=miktex-base /usr/local/bin/miktex* /usr/local/bin/
COPY --from=miktex-base /usr/local/bin/initexmf /usr/local/bin/
COPY --from=miktex-base /usr/local/bin/tex* /usr/local/bin/
COPY --from=miktex-base /usr/local/bin/pdf* /usr/local/bin/
COPY --from=miktex-base /opt/miktex /opt/miktex

# Set environment variables for MiKTeX
ENV PATH="/opt/miktex/bin:${PATH}"
ENV MIKTEX_USERCONFIG=/miktex/.miktex/texmfs/config
ENV MIKTEX_USERDATA=/miktex/.miktex/texmfs/data
ENV MIKTEX_USERINSTALL=/miktex/.miktex/texmfs/install

# Create MiKTeX user directory
RUN mkdir -p /miktex/.miktex/texmfs/config \
    /miktex/.miktex/texmfs/data \
    /miktex/.miktex/texmfs/install \
    && chmod -R 777 /miktex

# Configure MiKTeX for non-interactive use
RUN miktexsetup finish \
    && initexmf --set-config-value [MPM]AutoInstall=1 \
    && mpm --verbose --update-db

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories if they don't exist
RUN mkdir -p /app/assets/generated/latex
RUN mkdir -p /app/assets/generated/pdf
RUN mkdir -p /app/assets/photos

# Expose port
EXPOSE 8000

# Set environment variable
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]