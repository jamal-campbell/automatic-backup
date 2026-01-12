#!/bin/bash
#
# Setup Cron Job for Automatic NAS Backup
# This script installs a cron job to run the backup at 4 AM daily
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_to_nas.py"
CONFIG_FILE="$SCRIPT_DIR/config.json"
LOG_DIR="$SCRIPT_DIR/logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Automatic NAS Backup - Cron Setup"
echo "=========================================="
echo ""

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}Error: Backup script not found at $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found at $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Please copy config.example.json to config.json and configure it${NC}"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"
echo -e "${GREEN}✓${NC} Made backup script executable"

# Create logs directory
mkdir -p "$LOG_DIR"
echo -e "${GREEN}✓${NC} Created logs directory at $LOG_DIR"

# Create the cron job entry
CRON_JOB="0 4 * * * cd $SCRIPT_DIR && $BACKUP_SCRIPT $CONFIG_FILE >> $LOG_DIR/backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}⚠${NC}  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo -e "${GREEN}✓${NC} Cron job installed successfully!"
echo ""
echo "Schedule: Daily at 4:00 AM"
echo "Script: $BACKUP_SCRIPT"
echo "Config: $CONFIG_FILE"
echo "Logs: $LOG_DIR/backup.log"
echo ""
echo "To view your cron jobs, run: crontab -l"
echo "To remove the cron job, run: crontab -e (and delete the backup line)"
echo ""
echo "=========================================="
echo "Testing Configuration"
echo "=========================================="
echo ""

# Test run the backup script
echo "Running a test backup..."
echo ""

if $BACKUP_SCRIPT $CONFIG_FILE; then
    echo ""
    echo -e "${GREEN}✓${NC} Test backup completed successfully!"
    echo ""
    echo "Setup complete! Your backups will run automatically at 4 AM daily."
else
    echo ""
    echo -e "${RED}✗${NC} Test backup failed. Please check your configuration."
    echo "Check the error messages above and verify:"
    echo "  1. Source path exists and is accessible"
    echo "  2. NAS path is mounted or mount command is correct"
    echo "  3. Email settings are correct (if enabled)"
    exit 1
fi
