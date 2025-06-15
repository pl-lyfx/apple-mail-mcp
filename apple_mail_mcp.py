#!/usr/bin/env python3
"""
Generic Apple Mail MCP Server
A Model Context Protocol server for accessing Apple Mail data from local files

CONFIGURATION:
Before using this server, customize the variables below for your system.
"""

import json
import sys
import sqlite3
import os
import email
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import logging

# ====================================================================
# CONFIGURATION - CUSTOMIZE THESE VARIABLES FOR YOUR SYSTEM
# ====================================================================

# Path to Apple Mail directory (usually ~/Library/Mail, but may vary)
# On macOS, this is typically: /Users/[username]/Library/Mail
# You can find your mail directory by checking Apple Mail > Preferences > Accounts
MAIL_DIRECTORY = Path.home() / "Library" / "Mail"

# Your primary email address for searching sent emails
# Replace with your main email address that you want to search for
PRIMARY_EMAIL_ADDRESS = "your.email@example.com"

# Mail version directory (V10 is common for recent macOS versions)
# Other possible values: V9, V8, V7 depending on your macOS version
MAIL_VERSION = "V10"

# Envelope database name (usually "Envelope Index")
ENVELOPE_DB_NAME = "Envelope Index"

# MCP Server configuration
MCP_SERVER_NAME = "apple-mail-mcp"
MCP_SERVER_VERSION = "1.0.0"

# Logging level (INFO, DEBUG, WARNING, ERROR)
LOGGING_LEVEL = logging.INFO

# ====================================================================
# END CONFIGURATION
# ====================================================================

# Configure logging to stderr
logging.basicConfig(level=LOGGING_LEVEL, stream=sys.stderr)
logger = logging.getLogger(__name__)

class AppleMailMCPServer:
    def __init__(self):
        self.mail_dir = MAIL_DIRECTORY
        self.mail_version = MAIL_VERSION
        self.envelope_db_name = ENVELOPE_DB_NAME
        self.primary_email = PRIMARY_EMAIL_ADDRESS

        # Validate configuration
        if not self.mail_dir.exists():
            logger.warning(f"Mail directory not found: {self.mail_dir}")
            logger.warning("Please update MAIL_DIRECTORY in the configuration section")

    def handle_request(self, request):
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": MCP_SERVER_NAME,
                        "version": MCP_SERVER_VERSION
                    }
                },
                "id": request_id
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": "mail_search",
                            "description": "Search emails in local Apple Mail database",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query"
                                    },
                                    "limit": {
                                        "type": "number",
                                        "description": "Maximum results",
                                        "default": 10
                                    }
                                }
                            }
                        },
                        {
                            "name": "mail_list_accounts",
                            "description": "List all mail accounts",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "mail_examine_database",
                            "description": "Examine the envelope database structure to find tables and schemas",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "mail_search_all_tables",
                            "description": "Search for emails across all tables in the envelope database",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "date_filter": {
                                        "type": "string",
                                        "description": "Date to search for (YYYY-MM-DD)"
                                    },
                                    "limit": {
                                        "type": "number",
                                        "description": "Maximum results per table",
                                        "default": 10
                                    }
                                }
                            }
                        },
                        {
                            "name": "mail_find_sent_emails",
                            "description": "Find emails sent by the user on a specific date",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "date_filter": {
                                        "type": "string",
                                        "description": "Date to search for (YYYY-MM-DD)"
                                    },
                                    "email_address": {
                                        "type": "string",
                                        "description": f"Email address to search for (default: {PRIMARY_EMAIL_ADDRESS})"
                                    },
                                    "limit": {
                                        "type": "number",
                                        "description": "Maximum results",
                                        "default": 10
                                    }
                                }
                            }
                        },
                        {
                            "name": "mail_search_by_subject",
                            "description": "Search for emails by subject text on a specific date",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "subject_text": {
                                        "type": "string",
                                        "description": "Subject text to search for"
                                    },
                                    "date_filter": {
                                        "type": "string",
                                        "description": "Date to search for (YYYY-MM-DD)"
                                    },
                                    "limit": {
                                        "type": "number",
                                        "description": "Maximum results",
                                        "default": 10
                                    }
                                }
                            }
                        }
                    ]
                },
                "id": request_id
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                if tool_name == "mail_search":
                    result = self.search_emails(arguments)
                elif tool_name == "mail_list_accounts":
                    result = self.list_accounts()
                elif tool_name == "mail_examine_database":
                    result = self.examine_database()
                elif tool_name == "mail_search_all_tables":
                    result = self.search_all_tables(arguments)
                elif tool_name == "mail_find_sent_emails":
                    result = self.find_sent_emails(arguments)
                elif tool_name == "mail_search_by_subject":
                    result = self.search_by_subject(arguments)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        },
                        "id": request_id
                    }

                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    },
                    "id": request_id
                }

            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    },
                    "id": request_id
                }

        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }

    def _get_envelope_db_path(self):
        """Get the path to the envelope database"""
        return self.mail_dir / self.mail_version / "MailData" / self.envelope_db_name

    def list_accounts(self):
        """List mail accounts"""
        result = []

        version_dir = self.mail_dir / self.mail_version
        if version_dir.exists():
            result.append(f"Mail accounts found in {self.mail_version}:")
            for item in version_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    result.append(f"  - {item.name}")
        else:
            result.append(f"No {self.mail_version} mail directory found")
            result.append(f"Searched in: {self.mail_dir}")
            result.append(f"Try updating MAIL_VERSION in configuration (common values: V10, V9, V8)")

        return "\n".join(result)

    def search_emails(self, args):
        """Search emails in envelope database"""
        query = args.get("query", "")
        limit = args.get("limit", 10)

        # Try to find envelope database
        db_path = self._get_envelope_db_path()

        if not db_path.exists():
            return f"Envelope database not found at: {db_path}\nPlease check MAIL_DIRECTORY and MAIL_VERSION configuration"

        try:
            # Connect read-only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Simple search
            if query:
                sql = """
                    SELECT ROWID, subject, sender,
                           datetime(date_received, 'unixepoch') as date
                    FROM messages
                    WHERE subject LIKE ? OR sender LIKE ?
                    ORDER BY date_received DESC
                    LIMIT ?
                """
                cursor.execute(sql, [f"%{query}%", f"%{query}%", limit])
            else:
                sql = """
                    SELECT ROWID, subject, sender,
                           datetime(date_received, 'unixepoch') as date
                    FROM messages
                    ORDER BY date_received DESC
                    LIMIT ?
                """
                cursor.execute(sql, [limit])

            messages = cursor.fetchall()
            conn.close()

            if not messages:
                return "No messages found"

            result = [f"Found {len(messages)} messages:\n"]
            for msg in messages:
                result.append(f"ID: {msg['ROWID']}")
                result.append(f"Subject: {msg['subject'] or '(no subject)'}")
                result.append(f"From: {msg['sender'] or '(unknown)'}")
                result.append(f"Date: {msg['date']}")
                result.append("---")

            return "\n".join(result)

        except Exception as e:
            return f"Database error: {str(e)}"

    def examine_database(self):
        """Examine the envelope database structure"""
        db_path = self._get_envelope_db_path()

        if not db_path.exists():
            return f"Envelope database not found at: {db_path}\nPlease check MAIL_DIRECTORY and MAIL_VERSION configuration"

        try:
            # Connect read-only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            result = [f"Examining envelope database at: {db_path}\n"]

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()

            result.append(f"Found {len(tables)} tables:")
            for table in tables:
                table_name = table[0]
                result.append(f"\n=== Table: {table_name} ===")

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                result.append("Columns:")
                for col in columns:
                    result.append(f"  - {col[1]} ({col[2]})")

                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    result.append(f"Row count: {count}")
                except:
                    result.append("Row count: Unable to determine")

                # Get sample data for interesting tables
                if table_name in ['messages', 'mailboxes', 'subjects', 'addresses']:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        samples = cursor.fetchall()
                        if samples:
                            result.append("Sample rows:")
                            for i, sample in enumerate(samples):
                                result.append(f"  Row {i+1}: {dict(sample)}")
                    except Exception as e:
                        result.append(f"Sample data error: {e}")

            # Check for views
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
            views = cursor.fetchall()

            if views:
                result.append(f"\nFound {len(views)} views:")
                for view in views:
                    result.append(f"  - {view[0]}")

            conn.close()
            return "\n".join(result)

        except Exception as e:
            return f"Database examination error: {str(e)}"

    def search_all_tables(self, args):
        """Search for emails across all tables in the envelope database"""
        date_filter = args.get("date_filter")
        limit = args.get("limit", 10)

        db_path = self._get_envelope_db_path()

        if not db_path.exists():
            return f"Envelope database not found at: {db_path}\nPlease check MAIL_DIRECTORY and MAIL_VERSION configuration"

        try:
            # Connect read-only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            result = [f"Searching all tables for emails"]
            if date_filter:
                result[0] += f" on {date_filter}"
            result.append("")

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()

            # Search in each table that might contain email data
            for table in tables:
                table_name = table[0]

                try:
                    # Get table schema to understand structure
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    # Skip tables that clearly don't contain email data
                    if not any(col in column_names for col in ['subject', 'sender', 'date_received', 'date_sent', 'message_id']):
                        continue

                    result.append(f"=== Searching table: {table_name} ===")

                    # Build search query based on available columns
                    where_conditions = []
                    params = []

                    if date_filter:
                        # Look for date columns
                        date_columns = [col for col in column_names if 'date' in col.lower()]
                        if date_columns:
                            date_col = date_columns[0]  # Use first date column found
                            try:
                                # Convert date to timestamp for comparison
                                target_date = datetime.strptime(date_filter, "%Y-%m-%d")
                                start_timestamp = int(target_date.timestamp())
                                end_timestamp = int((target_date + timedelta(days=1)).timestamp())

                                where_conditions.append(f"{date_col} >= ? AND {date_col} < ?")
                                params.extend([start_timestamp, end_timestamp])
                            except:
                                # Fallback to string comparison
                                where_conditions.append(f"datetime({date_col}, 'unixepoch') LIKE ?")
                                params.append(f"%{date_filter}%")

                    # Build and execute query
                    if 'subject' in column_names and 'sender' in column_names:
                        # Looks like a messages table
                        select_cols = ['ROWID']
                        for col in ['subject', 'sender', 'recipients', 'to_recipients']:
                            if col in column_names:
                                select_cols.append(col)

                        # Add date column with readable format
                        for date_col in ['date_received', 'date_sent']:
                            if date_col in column_names:
                                select_cols.append(f"datetime({date_col}, 'unixepoch') as {date_col}_readable")
                                break

                        sql = f"SELECT {', '.join(select_cols)} FROM {table_name}"
                        if where_conditions:
                            sql += f" WHERE {' AND '.join(where_conditions)}"
                        sql += f" ORDER BY ROWID DESC LIMIT ?"
                        params.append(limit)

                        cursor.execute(sql, params)
                        messages = cursor.fetchall()

                        if messages:
                            result.append(f"Found {len(messages)} messages:")
                            for msg in messages:
                                result.append(f"  ID: {msg['ROWID']}")
                                if 'subject' in msg.keys():
                                    result.append(f"  Subject: {msg['subject'] or '(no subject)'}")
                                if 'sender' in msg.keys():
                                    result.append(f"  From: {msg['sender'] or '(unknown)'}")
                                if 'recipients' in msg.keys():
                                    result.append(f"  To: {msg['recipients'] or '(unknown)'}")
                                # Show readable date
                                for key in msg.keys():
                                    if key.endswith('_readable'):
                                        result.append(f"  Date: {msg[key]}")
                                        break
                                result.append("  ---")
                        else:
                            result.append("No matching messages found")
                    else:
                        # Generic table search
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        samples = cursor.fetchall()
                        if samples:
                            result.append(f"Sample data (first 3 rows):")
                            for sample in samples:
                                result.append(f"  {dict(sample)}")

                    result.append("")

                except Exception as e:
                    result.append(f"Error searching {table_name}: {e}")
                    result.append("")

            conn.close()
            return "\n".join(result)

        except Exception as e:
            return f"Database search error: {str(e)}"

    def find_sent_emails(self, args):
        """Find emails sent by the user on a specific date"""
        date_filter = args.get("date_filter")
        email_address = args.get("email_address", self.primary_email)
        limit = args.get("limit", 10)

        db_path = self._get_envelope_db_path()

        if not db_path.exists():
            return f"Envelope database not found at: {db_path}\nPlease check MAIL_DIRECTORY and MAIL_VERSION configuration"

        try:
            # Connect read-only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            result = [f"Searching for emails sent by {email_address}"]
            if date_filter:
                result[0] += f" on {date_filter}"
            result.append("")

            # Step 1: Find the address ID for the user's email
            cursor.execute("SELECT ROWID FROM addresses WHERE address = ?", (email_address,))
            address_row = cursor.fetchone()

            if not address_row:
                return f"Email address {email_address} not found in addresses table\nTry updating PRIMARY_EMAIL_ADDRESS in configuration"

            address_id = address_row[0]
            result.append(f"Found address ID: {address_id}")

            # Step 2: Find sender ID(s) associated with this address
            cursor.execute("SELECT sender FROM sender_addresses WHERE address = ?", (address_id,))
            sender_rows = cursor.fetchall()

            if not sender_rows:
                return f"No sender records found for address ID {address_id}"

            sender_ids = [row[0] for row in sender_rows]
            result.append(f"Found sender IDs: {sender_ids}")

            # Step 3: Find messages sent by this user
            sender_placeholders = ','.join(['?'] * len(sender_ids))

            # Build query for messages where user is the sender
            where_conditions = [f"sender IN ({sender_placeholders})"]
            params = sender_ids.copy()

            # Add date filter if specified
            if date_filter:
                try:
                    target_date = datetime.strptime(date_filter, "%Y-%m-%d")
                    start_timestamp = int(target_date.timestamp())
                    end_timestamp = int((target_date + timedelta(days=1)).timestamp())

                    where_conditions.append("date_sent >= ? AND date_sent < ?")
                    params.extend([start_timestamp, end_timestamp])
                except:
                    where_conditions.append("datetime(date_sent, 'unixepoch') LIKE ?")
                    params.append(f"%{date_filter}%")

            # Build the full query
            sql = """
                SELECT m.ROWID, m.message_id, s.subject,
                       datetime(m.date_sent, 'unixepoch') as sent_date,
                       datetime(m.date_received, 'unixepoch') as received_date,
                       mb.url as mailbox_url
                FROM messages m
                LEFT JOIN subjects s ON m.subject = s.ROWID
                LEFT JOIN mailboxes mb ON m.mailbox = mb.ROWID
                WHERE """ + " AND ".join(where_conditions) + """
                ORDER BY m.date_sent DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(sql, params)
            sent_messages = cursor.fetchall()

            if not sent_messages:
                result.append("No sent messages found matching criteria")
                result.append(f"Note: Check if {email_address} is correct in configuration")
            else:
                result.append(f"\nFound {len(sent_messages)} sent messages:")
                result.append("")

                for msg in sent_messages:
                    result.append(f"Message ID: {msg['ROWID']}")
                    result.append(f"Subject: {msg['subject'] or '(no subject)'}")
                    result.append(f"Sent Date: {msg['sent_date']}")
                    result.append(f"Received Date: {msg['received_date']}")
                    result.append(f"Mailbox: {msg['mailbox_url']}")

                    # Try to find recipients
                    cursor.execute("""
                        SELECT a.address
                        FROM recipients r
                        JOIN addresses a ON r.address = a.ROWID
                        WHERE r.message = ? AND r.type = 1
                        LIMIT 3
                    """, (msg['ROWID'],))
                    recipients = cursor.fetchall()

                    if recipients:
                        recipient_list = [r[0] for r in recipients]
                        result.append(f"To: {', '.join(recipient_list)}")

                    result.append("---")

            conn.close()
            return "\n".join(result)

        except Exception as e:
            return f"Error finding sent emails: {str(e)}"

    def search_by_subject(self, args):
        """Search for emails by subject text on a specific date"""
        subject_text = args.get("subject_text", "")
        date_filter = args.get("date_filter")
        limit = args.get("limit", 10)

        if not subject_text:
            return "Subject text is required"

        db_path = self._get_envelope_db_path()

        if not db_path.exists():
            return f"Envelope database not found at: {db_path}\nPlease check MAIL_DIRECTORY and MAIL_VERSION configuration"

        try:
            # Connect read-only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            result = [f"Searching for emails with subject containing: '{subject_text}'"]
            if date_filter:
                result[0] += f" on {date_filter}"
            result.append("")

            # Step 1: Find subject IDs that match the text
            cursor.execute("SELECT ROWID, subject FROM subjects WHERE subject LIKE ?", (f"%{subject_text}%",))
            subject_rows = cursor.fetchall()

            if not subject_rows:
                return f"No subjects found containing '{subject_text}'"

            result.append(f"Found {len(subject_rows)} matching subjects:")
            for subj in subject_rows:
                result.append(f"  Subject ID {subj[0]}: {subj[1]}")
            result.append("")

            # Step 2: Find messages with these subject IDs
            subject_ids = [row[0] for row in subject_rows]
            subject_placeholders = ','.join(['?'] * len(subject_ids))

            # Build query for messages with these subjects
            where_conditions = [f"m.subject IN ({subject_placeholders})"]
            params = subject_ids.copy()

            # Add date filter if specified
            if date_filter:
                try:
                    target_date = datetime.strptime(date_filter, "%Y-%m-%d")
                    start_timestamp = int(target_date.timestamp())
                    end_timestamp = int((target_date + timedelta(days=1)).timestamp())

                    where_conditions.append("(m.date_sent >= ? AND m.date_sent < ?) OR (m.date_received >= ? AND m.date_received < ?)")
                    params.extend([start_timestamp, end_timestamp, start_timestamp, end_timestamp])
                except:
                    where_conditions.append("datetime(m.date_sent, 'unixepoch') LIKE ? OR datetime(m.date_received, 'unixepoch') LIKE ?")
                    params.extend([f"%{date_filter}%", f"%{date_filter}%"])

            # Build the full query
            sql = """
                SELECT m.ROWID, m.message_id, s.subject,
                       datetime(m.date_sent, 'unixepoch') as sent_date,
                       datetime(m.date_received, 'unixepoch') as received_date,
                       mb.url as mailbox_url,
                       m.sender,
                       sender_addr.address as sender_address
                FROM messages m
                LEFT JOIN subjects s ON m.subject = s.ROWID
                LEFT JOIN mailboxes mb ON m.mailbox = mb.ROWID
                LEFT JOIN sender_addresses sa ON m.sender = sa.sender
                LEFT JOIN addresses sender_addr ON sa.address = sender_addr.ROWID
                WHERE """ + " AND ".join(where_conditions) + """
                ORDER BY m.date_sent DESC, m.date_received DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(sql, params)
            messages = cursor.fetchall()

            if not messages:
                result.append("No messages found matching criteria")
            else:
                result.append(f"Found {len(messages)} messages:")
                result.append("")

                for msg in messages:
                    result.append(f"Message ID: {msg['ROWID']}")
                    result.append(f"Subject: {msg['subject'] or '(no subject)'}")
                    result.append(f"Sent Date: {msg['sent_date']}")
                    result.append(f"Received Date: {msg['received_date']}")
                    result.append(f"Sender Address: {msg['sender_address'] or '(unknown)'}")
                    result.append(f"Mailbox: {msg['mailbox_url']}")

                    # Try to find recipients
                    cursor.execute("""
                        SELECT a.address
                        FROM recipients r
                        JOIN addresses a ON r.address = a.ROWID
                        WHERE r.message = ? AND r.type = 1
                        LIMIT 3
                    """, (msg['ROWID'],))
                    recipients = cursor.fetchall()

                    if recipients:
                        recipient_list = [r[0] for r in recipients]
                        result.append(f"To: {', '.join(recipient_list)}")

                    result.append("---")

            conn.close()
            return "\n".join(result)

        except Exception as e:
            return f"Error searching by subject: {str(e)}"

def main():
    """Main server loop"""
    server = AppleMailMCPServer()
    logger.info(f"Apple Mail MCP Server started")
    logger.info(f"Mail directory: {MAIL_DIRECTORY}")
    logger.info(f"Primary email: {PRIMARY_EMAIL_ADDRESS}")

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)

                # Handle notifications (no response needed)
                if request.get("method") == "notifications/initialized":
                    continue

                response = server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                logger.error(f"JSON error: {e}")
                continue

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
