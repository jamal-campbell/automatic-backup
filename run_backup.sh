#!/bin/bash
#
# Manual Backup Runner
# Use this script to run a backup manually for testing
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_to_nas.py"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at $CONFIG_FILE"
    echo "Please copy config.example.json to config.json and configure it"
    exit 1
fi

# Make sure the backup script is executable
chmod +x "$BACKUP_SCRIPT"

# Run the backup
echo "Starting manual backup..."
echo "================================"
"$BACKUP_SCRIPT" "$CONFIG_FILE"
exit_code=$?

echo "================================"
if [ $exit_code -eq 0 ]; then
    echo "Backup completed successfully!"
else
    echo "Backup failed with exit code $exit_code"
fi

exit $exit_code
