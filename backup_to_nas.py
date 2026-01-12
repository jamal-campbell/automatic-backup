#!/usr/bin/env python3
"""
Automatic Backup Script for Buffalo NAS
Monitors source directory for changes and syncs to NAS
Sends email notifications with operation details
"""

import os
import sys
import json
import hashlib
import smtplib
import shutil
import re
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

class BackupManager:
    def __init__(self, config_path='config.json', env_file='.env'):
        """Initialize backup manager with configuration"""
        self.config_path = config_path
        self.env_file = env_file
        self.load_env_file()
        self.config = self.load_config()
        self.state_file = Path(self.config.get('state_file', '.backup_state.json'))
        self.backup_log = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.current_job_config = {}  # Track current job for reporting

    def load_env_file(self):
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)

        if not env_path.exists():
            # .env file is optional
            return

        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Set environment variable
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Error loading .env file: {e}")

    def expand_env_vars(self, value):
        """Expand environment variables in a string value"""
        if not isinstance(value, str):
            return value

        # Support both ${VAR} and $VAR syntax
        def replacer(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))

        # Replace ${VAR} and $VAR
        pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        return re.sub(pattern, replacer, value)

    def expand_config_vars(self, obj):
        """Recursively expand environment variables in config"""
        if isinstance(obj, dict):
            return {key: self.expand_config_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.expand_config_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self.expand_env_vars(obj)
        else:
            return obj

    def load_config(self):
        """Load configuration from JSON file and expand environment variables"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Expand environment variables in all config values
            config = self.expand_config_vars(config)

            return config
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_path}' not found!")
            print("Please create a config.json file. See config.example.json for reference.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def load_state(self):
        """Load previous backup state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_state(self, state):
        """Save current backup state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.log(f"Error hashing {filepath}: {e}")
            return None

    def scan_directory(self, directory):
        """Scan directory and create file inventory with hashes"""
        inventory = {}
        dir_path = Path(directory)

        if not dir_path.exists():
            self.log(f"Error: Source directory '{directory}' does not exist!")
            return inventory

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = Path(root) / file
                relative_path = filepath.relative_to(dir_path)

                try:
                    stat = filepath.stat()
                    inventory[str(relative_path)] = {
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'hash': self.get_file_hash(filepath)
                    }
                except Exception as e:
                    self.log(f"Error scanning {filepath}: {e}")

        return inventory

    def detect_changes(self, current_inventory, previous_inventory):
        """Detect new, modified, and deleted files"""
        changes = {
            'new': [],
            'modified': [],
            'deleted': [],
            'unchanged': []
        }

        # Check for new and modified files
        for file, info in current_inventory.items():
            if file not in previous_inventory:
                changes['new'].append(file)
            elif info['hash'] != previous_inventory[file].get('hash'):
                changes['modified'].append(file)
            else:
                changes['unchanged'].append(file)

        # Check for deleted files
        for file in previous_inventory:
            if file not in current_inventory:
                changes['deleted'].append(file)

        return changes

    def mount_nas(self):
        """Mount NAS if not already mounted (optional)"""
        nas_path = Path(self.config['nas_path'])

        # Check if NAS path is accessible
        if not nas_path.exists():
            self.log(f"Warning: NAS path '{nas_path}' is not accessible!")

            # If mount command is provided in config, try to mount
            if 'mount_command' in self.config:
                self.log("Attempting to mount NAS...")
                try:
                    subprocess.run(self.config['mount_command'], shell=True, check=True)
                    self.log("NAS mounted successfully")
                except subprocess.CalledProcessError as e:
                    self.log(f"Error mounting NAS: {e}")
                    return False
            else:
                return False

        return True

    def sync_to_nas(self, changes):
        """Sync changed files to NAS"""
        source_path = Path(self.config['source_path'])
        nas_path = Path(self.config['nas_path'])

        if not self.mount_nas():
            self.log("Error: Cannot access NAS. Backup aborted.")
            return False

        # Create NAS backup directory if it doesn't exist
        try:
            nas_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log(f"Error creating NAS directory: {e}")
            return False

        success = True

        # Copy new and modified files
        for file in changes['new'] + changes['modified']:
            src = source_path / file
            dst = nas_path / file

            try:
                # Create parent directories if needed
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(src, dst)
                file_size = src.stat().st_size
                status = "NEW" if file in changes['new'] else "MODIFIED"
                self.log(f"{status}: {file} ({self.format_size(file_size)})")
            except Exception as e:
                self.log(f"Error copying {file}: {e}")
                success = False

        # Handle deleted files (optional)
        if self.config.get('delete_on_nas', False):
            for file in changes['deleted']:
                dst = nas_path / file
                try:
                    if dst.exists():
                        dst.unlink()
                        self.log(f"DELETED: {file}")
                except Exception as e:
                    self.log(f"Error deleting {file}: {e}")

        return success

    def format_size(self, bytes_size):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def send_email(self, subject, body):
        """Send email notification"""
        if not self.config.get('email_enabled', False):
            return

        try:
            email_config = self.config['email']

            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            if email_config.get('use_ssl', True):
                server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'])
            else:
                server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
                if email_config.get('use_tls', False):
                    server.starttls()

            # Login if credentials provided
            if 'username' in email_config and 'password' in email_config:
                server.login(email_config['username'], email_config['password'])

            # Send email
            server.send_message(msg)
            server.quit()

            self.log("Email notification sent successfully")
        except Exception as e:
            self.log(f"Error sending email: {e}")

    def log(self, message):
        """Add message to backup log"""
        self.backup_log.append(message)
        print(message)

    def create_report(self, changes, success, job_name=None):
        """Create backup report for a single job"""
        total_changes = len(changes['new']) + len(changes['modified']) + len(changes['deleted'])

        # Get source/dest from job_config if available, otherwise from main config
        source = self.current_job_config.get('source_path', self.config.get('source_path', 'N/A'))
        dest = self.current_job_config.get('nas_path', self.config.get('nas_path', 'N/A'))

        job_header = f"Job: {job_name}\n" if job_name else ""

        report = f"""
{job_header}Source: {source}
Destination: {dest}
Status: {'SUCCESS' if success else 'FAILED'}

Summary:
--------
New files: {len(changes['new'])}
Modified files: {len(changes['modified'])}
Deleted files: {len(changes['deleted'])}
Unchanged files: {len(changes['unchanged'])}
Total changes: {total_changes}

"""

        if total_changes > 0:
            report += "Details:\n--------\n"
            report += "\n".join(self.backup_log)
        else:
            report += "No changes detected. Backup not performed.\n"

        return report

    def create_consolidated_report(self, job_results):
        """Create consolidated report for multiple jobs"""
        total_jobs = len(job_results)
        successful_jobs = sum(1 for r in job_results if r['success'])
        failed_jobs = total_jobs - successful_jobs
        total_files_changed = sum(r['changes_count'] for r in job_results)

        report = f"""
Automatic Backup Report - Multiple Jobs
========================================
Timestamp: {self.timestamp}

Overall Summary:
----------------
Total jobs: {total_jobs}
Successful: {successful_jobs}
Failed: {failed_jobs}
Total files changed: {total_files_changed}

"""

        # Add details for each job
        report += "=" * 60 + "\n"
        report += "Job Details:\n"
        report += "=" * 60 + "\n\n"

        for result in job_results:
            report += result['report']
            report += "\n" + "-" * 60 + "\n"

        return report

    def run_single_job(self, job_config, job_name=None):
        """Run a single backup job"""
        # Store current job config for reporting
        self.current_job_config = job_config

        # Reset backup log for this job
        self.backup_log = []

        job_label = f" [{job_name}]" if job_name else ""
        self.log(f"Starting backup job{job_label}")
        self.log(f"Source: {job_config['source_path']}")
        self.log(f"Destination: {job_config['nas_path']}")

        # Use job-specific state file if provided, otherwise use default
        original_state_file = self.state_file
        if 'state_file' in job_config:
            self.state_file = Path(job_config['state_file'])

        # Load previous state
        previous_state = self.load_state()
        previous_inventory = previous_state.get('inventory', {})

        # Scan current directory
        self.log("Scanning source directory...")
        current_inventory = self.scan_directory(job_config['source_path'])

        if not current_inventory:
            self.log("Error: No files found or unable to scan source directory")
            changes = {'new': [], 'modified': [], 'deleted': [], 'unchanged': []}
            self.state_file = original_state_file
            return {
                'success': False,
                'changes': changes,
                'changes_count': 0,
                'report': self.create_report(changes, False, job_name),
                'job_name': job_name or 'default'
            }

        # Detect changes
        self.log("Detecting changes...")
        changes = self.detect_changes(current_inventory, previous_inventory)

        total_changes = len(changes['new']) + len(changes['modified']) + len(changes['deleted'])
        self.log(f"Found {total_changes} changes")

        success = True

        if total_changes > 0:
            # Perform backup - temporarily update config for sync_to_nas
            original_config_source = self.config.get('source_path')
            original_config_nas = self.config.get('nas_path')
            self.config['source_path'] = job_config['source_path']
            self.config['nas_path'] = job_config['nas_path']

            self.log("Syncing to NAS...")
            success = self.sync_to_nas(changes)

            # Restore original config
            if original_config_source:
                self.config['source_path'] = original_config_source
            if original_config_nas:
                self.config['nas_path'] = original_config_nas

            if success:
                # Update state
                new_state = {
                    'last_backup': self.timestamp,
                    'inventory': current_inventory
                }
                self.save_state(new_state)
                self.log("Backup completed successfully")
            else:
                self.log("Backup completed with errors")
        else:
            self.log("No changes detected. Skipping backup.")

        # Restore original state file
        self.state_file = original_state_file

        return {
            'success': success and total_changes >= 0,
            'changes': changes,
            'changes_count': total_changes,
            'report': self.create_report(changes, success, job_name),
            'job_name': job_name or 'default'
        }

    def run(self):
        """Main backup execution - supports both single and multiple jobs"""
        self.log(f"Starting backup process at {self.timestamp}")

        # Check if config has multiple jobs or single job
        if 'jobs' in self.config:
            # Multiple jobs mode
            self.log(f"Running {len(self.config['jobs'])} backup jobs...")
            job_results = []

            for job in self.config['jobs']:
                job_name = job.get('name', f"Job {len(job_results) + 1}")

                # Merge global config with job config (job config takes precedence)
                job_config = {
                    'source_path': job['source_path'],
                    'nas_path': job['nas_path'],
                    'state_file': job.get('state_file', f".backup_state_{job_name.replace(' ', '_').lower()}.json"),
                    'delete_on_nas': job.get('delete_on_nas', self.config.get('delete_on_nas', False)),
                    'mount_command': job.get('mount_command', self.config.get('mount_command'))
                }

                result = self.run_single_job(job_config, job_name)
                job_results.append(result)

                print()  # Add spacing between jobs

            # Create consolidated report
            all_successful = all(r['success'] for r in job_results)
            total_changes = sum(r['changes_count'] for r in job_results)

            if all_successful:
                if total_changes > 0:
                    subject = f"Backup SUCCESS - {total_changes} files across {len(job_results)} jobs - {self.timestamp}"
                else:
                    subject = f"Backup SKIPPED - No changes in {len(job_results)} jobs - {self.timestamp}"
            else:
                subject = f"Backup PARTIAL - {sum(1 for r in job_results if not r['success'])} failed - {self.timestamp}"

            report = self.create_consolidated_report(job_results)
            self.send_email(subject, report)

            return all_successful

        else:
            # Single job mode (backward compatibility)
            job_config = {
                'source_path': self.config['source_path'],
                'nas_path': self.config['nas_path'],
                'state_file': self.config.get('state_file', '.backup_state.json'),
                'delete_on_nas': self.config.get('delete_on_nas', False),
                'mount_command': self.config.get('mount_command')
            }

            result = self.run_single_job(job_config)

            # Send email with single job report
            total_changes = result['changes_count']
            if result['success']:
                if total_changes > 0:
                    subject = f"Backup SUCCESS - {total_changes} files updated - {self.timestamp}"
                else:
                    subject = f"Backup SKIPPED - No changes - {self.timestamp}"
            else:
                subject = f"Backup FAILED - {self.timestamp}"

            self.send_email(subject, result['report'])

            return result['success']


def main():
    """Main entry point"""
    # Check for config file argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'

    # Run backup
    backup = BackupManager(config_file)
    success = backup.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
