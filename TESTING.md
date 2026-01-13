# Testing the MCP Server in Cursor

## ✅ Verification Steps

### 1. Check Connection Status

In Cursor, you should see the MCP server status in the status bar or MCP panel. Look for:
- **Status**: "Connected" or "Ready"
- **Server**: `simple-utils-server`
- **Tools**: Should show 6 tools loaded

### 2. Verify Tools are Loaded

The following tools should be available:
1. `get_current_time` - Get current time
2. `get_current_date` - Get current date
3. `calculate` - Mathematical calculations
4. `get_timezone_info` - Timezone information
5. `format_number` - Number formatting
6. `execute_command` - Execute shell commands

## 🧪 How to Test in Cursor

### Method 1: Ask the AI to Use the Tools

Simply ask Cursor's AI to use the tools! The AI can automatically call them. Try these prompts:

#### Test Time Tools:
```
"What time is it right now?"
"Get the current date in US format"
"What's the time in New York?"
```

#### Test Calculator:
```
"Calculate sqrt(144) + 5 * 3"
"What's sin(pi/2) + cos(0)?"
"Calculate 2^10"
```

#### Test Number Formatting:
```
"Format the number 1234.5678 with 3 decimal places"
"Show me 1000000 in scientific notation"
```

#### Test Shell Commands:
```
"Run the command 'ls -la'"
"Execute 'echo hello world'"
"Run 'python --version'"
"Execute 'pwd' to show current directory"
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

## 📝 Example Test Scenarios

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

### Scenario 5: Format Number
**Ask Cursor:**
> "Format 1234567.89 with 2 decimal places"

**Expected Response:**
The AI should call `format_number` and return:
```json
{
  "original": 1234567.89,
  "formatted": "1234567.89",
  "decimals": 2,
  "scientific_notation": false
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

**Note:** ⚠️ Be careful with shell commands as they can execute arbitrary code on your server!

## 🔍 Debugging

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
```

## 🎯 Quick Test Checklist

- [ ] Server is running (`docker compose ps`)
- [ ] Connection shows as "Connected" in Cursor
- [ ] All 6 tools are visible/loaded
- [ ] Can ask AI to get current time → works
- [ ] Can ask AI to calculate math → works
- [ ] Can ask AI to get date → works
- [ ] Can ask AI about timezone → works
- [ ] Can ask AI to format numbers → works
- [ ] Can ask AI to run shell commands → works

## 💡 Tips

1. **Be specific**: Ask clearly what you want (e.g., "calculate 2+2" not just "math")
2. **Check responses**: The AI should show tool results in the chat
3. **Multiple tools**: You can ask for multiple operations in one request
4. **Error handling**: If a tool fails, the AI should show an error message

## 🐛 Troubleshooting

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
