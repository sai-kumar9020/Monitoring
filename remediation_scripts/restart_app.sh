#!/bin/bash

# Auto-remediation script for restarting Flask app in Docker environment
LOG_FILE="/var/log/alerts.log"
CONTAINER_NAME="flask-observability-app"

echo "$(date): High memory usage detected, restarting Flask app container" >> $LOG_FILE

# Check if container exists and is running
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    echo "$(date): Restarting container $CONTAINER_NAME" >> $LOG_FILE
    
    # Restart the container
    if docker restart $CONTAINER_NAME >> $LOG_FILE 2>&1; then
        echo "$(date): Container $CONTAINER_NAME restarted successfully" >> $LOG_FILE
        
        # Wait for container to be healthy
        sleep 10
        
        # Check if container is running
        if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
            echo "$(date): Container $CONTAINER_NAME is running and healthy" >> $LOG_FILE
        else
            echo "$(date): Warning: Container $CONTAINER_NAME may not be healthy after restart" >> $LOG_FILE
        fi
    else
        echo "$(date): Failed to restart container $CONTAINER_NAME" >> $LOG_FILE
    fi
else
    echo "$(date): Container $CONTAINER_NAME not found or not running" >> $LOG_FILE
fi