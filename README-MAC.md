# Mac Setup Guide for Buffalo NAS Backup

This guide shows you how to set up automatic backups on macOS to your Buffalo LinkStation NAS.

## Quick Start for Mac Users

### Option 1: Use Finder to Mount NAS (Easiest - Recommended)

This is the **simplest and most reliable** method for Mac users.

**Step 1: Mount your Buffalo NAS via Finder**

1. Open **Finder**
2. Press `Cmd+K` (or go to **Go > Connect to Server**)
3. Enter your NAS address:
   ```
   smb://LS210XXXX.local/share
   ```
4. Click **Connect**
5. Enter your NAS username and password
6. Check **"Remember this password in my keychain"** (important!)
7. Your NAS will mount at `/Volumes/share`

**Step 2: Configure the backup script**

```bash
# Copy Mac-specific templates
cp .env.mac.example .env
cp config.mac.example.json config.json

# Edit your .env file
nano .env
```

**In your .env file:**
```bash
# Your NAS is already mounted, so just point to it
NAS_MOUNT_POINT=/Volumes/share

# Your source paths on Mac
SOURCE_PATH_BOOKSTACK=/Users/yourname/Documents/projects/bookstack-wiki
SOURCE_PATH_DOCKER=/Users/yourname/docker

# NAS target paths (will be created automatically)
NAS_PATH_BOOKSTACK=/Volumes/share/backups/bookstack-wiki
NAS_PATH_DOCKER=/Volumes/share/backups/docker

# Email settings
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=465
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**In your config.json:**
```json
{
  "delete_on_nas": false,
  "email_enabled": true,
  "email": {
    "smtp_server": "${EMAIL_SMTP_SERVER}",
    "smtp_port": "${EMAIL_SMTP_PORT}",
    "use_ssl": true,
    "from": "${EMAIL_FROM}",
    "to": "${EMAIL_TO}",
    "username": "${EMAIL_USERNAME}",
    "password": "${EMAIL_PASSWORD}"
  },
  "jobs": [
    {
      "name": "Bookstack Wiki",
      "source_path": "${SOURCE_PATH_BOOKSTACK}",
      "nas_path": "${NAS_PATH_BOOKSTACK}",
      "state_file": ".backup_state_bookstack.json"
    },
    {
      "name": "Docker Configs",
      "source_path": "${SOURCE_PATH_DOCKER}",
      "nas_path": "${NAS_PATH_DOCKER}",
      "state_file": ".backup_state_docker.json"
    }
  ]
}
```

**Notice:** No `mount_command` needed! The script will use the already-mounted NAS.

**Step 3: Test the backup**

```bash
python3 backup_to_nas.py
```

The script will:
- ✅ Detect your NAS is already mounted
- ✅ Automatically create the `bookstack-wiki` folder on the NAS
- ✅ Copy your files to the NAS
- ✅ Send you an email notification

---

### Option 2: Automatic Mounting with mount_smbfs

If you want the script to automatically mount the NAS (without using Finder), use this method.

**Step 1: Configure with mount command**

**Your .env file:**
```bash
NAS_HOST=LS210XXXX.local
NAS_SHARE=share
NAS_MOUNT_POINT=/Volumes/BuffaloNAS

NAS_USERNAME=your_nas_username
NAS_PASSWORD=your_nas_password

SOURCE_PATH_BOOKSTACK=/Users/yourname/Documents/projects/bookstack-wiki

NAS_PATH_BOOKSTACK=${NAS_MOUNT_POINT}/backups/bookstack-wiki

# Email settings
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=465
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Your config.json:**
```json
{
  "mount_command": "mount_smbfs //${NAS_USERNAME}:${NAS_PASSWORD}@${NAS_HOST}/${NAS_SHARE} ${NAS_MOUNT_POINT}",
  "delete_on_nas": false,
  "email_enabled": true,
  "email": {
    "smtp_server": "${EMAIL_SMTP_SERVER}",
    "smtp_port": "${EMAIL_SMTP_PORT}",
    "use_ssl": true,
    "from": "${EMAIL_FROM}",
    "to": "${EMAIL_TO}",
    "username": "${EMAIL_USERNAME}",
    "password": "${EMAIL_PASSWORD}"
  },
  "jobs": [
    {
      "name": "Bookstack Wiki",
      "source_path": "${SOURCE_PATH_BOOKSTACK}",
      "nas_path": "${NAS_PATH_BOOKSTACK}",
      "state_file": ".backup_state_bookstack.json"
    }
  ]
}
```

**Security Note:** The script automatically secures your password - it's never visible in the process list!

---

## Setting Up Scheduled Backups on Mac

Mac uses `launchd` instead of `cron` for scheduled tasks.

**Step 1: Create a launchd plist file**

```bash
nano ~/Library/LaunchAgents/com.user.nasbackup.plist
```

**Add this content:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.nasbackup</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/automatic-backup/backup_to_nas.py</string>
        <string>/path/to/automatic-backup/config.json</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/path/to/automatic-backup/logs/backup.log</string>

    <key>StandardErrorPath</key>
    <string>/path/to/automatic-backup/logs/backup-error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**Important:** Replace `/path/to/automatic-backup/` with the actual path to your backup script directory!

**Step 2: Load the launchd job**

```bash
# Create logs directory
mkdir -p logs

# Load the job
launchctl load ~/Library/LaunchAgents/com.user.nasbackup.plist

# Verify it's loaded
launchctl list | grep nasbackup
```

**Step 3: Test it works**

```bash
# Trigger the job manually (don't wait for 4 AM)
launchctl start com.user.nasbackup

# Check the logs
tail -f logs/backup.log
```

**To unload/disable:**
```bash
launchctl unload ~/Library/LaunchAgents/com.user.nasbackup.plist
```

---

## Common Issues on Mac

### Issue 1: "NAS path is not accessible"

**Solution:** Mount the NAS via Finder first (Cmd+K, then `smb://LS210XXXX.local/share`)

### Issue 2: "Operation not permitted"

**Solution:** Grant Full Disk Access to Terminal/Python:

1. Open **System Preferences > Security & Privacy > Privacy**
2. Select **Full Disk Access**
3. Click the lock to make changes
4. Click **+** and add **Terminal** (or **Python** if running directly)

### Issue 3: "/Volumes/share not found"

**Cause:** Your NAS share name might be different

**Solution:** After mounting via Finder, check actual mount point:
```bash
ls /Volumes/
```

Use the actual folder name you see.

### Issue 4: Permission denied creating folders

**Solution:** Check NAS permissions - ensure your user can create folders on the share.

---

## Testing Your Setup

1. **Manual test:**
   ```bash
   python3 backup_to_nas.py
   ```

2. **Check what was created on NAS:**
   ```bash
   ls -la /Volumes/share/backups/
   ```

3. **View the backup report:**
   Check your email for the backup notification.

4. **Check logs:**
   ```bash
   cat logs/backup.log
   ```

---

## Folder Auto-Creation

**Important:** The script automatically creates folders on your NAS!

If you configure:
```bash
NAS_PATH_BOOKSTACK=/Volumes/share/backups/bookstack-wiki
```

The script will automatically create:
- `/Volumes/share/backups/` (if it doesn't exist)
- `/Volumes/share/backups/bookstack-wiki/` (if it doesn't exist)

Then copy your files into that folder.

**You don't need to create anything manually on the NAS first!**

---

## Path Examples for Mac

**Your Mac source paths:**
```bash
# Documents
/Users/yourname/Documents/projects/bookstack-wiki

# Desktop
/Users/yourname/Desktop/important-files

# Custom location
/Users/yourname/Development/docker-configs
```

**Your NAS paths (after mounting to /Volumes/share):**
```bash
# Root of share
/Volumes/share/backups/bookstack-wiki

# Organized by type
/Volumes/share/backups/projects/bookstack
/Volumes/share/backups/docker/configs
/Volumes/share/backups/documents/personal
```

---

## Recommended Setup for Mac

For the most reliable Mac experience:

1. ✅ **Mount NAS via Finder** and check "Remember password in keychain"
2. ✅ **Use pre-mounted path** `/Volumes/share` in your config
3. ✅ **Don't use `mount_command`** - let Finder handle mounting
4. ✅ **Use launchd** for scheduling, not cron
5. ✅ **Grant Full Disk Access** to Terminal/Python
6. ✅ **Test manually first** before setting up automation

This approach is:
- More reliable on Mac
- Easier to troubleshoot
- Works with macOS security features
- Uses Mac's native SMB implementation

---

## Need Help?

Check the main README.md for general troubleshooting, or open an issue if you're still stuck.
