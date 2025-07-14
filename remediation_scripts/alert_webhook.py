#!/usr/bin/env python3

from flask import Flask, request, jsonify
import subprocess
import logging
import json
import os
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def handle_alert():
    """Handle incoming alerts from Alertmanager"""
    try:
        alert_data = request.get_json()
        
        for alert in alert_data.get('alerts', []):
            alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
            status = alert.get('status', 'unknown')
            
            # Log the alert
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'alert': alert_name,
                'status': status,
                'labels': alert.get('labels', {}),
                'annotations': alert.get('annotations', {})
            }
            
            # Ensure log directory exists
            os.makedirs('/var/log', exist_ok=True)
            
            with open('/var/log/alerts.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"Received alert: {alert_name} - {status}")
            
            # Execute remediation scripts based on alert type
            if status == 'firing':
                if alert_name == 'HighMemoryUsage':
                    logger.info("Executing memory remediation - restarting Flask app container")
                    try:
                        # Restart the Flask app container
                        subprocess.run([
                            'docker', 'restart', 'flask-observability-app'
                        ], check=True, capture_output=True, text=True)
                        logger.info("Flask app container restarted successfully")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to restart Flask app container: {e}")
                
                elif alert_name == 'HighDiskUsage':
                    logger.info("Executing disk cleanup script")
                    try:
                        subprocess.run([
                            'bash', '/app/remediation_scripts/cleanup_disk.sh'
                        ], check=True, capture_output=True, text=True)
                        logger.info("Disk cleanup completed successfully")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to execute disk cleanup: {e}")
                
                elif alert_name == 'AppDown':
                    logger.info("App is down - attempting to restart container")
                    try:
                        subprocess.run([
                            'docker', 'restart', 'flask-observability-app'
                        ], check=True, capture_output=True, text=True)
                        logger.info("Flask app container restarted due to app down alert")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to restart app container: {e}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check for the webhook service"""
    return jsonify({'status': 'healthy', 'service': 'alert-webhook'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)