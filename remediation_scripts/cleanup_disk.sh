#!/bin/bash

# Auto-remediation script for cleaning up disk space in Docker environment
LOG_FILE="/var/log/alerts.log"

echo "$(date): High disk usage detected, cleaning up temporary files" >> $LOG_FILE

# Clean up /tmp directory (files older than 7 days)
find /tmp -type f -mtime +7 -exec rm -f {} \; 2>/dev/null || true

# Clean up log files older than 30 days
find /var/log -name "*.log" -type f -mtime +30 -exec rm -f {} \; 2>/dev/null || true

# Clean up Python cache files
find /app -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
find /app -name "*.pyc" -type f -exec rm -f {} \; 2>/dev/null || true

# Clean up pip cache if available
if command -v pip &> /dev/null; then
    pip cache purge 2>/dev/null || true
fi

# Rotate large log files
if [ -f "/var/log/alerts.log" ] && [ $(stat -c%s "/var/log/alerts.log") -gt 10485760 ]; then
    mv /var/log/alerts.log /var/log/alerts.log.old
    touch /var/log/alerts.log
fi

echo "$(date): Disk cleanup completed" >> $LOG_FILE

# Check current disk usage
df -h / >> $LOG_FILE 2>/dev/null || true