# Testing the MCP Server in Cursor

## Authentication Setup

The MCP server requires API key authentication for security. Configure your environment:

### Environment Variables

```bash
# Required: API key for authentication
export MCP_API_KEY="your-secure-api-key-here"

# Optional: TLS certificates for HTTPS
export SSL_CERTFILE=/path/to/your/cert.pem
export SSL_KEYFILE=/path/to/your/key.pem
```

### Testing HTTP Endpoints

All requests must include the API key:

```bash
# Test health endpoint with authentication
curl -H "X-API-Key: your-secure-api-key-here" http://<remote-server-ip>:8000/health

# Test without API key (should fail with 401)
curl http://<remote-server-ip>:8000/health

# Test MCP tools endpoint
curl -H "X-API-Key: your-secure-api-key-here" http://<remote-server-ip>:8000/mcp/tools

# Test tool call
curl -H "X-API-Key: your-secure-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_current_time", "arguments": {}}}' \
  http://<remote-server-ip>:8000/mcp/call
```

## Verification Steps

### 1. Check Connection Status

In Cursor, you should see the MCP server status in the status bar or MCP panel. Look for:
- **Status**: "Connected" or "Ready"
- **Server**: `simple-utils-server`
- **Tools**: Should show 6 tools loaded

### 2. Verify Logging is Working

After using any tool, check that requests are being logged:

```bash
# Check if log file exists and has content
ls -la requests_log.txt
tail -20 requests_log.txt
```

You should see detailed log entries for each request with client information, timestamps, and responses.

### 2. Verify Tools are Loaded

The following tools should be available:
1. `get_current_time` - Get current time
2. `get_current_date` - Get current date
3. `calculate` - Mathematical calculations
4. `get_timezone_info` - Timezone information
5. `generate_random_number` - Generate random numbers
6. `execute_command` - Execute shell commands

## How to Test in Cursor

### Method 1: Ask the AI to Use the Tools

Simply ask Cursor's AI to use the tools! The AI can automatically call them. Copy-paste these commands directly into Cursor chat:

#### Time & Date Tools:
```
What time is it right now?
Get the current date in US format
What's the time in Tokyo right now?
What's today's date in European format?
```

#### Calculator Tool:
```
Calculate sqrt(144) + 5 * 3
What's sin(pi/2) + cos(0)?
Calculate 2^10
Solve for x: 2*x + 5 = 17
```

#### Random Number Generator:
```
Generate a random number between 1 and 100
Give me 5 random numbers from 0 to 10
Pick a random number between 100 and 200
Generate 10 random integers between -50 and 50
```

#### Shell Command Tools:
```
Run the command 'ls -la'
Execute 'echo hello world'
Run 'python --version'
Execute 'pwd' to show current directory
Run 'date' to show system time
Execute 'whoami' to show current user
```

#### Edge Cases & Error Testing:
```
Calculate 1/0 (should handle division by zero gracefully)
Generate 0 random numbers (should show error)
Generate 101 random numbers (should exceed limit)
Run the command 'nonexistent_command' (should handle command not found)
```

#### Complex Multi-Tool Requests:
```
What's the current time, and can you calculate the square root of 256?
Generate 3 random numbers between 1 and 10, and tell me what time it is in London
Calculate 2^8 and also run the command 'echo "test"'
```

### Complete Test Command List

**Copy and paste these commands one by one into Cursor chat:**

```bash
# Time & Date Tests
What time is it right now?
Get the current date in US format
What's the time in Tokyo right now?
What's today's date in European format?

# Calculator Tests
Calculate sqrt(144) + 5 * 3
What's sin(pi/2) + cos(0)?
Calculate 2^10
Solve for x: 2*x + 5 = 17

# Random Number Tests
Generate a random number between 1 and 100
Give me 5 random numbers from 0 to 10
Pick a random number between 100 and 200
Generate 10 random integers between -50 and 50

# Shell Command Tests
Run the command 'ls -la'
Execute 'echo hello world'
Run 'python --version'
Execute 'pwd' to show current directory
Run 'date' to show system time
Execute 'whoami' to show current user

# Error Testing
Calculate 1/0 (should handle division by zero gracefully)
Generate 0 random numbers (should show error)
Generate 101 random numbers (should exceed limit)
Run the command 'nonexistent_command' (should handle command not found)

# Multi-Tool Tests
What's the current time, and can you calculate the square root of 256?
Generate 3 random numbers between 1 and 10, and tell me what time it is in London
Calculate 2^8 and also run the command 'echo "test"'
```

### Method 2: Direct Tool Invocation

If Cursor has a tools panel or command palette:
1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Search for "MCP" or "Tools"
3. Select a tool to use

### Method 3: Check MCP Panel

1. Look for an MCP icon or panel in Cursor's sidebar
2. Expand `simple-utils-server`
3. You should see all 6 tools listed
4. Click on a tool to test it

## Example Test Scenarios

### Scenario 1: Get Current Time
**Ask Cursor:**
> "What's the current UTC time?"

**Expected Response:**
The AI should call `get_current_time` and return:
```json
{
  "utc_time": "2026-01-13 02:30:45 UTC",
  "local_time": "2026-01-13 02:30:45",
  "unix_timestamp": 1736737845,
  "iso_format": "2026-01-13T02:30:45+00:00"
}
```

### Scenario 2: Calculate Math
**Ask Cursor:**
> "Calculate the square root of 256 plus 10 times 5"

**Expected Response:**
The AI should call `calculate` with expression `sqrt(256) + 10 * 5` and return:
```json
{
  "expression": "sqrt(256) + 10 * 5",
  "result": 66.0,
  "type": "float"
}
```

### Scenario 3: Get Date
**Ask Cursor:**
> "What's today's date in European format?"

**Expected Response:**
The AI should call `get_current_date` with format `european` and return the date.

### Scenario 4: Timezone Info
**Ask Cursor:**
> "What time is it in Tokyo right now?"

**Expected Response:**
The AI should call `get_timezone_info` with timezone `Asia/Tokyo` and return timezone information.

### Scenario 5: Generate Random Number
**Ask Cursor:**
> "Generate a random number between 1 and 100"

**Expected Response:**
The AI should call `generate_random_number` and return:
```json
{
  "random_number": 42.73,
  "min_value": 1,
  "max_value": 100,
  "type": "single"
}
```

### Scenario 6: Generate Multiple Random Numbers
**Ask Cursor:**
> "Give me 5 random numbers between 0 and 10"

**Expected Response:**
The AI should call `generate_random_number` with count=5 and return:
```json
{
  "random_numbers": [2.45, 7.89, 1.23, 9.56, 4.78],
  "count": 5,
  "min_value": 0,
  "max_value": 10,
  "type": "multiple"
}
```

### Scenario 6: Execute Shell Command
**Ask Cursor:**
> "Run the command 'ls -la'"

**Expected Response:**
The AI should call `execute_command` and return:
```json
{
  "command": "ls -la",
  "return_code": 0,
  "stdout": "total 24\ndrwxr-xr-x ...",
  "stderr": "",
  "success": true
}
```

**Note:** Be careful with shell commands as they can execute arbitrary code on your server!

## Debugging

### Check Server Logs
```bash
docker compose logs -f mcp-server
```

You should see:
- `POST /sse HTTP/1.1" 200 OK` - Successful requests
- No error messages

### Check Cursor MCP Logs
In Cursor, check the MCP connection logs:
- Look for connection status
- Check for any error messages
- Verify tools are listed

### Test Direct HTTP Endpoints

You can also test the server directly:

```bash
# Health check (replace <remote-server-ip> with your server IP)
curl http://<remote-server-ip>:8000/health

# List tools
curl http://<remote-server-ip>:8000/mcp/tools

# Test a tool call (direct HTTP)
curl -X POST http://<remote-server-ip>:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_current_time", "arguments": {}}'

# Check logs (on host machine)
tail -20 logs/requests_log.txt
```

## Quick Test Checklist

### Basic Connectivity:
- [ ] Server is running (`docker compose ps`)
- [ ] Connection shows as "Connected" in Cursor
- [ ] All 6 tools are visible/loaded
- [ ] Requests are being logged to logs/requests_log.txt

### Tool Functionality:
- [ ] **Time**: `What time is it right now?` - returns current UTC/local time
- [ ] **Date**: `Get the current date in US format` - returns formatted date
- [ ] **Timezone**: `What's the time in Tokyo right now?` - returns Tokyo time info
- [ ] **Calculator**: `Calculate sqrt(16) * 4` - returns 16.0
- [ ] **Random**: `Generate 2 random numbers between 1 and 6` - returns array of numbers
- [ ] **Shell**: `Run 'echo "test"'` - returns command output

### Advanced Testing:
- [ ] **Multi-tool**: `What's the time and calculate 10 + 20?` - handles multiple tools
- [ ] **Error handling**: `Calculate 1/0` - shows appropriate error message
- [ ] **Edge cases**: `Generate 101 random numbers` - respects limits
- [ ] **Complex math**: `Solve for x: 2*x + 5 = 17` - handles equations

## Tips

1. **Be specific**: Ask clearly what you want (e.g., "calculate 2+2" not just "math")
2. **Check responses**: The AI should show tool results in the chat
3. **Multiple tools**: You can ask for multiple operations in one request
4. **Error handling**: If a tool fails, the AI should show an error message
5. **Test systematically**: Use the Complete Test Command List to test everything
6. **Check logs**: Verify requests are logged in `logs/requests_log.txt`
7. **Shell commands**: Be careful with shell commands - they execute on your server
8. **Complex queries**: Try combining multiple tools in one request for advanced testing

## Troubleshooting

### Tools not showing up?
- Restart Cursor completely
- Check server logs for errors
- Verify MCP configuration in Cursor settings

### "Tool not found" errors?
- Verify the tool name matches exactly
- Check server logs for the actual request
- Ensure server is running and connected

### Connection issues?
- Verify the URL in MCP config matches your server (should be `http://<remote-server-ip>:8000/sse`)
- Check firewall allows port 8000
- Test with `curl http://<remote-server-ip>:8000/health` to verify server is accessible
