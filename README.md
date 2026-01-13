# Simple MCP Server

A simple, self-contained MCP (Model Context Protocol) server with basic utility functions. **No API keys, no credit cards, no external dependencies required!**

## Features

- ✅ **Get Current Time** - UTC and local time
- ✅ **Get Current Date** - Multiple date formats
- ✅ **Calculate** - Basic mathematical operations
- ✅ **Timezone Info** - Get timezone information
- ✅ **Format Numbers** - Format numbers with various options
- ✅ **Execute Shell Commands** - Run shell commands and get output

## 📖 Complete Setup Guide

### Step 1: Start the Server

1. **Navigate to the project directory:**
   ```bash
   cd mcp
   ```

2. **Build and start the Docker container:**
   ```bash
   docker compose up --build
   ```

   This will:
   - Build the Docker image
   - Start the container
   - Expose the server on port 8000

3. **Verify the server is running:**
   ```bash
   # Check container status
   docker compose ps
   
   # Check logs (in another terminal)
   docker compose logs -f mcp-server
   
   # Test health endpoint (replace <remote-server-ip> with your server IP)
   curl http://<remote-server-ip>:8000/health
   ```

   You should see:
   - Container status: `Up`
   - Logs showing: `Uvicorn running on http://0.0.0.0:8000`
   - Health check returning: `{"status": "healthy"}`

### Step 2: Configure Cursor IDE

1. **Open Cursor IDE**

2. **Open Command Palette:**
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type: `MCP Settings` or `MCP: Configure`

3. **Add New MCP Server:**
   - Click "Add New" or "+" button
   - You'll be prompted to add server configuration

4. **Enter Server Configuration:**
   
   **Option A: Manual Entry**
   - **Name**: `simple-utils-server`
   - **URL**: `http://<remote-server-ip>:8000/sse`
     - Replace `<remote-server-ip>` with your actual server IP address
     - Example: `http://192.168.1.100:8000/sse` or `http://example.com:8000/sse`
   - **Transport**: `sse` or `SSE`

   **Option B: Import from mcp.json**
   - Open the `mcp.json` file in this repository
   - Copy the entire contents
   - Paste it into the MCP settings configuration
   - **Important**: Replace `<remote-server-ip>` with your actual server IP address
   - The configuration should look like:
     ```json
     {
       "mcpServers": {
         "simple-utils-server": {
           "url": "http://<remote-server-ip>:8000/sse",
           "transport": "sse"
         }
       }
     }
     ```

5. **Save the Configuration:**
   - Click "Save" or press `Enter`
   - Cursor will automatically connect to the server

6. **Verify Connection:**
   - Look for the MCP server status in Cursor's status bar
   - It should show: `simple-utils-server: Connected`
   - You should see 6 tools loaded

### Step 3: Test the Connection

1. **In Cursor's chat, try asking:**
   ```
   "What time is it right now?"
   ```

2. **The AI should:**
   - Automatically use the `get_current_time` tool
   - Return the current time information

3. **Try other commands:**
   ```
   "Calculate sqrt(144) + 5"
   "Run the command 'echo hello world'"
   "Get today's date"
   ```

### Troubleshooting Connection Issues

- **Server not connecting?**
  - Verify server is running: `docker compose ps`
  - Check server logs: `docker compose logs mcp-server`
  - Test server directly: `curl http://<remote-server-ip>:8000/health`

- **Connection refused?**
  - Check firewall allows port 8000
  - Verify the IP address is correct
  - Ensure server is listening on `0.0.0.0` (it is by default)

- **Tools not loading?**
  - Restart Cursor completely
  - Check MCP settings configuration is correct
  - Verify the URL includes `/sse` at the end

## Quick Start (Summary)

```bash
# 1. Start server
docker compose up --build

# 2. In Cursor: Ctrl+Shift+P -> MCP Settings -> Add New
#    URL: http://<remote-server-ip>:8000/sse
#    Transport: sse

# 3. Test: Ask "What time is it?"
```

## Available Tools

### 1. get_current_time
Get the current time in UTC and local timezone.

**Example:**
```json
{
  "tool": "get_current_time",
  "arguments": {}
}
```

### 2. get_current_date
Get the current date in various formats.

**Example:**
```json
{
  "tool": "get_current_date",
  "arguments": {
    "format": "iso"
  }
}
```

**Formats**: `iso`, `us`, `european`, `unix`

### 3. calculate
Perform basic mathematical calculations.

**Example:**
```json
{
  "tool": "calculate",
  "arguments": {
    "expression": "sqrt(16) + 2 * 3"
  }
}
```

**Supported functions**: `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `pow`, `abs`, `round`, `floor`, `ceil`, `min`, `max`, `sum`
**Constants**: `pi`, `e`

### 4. get_timezone_info
Get information about a timezone.

**Example:**
```json
{
  "tool": "get_timezone_info",
  "arguments": {
    "timezone": "America/New_York"
  }
}
```

### 5. format_number
Format a number with various options.

**Example:**
```json
{
  "tool": "format_number",
  "arguments": {
    "number": 1234.5678,
    "decimals": 2,
    "scientific": false
  }
}
```

### 6. execute_command
Execute a shell command and return the output. **⚠️ WARNING: Use with caution as this can execute arbitrary commands.**

**Example:**
```json
{
  "tool": "execute_command",
  "arguments": {
    "command": "ls -la",
    "working_directory": "/tmp",
    "timeout": 30
  }
}
```

**Parameters:**
- `command` (required): Shell command to execute
- `working_directory` (optional): Working directory for the command
- `timeout` (optional): Timeout in seconds (default: 30)

**Example commands:**
- `"ls -la"` - List files
- `"echo hello world"` - Print text
- `"python --version"` - Check Python version
- `"pwd"` - Print working directory
- `"date"` - Get current date

## Testing

### Test with curl:

```bash
# Health check (replace <remote-server-ip> with your server IP)
curl http://<remote-server-ip>:8000/health

# Root endpoint
curl http://<remote-server-ip>:8000/
```

### Test MCP Tools (using HTTP directly):

The server uses SSE for MCP protocol, but you can test the basic endpoints.

## Firewall Configuration

If accessing from outside your VPS, open port 8000:

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

## Development

### Run Locally (without Docker):

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python http_server.py
```

The server will be available at `http://<remote-server-ip>:8000`

### Project Structure

```
mcp/
├── server.py          # Stdio MCP server (for local use)
├── http_server.py     # HTTP/SSE MCP server (for remote use)
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker image definition
├── docker-compose.yml # Docker compose configuration
└── README.md          # This file
```

## Troubleshooting

1. **Container won't start**: Check logs with `docker compose logs mcp-server`

2. **Port already in use**: Change port in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Use 8001 instead
   ```

3. **Can't connect from Cursor**: 
   - Verify firewall allows port 8000
   - Check that container is running: `docker compose ps`
   - Verify the URL is correct: `http://<remote-server-ip>:8000/sse`

4. **Connection refused**: 
   - Ensure the server is listening on `0.0.0.0` (it is by default)
   - Check VPS firewall rules

## Security Notes

- The server has CORS enabled for all origins (for testing)
- For production, consider:
  - Restricting CORS origins
  - Adding authentication
  - Using HTTPS with a reverse proxy (nginx/traefik)
  - Restricting firewall access to trusted IPs

## Useful Commands

```bash
# View logs
docker compose logs -f mcp-server

# Restart the server
docker compose restart mcp-server

# Stop the server
docker compose down

# Rebuild and restart
docker compose up -d --build

# Check container status
docker compose ps
```

## No External Dependencies!

This server uses only:
- Python standard library (datetime, math, json)
- MCP SDK (for protocol)
- FastAPI/Uvicorn (for HTTP server)

**No API keys, no credit cards, no external services required!**
