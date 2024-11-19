FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY requirements first
COPY requirements_server.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_server.txt
RUN pip install gunicorn

RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt_tab
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN chmod -R 755 /usr/local/share/nltk_data

# Create logs directory
RUN mkdir -p logs

# Copy only rfp folder contents
COPY . /app/rfp/

# Set Python path to recognize the rfp module
ENV PYTHONPATH=/app

EXPOSE 5000

# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "6", "rfp.rfp_http_server:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "5", "--forwarded-allow-ips=*", "rfp.rfp_http_server:app"]

