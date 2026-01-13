# Automatic NAS Backup Script

A Python-based automated backup solution that monitors a local directory for changes and syncs files to a Buffalo NAS device. Features intelligent change detection, email notifications, and scheduled execution via cron.

## Features

- 🔍 **Smart Change Detection**: Only backs up files that are new or modified (using MD5 hashing)
- 📧 **Email Notifications**: Sends detailed reports of each backup operation with timestamps
- ⏰ **Scheduled Execution**: Runs automatically at 4 AM daily via cron
- 🚀 **Efficient**: Skips backup if no changes are detected
- 📊 **Detailed Logging**: Tracks all operations with file sizes and statuses
- 🔒 **Safe**: Preserves file metadata and handles errors gracefully
- 💾 **State Tracking**: Maintains backup state to detect changes between runs
- 🛡️ **Security Hardened**: Protection against command injection, path traversal, symlink attacks, and password exposure
- 🔐 **Auto-Permissions**: Automatically enforces secure file permissions on sensitive files

## Requirements

- Python 3.6 or higher
- Access to a Buffalo NAS device (or any network storage)
- SMTP server access for email notifications (e.g., Gmail)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd automatic-backup
```

### 2. Configure

**Option A: Multi-Job Backup (Recommended for multiple directories)**

If you need to backup multiple directories (e.g., Docker configs, documents, photos):

```bash
cp .env.multi-job.example .env
cp config.multi-job.example.json config.json
nano .env
```

This sets up multiple backup jobs in one configuration. See the "Multiple Backup Jobs" section for details.

**Option B: Single Directory with .env (Recommended for security)**

For backing up a single directory:

```bash
cp .env.example .env
cp config.example.json config.json
nano .env
```

The `.env` file keeps your passwords and credentials separate from the config. Set your sensitive values in `.env` and the config will automatically use them.

**Option C: Direct configuration**

Copy and edit the config file directly:

```bash
cp config.example.json config.json
nano config.json
```

Then replace `${VARIABLE}` placeholders with your actual values.

### 3. Install Cron Job

Run the setup script to install the cron job:

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

This will:
- Make the backup script executable
- Create a logs directory
- Install a cron job for 4 AM daily execution
- Run a test backup to verify configuration

## Configuration

Edit `config.json` with your specific settings:

```json
{
  "source_path": "/path/to/your/docker/files",
  "nas_path": "/mnt/nas/backup",
  "state_file": ".backup_state.json",
  "delete_on_nas": false,
  "mount_command": "mount -t cifs //192.168.1.100/backup /mnt/nas -o username=user,password=pass",
  "email_enabled": true,
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "use_ssl": true,
    "from": "your_email@gmail.com",
    "to": "your_email@gmail.com",
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

### Configuration Options

| Option | Description | Required |
|--------|-------------|----------|
| `source_path` | Local directory to backup | Yes |
| `nas_path` | Destination path on NAS | Yes |
| `state_file` | File to store backup state | No (default: `.backup_state.json`) |
| `delete_on_nas` | Delete files on NAS if deleted from source | No (default: `false`) |
| `mount_command` | Command to mount NAS if not mounted | No |
| `email_enabled` | Enable/disable email notifications | No (default: `false`) |
| `email.*` | Email configuration settings | Required if `email_enabled` is `true` |

### Using Environment Variables (Recommended)

Instead of hardcoding sensitive credentials in `config.json`, use environment variables with a `.env` file:

**1. Create your .env file:**

```bash
cp .env.example .env
chmod 600 .env  # Restrict permissions
nano .env
```

**2. Set your credentials in .env:**

```bash
# .env
SOURCE_PATH=/Documents/projects/bookstack-wiki
NAS_PATH=/mnt/nas/backup
NAS_USERNAME=your_username
NAS_PASSWORD=your_secure_password
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**3. Reference them in config.json:**

The config file uses `${VARIABLE}` syntax to reference environment variables:

```json
{
  "source_path": "${SOURCE_PATH}",
  "nas_path": "${NAS_PATH}",
  "mount_command": "mount -t cifs //${NAS_IP}/${NAS_SHARE} ${NAS_PATH} -o username=${NAS_USERNAME},password=${NAS_PASSWORD}",
  "email": {
    "username": "${EMAIL_USERNAME}",
    "password": "${EMAIL_PASSWORD}"
  }
}
```

**Benefits:**
- ✅ Credentials never committed to version control
- ✅ Easy to manage multiple environments
- ✅ More secure than hardcoded passwords
- ✅ `.env` is automatically excluded by `.gitignore`

**Alternative:** You can also set environment variables in your shell or use system environment variables. The script will automatically expand them.

### Multiple Backup Jobs (Recommended for Multiple Directories)

The script supports backing up multiple source directories in a single run, making it perfect for backing up different projects or categories of files.

**Benefits of Multi-Job Configuration:**
- ✅ Single cron job backs up everything
- ✅ Consolidated email report for all backups
- ✅ Each job tracks changes independently
- ✅ Different source/destination paths per job
- ✅ Named jobs for easy identification

**Setup Multi-Job Backups:**

1. **Use the multi-job configuration template:**

```bash
cp config.multi-job.example.json config.json
cp .env.multi-job.example .env
nano .env
```

2. **Configure your .env with all source paths:**

```bash
# .env
SOURCE_PATH_BOOKSTACK=/Documents/projects/bookstack-wiki
SOURCE_PATH_DOCKER=/home/user/docker
SOURCE_PATH_DOCUMENTS=/home/user/Documents
SOURCE_PATH_PHOTOS=/home/user/Pictures
NAS_PATH=/mnt/nas/backup
```

3. **Your config.json uses the jobs array:**

```json
{
  "email_enabled": true,
  "email": { ... },
  "jobs": [
    {
      "name": "Bookstack Wiki",
      "source_path": "${SOURCE_PATH_BOOKSTACK}",
      "nas_path": "${NAS_PATH}/bookstack",
      "state_file": ".backup_state_bookstack.json"
    },
    {
      "name": "Docker Configs",
      "source_path": "${SOURCE_PATH_DOCKER}",
      "nas_path": "${NAS_PATH}/docker",
      "state_file": ".backup_state_docker.json"
    },
    {
      "name": "Personal Documents",
      "source_path": "${SOURCE_PATH_DOCUMENTS}",
      "nas_path": "${NAS_PATH}/documents",
      "state_file": ".backup_state_documents.json"
    }
  ]
}
```

**How It Works:**
- Each job runs sequentially during the backup
- Each job has its own state file to track changes independently
- You get one consolidated email showing all job results
- Global settings (email, mount_command) are shared across all jobs
- Job-specific settings override global settings

**Example Multi-Job Email Report:**

```
Automatic Backup Report - Multiple Jobs
========================================
Timestamp: 2026-01-12 04:00:15

Overall Summary:
----------------
Total jobs: 4
Successful: 4
Failed: 0
Total files changed: 23

============================================================
Job Details:
============================================================

Job: Bookstack Wiki
Source: /Documents/projects/bookstack-wiki
Destination: /mnt/nas/backup/bookstack
Status: SUCCESS

Summary:
--------
New files: 3
Modified files: 2
Total changes: 5

------------------------------------------------------------

Job: Docker Configs
Source: /home/user/docker
Destination: /mnt/nas/backup/docker
Status: SUCCESS

Summary:
--------
New files: 0
Modified files: 1
Total changes: 1

------------------------------------------------------------
```

**Adding New Backup Jobs:**

Simply add a new entry to the `jobs` array in your config.json:

```json
{
  "jobs": [
    ...existing jobs...,
    {
      "name": "New Project",
      "source_path": "${SOURCE_PATH_NEW_PROJECT}",
      "nas_path": "${NAS_PATH}/new-project",
      "state_file": ".backup_state_new_project.json"
    }
  ]
}
```

And add the source path to your .env:

```bash
SOURCE_PATH_NEW_PROJECT=/path/to/new/project
```

**Backward Compatibility:**

The single-job configuration format is still fully supported. If your config doesn't have a `jobs` array, it will work exactly as before.

### NAS Target Folder Organization

**Automatic Directory Creation:**

The script automatically creates NAS target directories if they don't exist - you don't need to manually create them! The script uses `mkdir -p` functionality to create all parent directories.

**Organizing Your Backups:**

You have complete flexibility in how you structure your NAS backups using environment variables:

**Option 1: Shared Base Path (Recommended)**

```bash
# .env
NAS_PATH=/mnt/nas/backup

SOURCE_PATH_BOOKSTACK=/Documents/projects/bookstack-wiki
SOURCE_PATH_DOCKER=/home/user/docker
```

```json
// config.json
{
  "jobs": [
    {
      "name": "Bookstack Wiki",
      "source_path": "${SOURCE_PATH_BOOKSTACK}",
      "nas_path": "${NAS_PATH}/bookstack-wiki"
    },
    {
      "name": "Docker",
      "source_path": "${SOURCE_PATH_DOCKER}",
      "nas_path": "${NAS_PATH}/docker"
    }
  ]
}
```

Creates: `/mnt/nas/backup/bookstack-wiki/` and `/mnt/nas/backup/docker/`

**Option 2: Organized by Hostname (Multi-Server)**

```bash
# .env
NAS_BASE=/mnt/nas/backup
HOSTNAME=myserver
NAS_PATH=${NAS_BASE}/${HOSTNAME}
```

Creates: `/mnt/nas/backup/myserver/bookstack-wiki/`

**Option 3: Category-Based Organization**

```bash
# .env
NAS_BASE=/mnt/nas/backup
NAS_PATH_PROJECTS=${NAS_BASE}/projects
NAS_PATH_SYSTEM=${NAS_BASE}/system
```

```json
{
  "jobs": [
    {
      "name": "Bookstack",
      "source_path": "/Documents/projects/bookstack-wiki",
      "nas_path": "${NAS_PATH_PROJECTS}/bookstack"
    },
    {
      "name": "Docker",
      "source_path": "/home/user/docker",
      "nas_path": "${NAS_PATH_SYSTEM}/docker"
    }
  ]
}
```

Creates organized structure:
```
/mnt/nas/backup/
├── projects/
│   └── bookstack/
└── system/
    └── docker/
```

**Quick Start Templates:**

For a complete Bookstack-focused setup:
```bash
cp .env.bookstack.example .env
cp config.bookstack.example.json config.json
nano .env
```

### Email Setup (Gmail Example)

For Gmail, you need to use an App Password:

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this password in the `config.json` file

### NAS Mount Options

The script can automatically mount your NAS if needed. Configure the `mount_command` based on your NAS type:

**Buffalo NAS (SMB/CIFS):**
```bash
mount -t cifs //192.168.1.100/backup /mnt/nas -o username=your_username,password=your_password
```

**NFS Mount:**
```bash
mount -t nfs 192.168.1.100:/backup /mnt/nas
```

**Pre-mounted NAS:**
If your NAS is already mounted at boot, simply set `nas_path` to the mount point and omit `mount_command`.

## Usage

### Manual Backup

Run a backup manually for testing:

```bash
./run_backup.sh
```

Or run the Python script directly:

```bash
python3 backup_to_nas.py config.json
```

### Automatic Backups

After running `setup_cron.sh`, backups will run automatically at 4 AM daily.

### View Logs

Check backup logs:

```bash
cat logs/backup.log
```

View recent logs:

```bash
tail -f logs/backup.log
```

### Manage Cron Job

View installed cron jobs:

```bash
crontab -l
```

Edit cron jobs:

```bash
crontab -e
```

Remove the backup cron job:

```bash
crontab -e
# Delete the line containing backup_to_nas.py
```

## How It Works

1. **State Tracking**: The script maintains a `.backup_state.json` file with MD5 hashes of all backed up files
2. **Change Detection**: On each run, it scans the source directory and compares file hashes with the previous state
3. **Selective Sync**: Only new or modified files are copied to the NAS
4. **Email Report**: After each run, an email is sent with details of what was backed up
5. **Timestamp**: All operations are timestamped for audit purposes

### Email Notifications

You'll receive an email after each backup run with:

- Timestamp of the backup
- Number of new, modified, and deleted files
- Detailed list of all changes
- Success/failure status
- File sizes for transferred files

**Example Email:**

```
Automatic Backup Report
=======================
Timestamp: 2026-01-12 04:00:15
Source: /home/user/docker
Destination: /mnt/nas/backup

Status: SUCCESS

Summary:
--------
New files: 2
Modified files: 1
Deleted files: 0
Unchanged files: 47
Total changes: 3

Details:
--------
NEW: docker-compose.yml (2.45 KB)
NEW: nginx/nginx.conf (1.23 KB)
MODIFIED: app/config.json (856 B)
```

## Troubleshooting

### NAS Not Accessible

If the NAS path is not accessible:
- Verify the NAS is powered on and connected to the network
- Check if the mount command is correct
- Try mounting manually: `sudo mount -t cifs //nas-ip/share /mnt/nas -o username=user,password=pass`
- Check firewall settings

### Email Not Sending

If emails are not being sent:
- Verify SMTP server and port are correct
- For Gmail, ensure you're using an App Password, not your regular password
- Check if "Less secure app access" is enabled (if not using App Password)
- Verify your email credentials
- Check spam folder

### Permission Errors

If you get permission errors:
- Ensure the backup script is executable: `chmod +x backup_to_nas.py`
- Verify you have read access to the source directory
- Verify you have write access to the NAS path
- Check NAS share permissions

### Cron Job Not Running

If the cron job doesn't run:
- Verify the cron job is installed: `crontab -l`
- Check cron logs: `grep CRON /var/log/syslog` (Ubuntu/Debian) or `journalctl -u cron`
- Ensure the script paths in cron are absolute paths
- Check that the user running cron has necessary permissions

## Advanced Usage

### Custom Schedule

To change the backup schedule, edit the cron job:

```bash
crontab -e
```

Cron schedule format: `minute hour day month weekday command`

Examples:
- Every 6 hours: `0 */6 * * *`
- Twice daily (6 AM and 6 PM): `0 6,18 * * *`
- Every Monday at 3 AM: `0 3 * * 1`

### Multiple Backup Configurations

**Recommended Approach: Use Multi-Job Configuration**

The preferred way to backup multiple directories is using the `jobs` array in a single config file (see "Multiple Backup Jobs" section above). This provides:
- One cron job for all backups
- Consolidated email reports
- Easier management

**Alternative: Multiple Config Files**

You can also create separate configuration files and run them independently:

```bash
python3 backup_to_nas.py config_docker.json
python3 backup_to_nas.py config_documents.json
```

This approach requires multiple cron jobs and generates separate emails for each backup.

### Backup State Reset

To force a full backup (re-sync all files), delete the state file:

```bash
rm .backup_state.json
```

## Security Considerations

**🛡️ Security Hardened Version 2.0**

This backup system includes comprehensive security protections. For complete security documentation, see [SECURITY.md](SECURITY.md).

### Built-in Security Features

- ✅ **Command Injection Prevention**: No `shell=True` - uses safe command parsing
- ✅ **Password Protection**: Credentials never appear in process list (uses temporary credential files)
- ✅ **Path Validation**: Restricts backup sources/destinations to allowed directories
- ✅ **Symlink Protection**: Prevents symlink attacks and directory traversal
- ✅ **Auto-Permission Enforcement**: Automatically sets `0600` on `.env`, `config.json`, and state files
- ✅ **Input Validation**: Validates all configuration values before use

### Quick Security Setup

1. **Use .env Files** (automatically secured to `0600`):
   ```bash
   cp .env.example .env
   # Permissions auto-fixed to 0600 on first run
   ```

2. **Verify Permissions**:
   ```bash
   ls -la | grep -E '\.(env|json)'
   # Should show: -rw------- (0600)
   ```

3. **Configure Allowed Paths** (optional):
   ```json
   {
     "allowed_source_prefixes": ["/home/user", "/Documents"],
     "allowed_nas_prefixes": ["/mnt/nas"]
   }
   ```

### Security Best Practices

- **Use .env Files**: Store credentials in `.env` (auto-protected, never committed)
- **App Passwords**: Use app-specific passwords instead of main account passwords
- **Dedicated NAS User**: Create a backup-only user with minimal permissions
- **Network Security**: Ensure NAS is only accessible from trusted networks
- **Regular Audits**: Review logs and check file permissions periodically
- **Git Safety**: The `.gitignore` file prevents `.env` and `config.json` from being committed

### What's Protected

The script automatically detects and blocks:
- Command injection attempts
- Path traversal attacks (e.g., `../../etc/passwd`)
- Symlink escapes from backup directory
- Insecure file permissions
- Invalid configuration values

**📖 Read [SECURITY.md](SECURITY.md) for complete security documentation, incident response procedures, and security audit checklist.**

## File Structure

```
automatic-backup/
├── backup_to_nas.py                # Main backup script (security hardened)
├── config.json                     # Your configuration (create from example)
├── config.example.json             # Single-job example with ${VAR} placeholders
├── config.multi-job.example.json   # Multi-job example (recommended)
├── config.bookstack.example.json   # Bookstack-focused multi-job template
├── .env                            # Your credentials (create from .env.example)
├── .env.example                    # Single-job environment variables
├── .env.multi-job.example          # Multi-job environment variables
├── .env.bookstack.example          # Bookstack-focused environment variables
├── setup_cron.sh                   # Cron installation script
├── run_backup.sh                   # Manual backup runner
├── .gitignore                      # Protects sensitive files
├── .backup_state*.json             # Backup state files (auto-generated, one per job)
├── logs/                           # Backup logs directory
│   └── backup.log
├── README.md                       # This file
└── SECURITY.md                     # Security documentation and best practices
```

## License

This project is provided as-is for personal use.

## Support

For issues or questions, please open an issue on the repository.
