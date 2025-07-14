# Complete Docker Setup Guide for Flask Observability Stack

This guide provides step-by-step instructions to deploy a complete observability stack using Docker containers.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Linux/macOS/Windows with Docker Desktop

## Quick Start

### 1. Clone or Download Files

Ensure you have all the following files in your project directory:
```
flask-observability/
├── Dockerfile
├── Dockerfile.webhook
├── docker-compose.yml
├── app.py
├── requirements.txt
├── prometheus.yml
├── alert_rules.yml
├── alertmanager.yml
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml
│   │   └── dashboards/
│   │       └── dashboard.yml
│   └── dashboards/
│       └── flask-observability.json
├── remediation_scripts/
│   ├── alert_webhook.py
│   ├── cleanup_disk.sh
│   └── restart_app.sh
└── logs/
```

### 2. Create Required Directories

```bash
mkdir -p logs
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/dashboards
chmod +x remediation_scripts/*.sh
```

### 3. Start the Complete Stack

```bash
# Build and start all services
docker-compose up -d

# Check if all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

Once all containers are running, access the services:

- **Flask Application**: http://localhost:5000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Alertmanager**: http://localhost:9093
- **Node Exporter**: http://localhost:9100

## Service Details

### Flask Application (Port 5000)
- **Health Check**: http://localhost:5000/health
- **Metrics**: http://localhost:5000/metrics
- **API Endpoints**:
  - `GET /api/orders` - List orders
  - `POST /api/orders` - Create order
  - `GET /api/simulate-error` - Simulate errors
  - `GET /api/simulate-slow` - Simulate slow responses

### Prometheus (Port 9090)
- **Web UI**: http://localhost:9090
- **Targets**: http://localhost:9090/targets
- **Alerts**: http://localhost:9090/alerts

### Grafana (Port 3000)
- **Login**: admin/admin
- **Dashboard**: Pre-configured "Flask App Observability" dashboard
- **Data Source**: Prometheus (auto-configured)

### Alertmanager (Port 9093)
- **Web UI**: http://localhost:9093
- **Webhook Endpoint**: http://localhost:5001/webhook

## Testing the Setup

### 1. Generate Test Traffic

```bash
# Create some orders
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/orders \
    -H "Content-Type: application/json" \
    -d "{\"product\": \"Product $i\", \"quantity\": $((RANDOM % 10 + 1)), \"price\": $((RANDOM % 100 + 10))}"
  sleep 1
done

# Get all orders
curl http://localhost:5000/api/orders

# Check health
curl http://localhost:5000/health
```

### 2. Test Error Scenarios

```bash
# Generate 500 errors
for i in {1..5}; do
  curl http://localhost:5000/api/simulate-error?type=server
  sleep 1
done

# Generate slow responses
curl http://localhost:5000/api/simulate-slow?delay=3

# Generate memory stress
curl http://localhost:5000/api/memory-stress?size=50
```

### 3. Verify Metrics

```bash
# Check Prometheus metrics
curl http://localhost:5000/metrics | grep flask_

# Check specific metrics
curl "http://localhost:9090/api/v1/query?query=flask_http_request_total"
curl "http://localhost:9090/api/v1/query?query=rate(flask_http_request_total[1m])"
```

### 4. Test Alerting

```bash
# Send test alert to Alertmanager
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "instance": "localhost:5000"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing the alerting pipeline"
    }
  }]'

# Check alert webhook logs
docker-compose logs alert-webhook
```

## Monitoring Key Metrics

### Application Metrics
- **Request Rate**: `rate(flask_http_request_total[1m])`
- **Error Rate**: `rate(flask_http_errors_total[1m]) / rate(flask_http_request_total[1m]) * 100`
- **Response Time P95**: `histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))`
- **Orders Created**: `flask_orders_total`
- **Active Connections**: `flask_active_connections`

### System Metrics
- **CPU Usage**: `system_cpu_usage_percent`
- **Memory Usage**: `system_memory_usage_percent`
- **Disk Usage**: `system_disk_usage_percent`

### Node Exporter Metrics
- **CPU**: `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **Memory**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **Disk**: `100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)`

## Alert Rules

The following alerts are configured:

1. **HighErrorRate**: Error rate > 5% for 2 minutes
2. **HighLatency**: 95th percentile latency > 1s for 2 minutes
3. **AppDown**: Flask app unreachable for 1 minute
4. **NoHealthChecks**: No health checks for 5 minutes
5. **HighMemoryUsage**: Memory usage > 85% for 2 minutes
6. **HighDiskUsage**: Disk usage > 90% for 1 minute
7. **HighCPUUsage**: CPU usage > 80% for 5 minutes

## Auto-Remediation

The system includes automatic remediation for:

1. **High Memory Usage**: Restarts Flask app container
2. **High Disk Usage**: Cleans up temporary files and logs
3. **App Down**: Attempts to restart the Flask app container

All remediation actions are logged to `/var/log/alerts.log`.

## Customization

### Adding Custom Metrics

Edit `app.py` to add new Prometheus metrics:

```python
CUSTOM_METRIC = Counter('custom_metric_total', 'Description of custom metric')

@app.route('/custom-endpoint')
def custom_endpoint():
    CUSTOM_METRIC.inc()
    return jsonify({"status": "success"})
```

### Adding New Alerts

Edit `alert_rules.yml`:

```yaml
- alert: CustomAlert
  expr: custom_metric_total > 100
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Custom metric threshold exceeded"
```

### Configuring Notifications

#### Email Notifications
Update `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
```

#### Slack Notifications
Update `alertmanager.yml`:

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
```

## Troubleshooting

### Common Issues

1. **Containers not starting**:
   ```bash
   docker-compose logs <service-name>
   docker-compose down && docker-compose up -d
   ```

2. **Prometheus not scraping targets**:
   - Check `prometheus.yml` configuration
   - Verify network connectivity between containers
   - Check target health: http://localhost:9090/targets

3. **Grafana dashboard not loading**:
   - Verify Prometheus data source configuration
   - Check if metrics are being collected
   - Import dashboard manually if auto-provisioning fails

4. **Alerts not firing**:
   - Check alert rules syntax: http://localhost:9090/rules
   - Verify Alertmanager configuration: http://localhost:9093

5. **Auto-remediation not working**:
   - Check webhook service logs: `docker-compose logs alert-webhook`
   - Verify Docker socket is mounted correctly
   - Check script permissions

### Useful Commands

```bash
# Restart specific service
docker-compose restart <service-name>

# View logs for specific service
docker-compose logs -f <service-name>

# Execute command in running container
docker-compose exec flask-app bash

# Check container resource usage
docker stats

# Clean up everything
docker-compose down -v
docker system prune -a
```

## Production Considerations

### Security
- Change default Grafana password
- Use proper authentication for Prometheus and Alertmanager
- Secure webhook endpoints
- Use secrets management for sensitive configuration

### Performance
- Adjust Prometheus retention period
- Configure appropriate scrape intervals
- Monitor container resource usage
- Use persistent volumes for data

### Backup
- Backup Grafana dashboards and configuration
- Backup Prometheus data
- Version control all configuration files

### Scaling
- Use Docker Swarm or Kubernetes for multi-node deployment
- Implement service discovery for dynamic targets
- Consider using Prometheus federation for large deployments

## Next Steps

1. **Add Log Aggregation**: Integrate ELK stack or Loki
2. **Implement Tracing**: Add Jaeger for distributed tracing
3. **Enhanced Dashboards**: Create business-specific dashboards
4. **Advanced Alerting**: Implement alert routing and escalation
5. **CI/CD Integration**: Automate deployment and monitoring setup