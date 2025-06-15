# Apple Mail MCP Server

A custom Model Context Protocol (MCP) server that provides direct access to Apple Mail data without requiring network connections or complex authentication. This tool bypasses Apple Mail's API limitations by reading directly from the local SQLite databases.

## Features

- 🔍 **Search emails** by subject, sender, date, or content
- 📤 **Find sent emails** by specific users and dates
- 📊 **Database examination** to understand Apple Mail's structure
- 🏠 **Local-only access** - no network dependencies or passwords required
- 🛡️ **Privacy-preserving** - all data stays on your machine
- ⚙️ **Highly configurable** - easy to adapt for different systems

## Prerequisites

- macOS with Apple Mail
- Claude Desktop application
- Python 3.7 or higher
- Full Disk Access permissions (see setup instructions)

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/your-username/apple-mail-mcp-server.git
   cd apple-mail-mcp-server
   ```

2. **Make the script executable:**
   ```bash
   chmod +x apple_mail_mcp.py
   ```

## Configuration

### 1. Configure the Python Script

Edit the configuration section at the top of `apple_mail_mcp.py`:

```python
# CONFIGURATION - CUSTOMIZE THESE VARIABLES FOR YOUR SYSTEM

# Path to Apple Mail directory (usually ~/Library/Mail, but may vary)
MAIL_DIRECTORY = Path.home() / "Library" / "Mail"

# Your primary email address for searching sent emails
PRIMARY_EMAIL_ADDRESS = "your.email@example.com"  # ← CHANGE THIS

# Mail version directory (V10 is common for recent macOS versions)
MAIL_VERSION = "V10"  # May be V9, V8, V7 on older systems
```

**Important:** Replace `"your.email@example.com"` with your actual email address.

### 2. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration file. The location depends on your operating system:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple_mail": {
      "command": "python3",
      "args": ["/path/to/your/apple_mail_mcp.py"]
    }
  }
}
```

**Replace `/path/to/your/apple_mail_mcp.py`** with the actual path to the script.

**Example with full path:**
```json
{
  "mcpServers": {
    "apple_mail": {
      "command": "python3",
      "args": ["/Users/yourusername/apple-mail-mcp-server/apple_mail_mcp.py"]
    }
  }
}
```

### 3. Grant Permissions

Apple Mail data is protected by macOS security. You need to grant **Full Disk Access** to:

1. **Terminal** (for testing the script)
2. **Claude Desktop** (for the MCP server to work)

**Steps:**
1. Open **System Preferences/Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+ button** to add applications
3. Add both **Terminal** and **Claude Desktop**
4. Enable the toggles for both applications

### 4. Test the Installation

Before using with Claude Desktop, test the script manually:

```bash
cd /path/to/apple-mail-mcp-server
echo '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | python3 apple_mail_mcp.py
```

You should see a JSON response listing available tools.

### 5. Restart Claude Desktop

After configuration changes, restart Claude Desktop to load the new MCP server.

## Usage

Once configured, you can use these tools in Claude Desktop:

### Available Tools

- **`mail_search`** - Search emails in the database
- **`mail_list_accounts`** - List all email accounts  
- **`mail_find_sent_emails`** - Find emails sent by you on specific dates
- **`mail_search_by_subject`** - Search by subject text
- **`mail_examine_database`** - Examine database structure
- **`mail_search_all_tables`** - Comprehensive search across all tables

### Example Queries

- *"Find emails I sent yesterday"*
- *"Search for emails about 'project deadline'"*  
- *"Show me emails from last Monday"*
- *"List all my email accounts"*

## Troubleshooting

### Common Issues

**"Server disconnected" error:**
- Check that the script path in `claude_desktop_config.json` is correct
- Verify the script is executable: `chmod +x apple_mail_mcp.py`
- Ensure Claude Desktop has Full Disk Access

**"Envelope database not found" error:**
- Check if `MAIL_DIRECTORY` points to the correct location
- Try updating `MAIL_VERSION` (V9, V8, V7 for older systems)
- Ensure Apple Mail has been opened at least once

**"Email address not found" error:**
- Verify `PRIMARY_EMAIL_ADDRESS` matches exactly with your email
- Check spelling and case sensitivity
- Try using `mail_examine_database` to see available addresses

**Permission denied errors:**
- Grant Full Disk Access to Terminal and Claude Desktop
- Restart both applications after granting permissions

### Finding Your Mail Directory

If the default mail directory doesn't work, find yours:

1. Open **Apple Mail** → **Preferences** → **Accounts**
2. Select your account and note the server settings
3. Check these common locations:
   - `~/Library/Mail/`
   - `~/Library/Application Support/Mail/`

### Testing Manual Commands

```bash
# Test configuration
python3 apple_mail_mcp.py

# Check available tools
echo '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | python3 apple_mail_mcp.py

# Test account listing
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "mail_list_accounts", "arguments": {}}, "id": 2}' | python3 apple_mail_mcp.py
```

## How It Works

This MCP server accesses Apple Mail's local SQLite databases directly:

- **Database Location**: `~/Library/Mail/V10/MailData/Envelope Index`
- **46 tables** containing message metadata, addresses, subjects, attachments
- **Read-only access** - never modifies your mail data
- **No network calls** - works entirely with local files

## Security & Privacy

- ✅ **Local only** - no data sent to external servers
- ✅ **Read-only** - cannot modify or delete emails  
- ✅ **No passwords** - accesses local database files directly
- ✅ **Transparent** - open source code you can review

## Contributing

Contributions welcome! Please feel free to:

- Report bugs
- Suggest new features  
- Submit pull requests
- Improve documentation

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built using the Model Context Protocol (MCP) framework by Anthropic. This project demonstrates the power of custom MCP servers for accessing local data sources.
