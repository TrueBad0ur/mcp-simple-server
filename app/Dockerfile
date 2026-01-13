FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .

# Make server executable
RUN chmod +x server.py

# Expose port
EXPOSE 8000

# Run the HTTP MCP server
CMD ["python", "server.py"]
