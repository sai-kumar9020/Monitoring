# Flask Observability Setup Guide

This guide will walk you through setting up a complete observability stack for a Python Flask application.

## Prerequisites

- Linux VM (Ubuntu 20.04+ recommended)
- Python 3.8+
- Docker and Docker Compose
- Git

## Step 1: Setup Environment

### 1.1 Install Required System Packages

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git curl
```

### 1.2 Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.3 Create Project Directory

```bash
mkdir flask-observability
cd flask-observability
```

## Step 2: Setup Flask Application

### 2.1 Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.2 Install Python Dependencies

```bash
pip install flask prometheus_client psutil
```

### 2.3 Copy Application Files

Copy the following files to your project directory:
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies

### 2.4 Run Flask Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Step 3: Setup Monitoring Stack

### 3.1 Copy Configuration Files

Copy these files to your project directory:
- `docker-compose.yml` - Docker services configuration
- `prometheus.yml` - Prometheus configuration
- `alert_rules.yml` - Alerting rules
- `alertmanager.yml` - Alertmanager configuration
- `grafana-dashboard.json` - Grafana dashboard

### 3.2 Start Monitoring Stack

```bash
docker-compose up -d
```

This will start:
- Prometheus on port 9090
- Grafana on port 3000
- Alertmanager on port 9093
- Node Exporter on port 9100

### 3.3 Verify Services

```bash
# Check running containers
docker-compose ps

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Flask app metrics
curl http://localhost:5000/metrics
```

## Step 4: Configure Grafana

### 4.1 Access Grafana

1. Open http://localhost:3000 in your browser
2. Login with admin/admin
3. Change the default password when prompted

### 4.2 Add Prometheus Data Source

1. Go to Configuration → Data Sources
2. Click "Add data source"
3. Select Prometheus
4. Set URL to `http://prometheus:9090`
5. Click "Save & Test"

### 4.3 Import Dashboard

1. Go to Create → Import
2. Copy the content from `grafana-dashboard.json`
3. Paste it in the import dialog
4. Click "Load" then "Import"

## Step 5: Setup Auto-Remediation

### 5.1 Create Remediation Scripts Directory

```bash
mkdir remediation_scripts
chmod +x remediation_scripts/*.sh
```

### 5.2 Setup Alert Webhook Service

```bash
# Install webhook service
python remediation_scripts/alert_webhook.py &
```

### 5.3 Update Script Paths

Edit the remediation scripts and update the paths:
- `/path/to/your/flask/app` → Your actual Flask app path
- `/path/to/remediation_scripts` → Your actual scripts path

## Step 6: Testing the Setup

### 6.1 Test Basic Functionality

```bash
# Test health endpoint
curl http://localhost:5000/health

# Create test orders
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"product": "Test Product", "quantity": 5, "price": 29.99}'

# Get all orders
curl http://localhost:5000/api/orders
```

### 6.2 Test Error Scenarios

```bash
# Simulate server error
curl http://localhost:5000/api/simulate-error?type=server

# Simulate slow response
curl http://localhost:5000/api/simulate-slow?delay=2

# Simulate memory stress
curl http://localhost:5000/api/memory-stress?size=100
```

### 6.3 Verify Metrics

```bash
# Check Prometheus metrics
curl http://localhost:5000/metrics

# Check specific metric
curl http://localhost:9090/api/v1/query?query=flask_http_request_total
```

## Step 7: Configure Alerting

### 7.1 Test Alertmanager

```bash
# Check Alertmanager configuration
curl http://localhost:9093/api/v1/status

# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

### 7.2 Configure Email Notifications

Update `alertmanager.yml` with your SMTP settings:

```yaml
global:
  smtp_smarthost: 'your-smtp-server:587'
  smtp_from: 'alerts@yourcompany.com'
  smtp_auth_username: 'your-email@yourcompany.com'
  smtp_auth_password: 'your-app-password'
```

### 7.3 Configure Slack Notifications

1. Create a Slack webhook URL
2. Update `alertmanager.yml` with your Slack webhook URL
3. Restart Alertmanager: `docker-compose restart alertmanager`

## Step 8: Production Deployment

### 8.1 Systemd Service for Flask App

Create `/etc/systemd/system/flask-app.service`:

```ini
[Unit]
Description=Flask Observability App
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/flask-observability
Environment=PATH=/path/to/flask-observability/venv/bin
ExecStart=/path/to/flask-observability/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-app
sudo systemctl start flask-app
```

### 8.2 Nginx Reverse Proxy

Create `/etc/nginx/sites-available/flask-app`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 8.3 Monitoring Stack as Services

For production, run monitoring components as systemd services instead of Docker containers for better resource management.

## Troubleshooting

### Common Issues

1. **Flask app not accessible**: Check if the app is running on all interfaces (0.0.0.0)
2. **Prometheus can't scrape metrics**: Verify the Flask app is exposing metrics on `/metrics`
3. **Alerts not firing**: Check Prometheus rules and Alertmanager configuration
4. **Grafana not showing data**: Verify Prometheus data source configuration

### Useful Commands

```bash
# Check Flask app logs
journalctl -u flask-app -f

# Check Docker logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f alertmanager

# Check system resources
htop
df -h
free -h
```

## Key Metrics to Monitor

### Application Metrics
- `flask_http_request_total` - Total HTTP requests
- `flask_http_request_duration_seconds` - Request duration
- `flask_http_errors_total` - Total HTTP errors
- `flask_orders_total` - Total orders created
- `flask_active_connections` - Active connections

### System Metrics
- `system_cpu_usage_percent` - CPU usage
- `system_memory_usage_percent` - Memory usage
- `system_disk_usage_percent` - Disk usage

### Prometheus Queries
- Request rate: `rate(flask_http_request_total[1m])`
- Error rate: `rate(flask_http_errors_total[1m]) / rate(flask_http_request_total[1m])`
- Average latency: `rate(flask_http_request_duration_seconds_sum[1m]) / rate(flask_http_request_duration_seconds_count[1m])`
- 95th percentile latency: `histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[1m]))`

## Next Steps

1. Set up log aggregation with ELK stack
2. Implement distributed tracing with Jaeger
3. Add custom business metrics
4. Set up automated testing of alerting rules
5. Implement more sophisticated auto-remediation workflows