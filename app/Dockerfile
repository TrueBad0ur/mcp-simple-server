FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application package
COPY . .

# Make sure all Python files are accessible
RUN find . -name "*.py" -exec chmod +r {} \;

# Expose port
EXPOSE 8000

# Run the HTTP MCP server
CMD ["python", "server.py"]
