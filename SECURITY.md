# Security Features and Best Practices

This document outlines the security measures implemented in the automatic NAS backup system and best practices for secure usage.

## Security Enhancements (Latest Version)

### ✅ Critical Vulnerabilities Fixed

#### 1. **Command Injection Prevention**
**Issue:** Previous versions used `subprocess.run(shell=True)` which allowed command injection through mount commands.

**Fix:**
- Now uses `shell=False` with `shlex.split()` to safely parse commands
- Mount commands are parsed as arrays, preventing injection attacks
- Example: `['mount', '-t', 'cifs', '//nas/share', '/mnt']` instead of shell string

**Impact:** Eliminates arbitrary command execution risk.

#### 2. **Password Exposure Prevention**
**Issue:** Mount commands with passwords were visible in process listings (`ps`, `top`).

**Fix:**
- Credentials are now written to temporary files with `0600` permissions
- Mount uses `credentials=file` option instead of command-line parameters
- Temporary credential files are always deleted after use
- Password never appears in process list

**Impact:** Prevents password leakage through process inspection.

### ✅ High-Severity Protections

#### 3. **Path Validation**
**Feature:** All source and NAS paths are validated against allowed prefixes.

**Default Allowed Paths:**
- Source: `/home`, `/mnt`, `/Documents`, `/Users`, `/opt`, `/var`, `/srv`
- NAS: `/mnt`, `/media`, `/Volumes`

**Customization:**
```json
{
  "allowed_source_prefixes": ["/home", "/Documents"],
  "allowed_nas_prefixes": ["/mnt/nas"]
}
```

**Impact:** Prevents backups from/to sensitive system directories like `/etc`, `/root`, etc.

#### 4. **Symlink Protection**
**Feature:** Symlinks are not followed during backup operations.

**Implementation:**
- `os.walk(followlinks=False)` prevents symlink directory traversal
- Symlinked files are detected and skipped
- All paths are resolved and validated to be within source directory

**Impact:** Prevents symlink attacks that could escape backup directory.

#### 5. **Automatic File Permission Enforcement**
**Feature:** Sensitive files automatically get `0600` (read/write owner only) permissions.

**Protected Files:**
- `.env` - Environment variables with credentials
- `config.json` - Configuration file
- `.backup_state*.json` - Backup state files

**Example:**
```
Security: Fixed permissions on .env (was 0644, now 0600)
```

**Impact:** Prevents unauthorized access to credentials and configuration.

#### 6. **Input Validation**
**Feature:** Configuration values are validated before use.

**Validations:**
- SMTP port must be 1-65535
- Required email fields are checked
- Paths must exist and be directories
- All paths are validated against allowed prefixes

**Impact:** Prevents malformed configurations from causing security issues.

## Security Best Practices

### 1. Use .env Files for Credentials
**Do:**
```bash
# .env
NAS_USERNAME=myuser
NAS_PASSWORD=securepassword123
```

```json
// config.json
{
  "mount_command": "mount ... -o username=${NAS_USERNAME},password=${NAS_PASSWORD}"
}
```

**Don't:**
```json
{
  "mount_command": "mount ... -o username=myuser,password=securepassword123"
}
```

### 2. Restrict File Permissions
The script automatically enforces `0600` permissions, but verify:

```bash
chmod 600 .env config.json
ls -la | grep -E '\.(env|json)'
```

Expected output:
```
-rw------- 1 user user  .env
-rw------- 1 user user  config.json
```

### 3. NAS Mounting Security

**Critical: Never expose passwords in mount commands!**

**✅ Secure Method (Automatic with this script):**
```bash
# .env
NAS_USERNAME=backup_user
NAS_PASSWORD=secure_password

# config.json uses variables
"mount_command": "mount -t cifs //${NAS_IP}/${NAS_SHARE} ${NAS_PATH} -o username=${NAS_USERNAME},password=${NAS_PASSWORD}"
```

**What happens:**
1. Script automatically detects credentials in mount command
2. Creates temporary credentials file: `/tmp/backup_XXXXX.cred` (0600 permissions)
3. Executes: `mount -t cifs //nas/share /mnt -o credentials=/tmp/backup_XXXXX.cred`
4. Deletes temporary file immediately

**Password NEVER appears in:**
- Process list (`ps aux`, `top`, `htop`)
- Shell history
- System logs
- Other user's view

**❌ Insecure Methods (NEVER DO THIS):**

**Manual mount with password on command line:**
```bash
# ❌ Password visible to all users with `ps aux`
mount -t cifs //nas/share /mnt -o username=user,password=secret123
```

**Hardcoded password in config:**
```json
{
  // ❌ Password in version control, visible in config file
  "mount_command": "mount ... -o username=user,password=secret123"
}
```

**Password in shell scripts:**
```bash
# ❌ Password in shell history and script file
#!/bin/bash
mount -t cifs //nas/share /mnt -o username=user,password=secret123
```

**🔐 Most Secure Alternative: Pre-mount via /etc/fstab**

If you have root access, the most secure approach is to mount at boot:

1. Create credentials file:
   ```bash
   sudo bash -c 'cat > /root/.nascreds << EOF
   username=backup_user
   password=secure_password
   EOF'
   sudo chmod 600 /root/.nascreds
   ```

2. Add to `/etc/fstab`:
   ```bash
   //192.168.1.100/backup /mnt/nas cifs credentials=/root/.nascreds,uid=1000,gid=1000,file_mode=0644,dir_mode=0755 0 0
   ```

3. Mount and verify:
   ```bash
   sudo mount -a
   df -h | grep nas
   ```

4. In your backup config, just reference the mount point:
   ```json
   {
     "nas_path": "/mnt/nas/backup"
     // No mount_command needed!
   }
   ```

**Benefits:**
- Password stored in root-only file
- Mounted at boot automatically
- No need for backup script to mount
- No credentials in process list ever

### 4. Use Dedicated NAS User Account
Create a dedicated user for backups with minimal permissions:
- Read-only access to backup share (or write-only if possible)
- No administrative privileges
- Separate from your main account
- Consider using different credentials per machine

### 5. Network Security
- **Local Network Only:** Ensure NAS is only accessible from trusted local network
- **Firewall:** Configure firewall to block external access to NAS
- **VPN:** Use VPN if accessing NAS remotely

### 5. Email Security
- **App Passwords:** Use app-specific passwords, not main account password
- **TLS/SSL:** Always use `use_ssl: true` or `use_tls: true`
- **Dedicated Email:** Consider using a dedicated email account for backup notifications

### 6. Restrict Backup Paths
Customize allowed paths to only what you need:

```json
{
  "allowed_source_prefixes": ["/home/user/projects", "/home/user/Documents"],
  "allowed_nas_prefixes": ["/mnt/nas/backup"]
}
```

### 7. Regular Security Audits
Periodically check:
- File permissions: `ls -la .env config.json`
- Running processes: `ps aux | grep backup_to_nas`
- Cron job security: `crontab -l`
- Email report contents for sensitive information

### 8. Backup Encryption (Optional)
For sensitive data, consider encrypting before backup:

```bash
# Example: Encrypt before backup
tar czf - /source | gpg --encrypt > encrypted_backup.tar.gz.gpg
```

Or use NAS-level encryption if available.

## Security Incident Response

### If Credentials Are Compromised

1. **Immediately change passwords:**
   ```bash
   # Update .env file
   nano .env

   # Change NAS user password
   # Change email app password
   ```

2. **Review backup logs for unauthorized access:**
   ```bash
   cat logs/backup.log | grep -E "(FAILED|Error)"
   ```

3. **Check cron job hasn't been modified:**
   ```bash
   crontab -l
   ```

4. **Verify file integrity:**
   ```bash
   # Check for unexpected modifications
   find /path/to/backup -type f -mtime -1
   ```

### If Malicious Files Are Detected

1. **Stop scheduled backups:**
   ```bash
   crontab -e
   # Comment out backup line
   ```

2. **Review backup state:**
   ```bash
   cat .backup_state.json | jq
   ```

3. **Quarantine affected files**
4. **Run virus/malware scan on both source and NAS**

## Security Audit Checklist

Use this checklist to verify your backup system security:

- [ ] `.env` file has `0600` permissions
- [ ] `config.json` has `0600` permissions
- [ ] No passwords in `config.json` (using environment variables)
- [ ] NAS user has minimal required permissions
- [ ] Email uses app-specific password, not main password
- [ ] Email uses SSL/TLS encryption
- [ ] Backup paths are restricted (not `/`, `/etc`, `/root`)
- [ ] Cron job runs as appropriate user (not root unless necessary)
- [ ] NAS is on local network only or behind VPN
- [ ] Regular backup logs are reviewed for errors
- [ ] No sensitive data in email notifications
- [ ] State files are protected with `0600` permissions

## Vulnerability Reporting

If you discover a security vulnerability in this backup system:

1. **Do not** open a public GitHub issue
2. Report privately to the repository maintainer
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if applicable)

## Security Update History

### v2.0 (2026-01-13) - Security Hardening Release
- ✅ Fixed command injection via shell=True
- ✅ Fixed password exposure in process list
- ✅ Added path validation against allowed prefixes
- ✅ Disabled symlink following
- ✅ Automatic file permission enforcement
- ✅ Input validation for configuration values

### v1.0 - Initial Release
- Basic .env support
- .gitignore protection
- Email encryption (TLS/SSL)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

## License

This security documentation is provided as-is. While we've implemented industry-standard security practices, no system is 100% secure. Use at your own risk and maintain appropriate security practices.
