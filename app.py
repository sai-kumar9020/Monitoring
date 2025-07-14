from flask import Flask, request, jsonify
import time
import random
import logging
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('flask_http_request_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('flask_http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ERROR_COUNT = Counter('flask_http_errors_total', 'Total HTTP errors', ['method', 'endpoint', 'status'])
ORDER_COUNT = Counter('flask_orders_total', 'Total orders created')
ACTIVE_CONNECTIONS = Gauge('flask_active_connections', 'Active connections')

# System metrics
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage')

# In-memory storage for demo
orders = []
active_connections = 0

def update_system_metrics():
    """Update system metrics"""
    try:
        CPU_USAGE.set(psutil.cpu_percent())
        MEMORY_USAGE.set(psutil.virtual_memory().percent)
        DISK_USAGE.set(psutil.disk_usage('/').percent)
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def metrics_middleware(f):
    """Decorator to track metrics for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Increment active connections
            global active_connections
            active_connections += 1
            ACTIVE_CONNECTIONS.set(active_connections)
            
            # Execute the function
            response = f(*args, **kwargs)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = getattr(response, 'status_code', 200)
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
            
            # Track errors
            if status_code >= 400:
                ERROR_COUNT.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=status_code
                ).inc()
            
            return response
            
        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=500
            ).inc()
            
            logger.error(f"Error in {request.endpoint}: {e}")
            return jsonify({"error": "Internal server error"}), 500
            
        finally:
            # Decrement active connections
            active_connections -= 1
            ACTIVE_CONNECTIONS.set(active_connections)
            
            # Update system metrics
            update_system_metrics()
    
    return decorated_function

@app.route('/health')
@metrics_middleware
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "flask-observability-app"
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/orders', methods=['GET'])
@metrics_middleware
def get_orders():
    """Get all orders"""
    # Simulate some processing time
    time.sleep(random.uniform(0.1, 0.5))
    
    return jsonify({
        "orders": orders,
        "total": len(orders)
    })

@app.route('/api/orders', methods=['POST'])
@metrics_middleware
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()
        
        # Simulate processing time
        time.sleep(random.uniform(0.2, 0.8))
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% error rate
            return jsonify({"error": "Order processing failed"}), 500
        
        # Create order
        order = {
            "id": len(orders) + 1,
            "product": data.get('product', 'Unknown'),
            "quantity": data.get('quantity', 1),
            "price": data.get('price', 0),
            "timestamp": time.time()
        }
        
        orders.append(order)
        ORDER_COUNT.inc()
        
        logger.info(f"Order created: {order['id']}")
        
        return jsonify(order), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({"error": "Invalid order data"}), 400

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@metrics_middleware
def get_order(order_id):
    """Get specific order"""
    # Simulate processing time
    time.sleep(random.uniform(0.05, 0.3))
    
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(order)

@app.route('/api/simulate-error')
@metrics_middleware
def simulate_error():
    """Endpoint to simulate errors for testing"""
    error_type = request.args.get('type', 'server')
    
    if error_type == 'client':
        return jsonify({"error": "Bad request simulation"}), 400
    elif error_type == 'server':
        return jsonify({"error": "Internal server error simulation"}), 500
    else:
        return jsonify({"error": "Not found simulation"}), 404

@app.route('/api/simulate-slow')
@metrics_middleware
def simulate_slow():
    """Endpoint to simulate slow responses"""
    delay = float(request.args.get('delay', 2.0))
    time.sleep(delay)
    return jsonify({"message": f"Delayed response after {delay} seconds"})

@app.route('/api/memory-stress')
@metrics_middleware
def memory_stress():
    """Endpoint to simulate memory usage"""
    # Simulate memory usage
    size = int(request.args.get('size', 100))  # MB
    data = 'x' * (size * 1024 * 1024)  # Create large string
    
    return jsonify({
        "message": f"Allocated {size}MB of memory",
        "size": len(data)
    })

@app.route('/')
@metrics_middleware
def index():
    """Main index page"""
    return jsonify({
        "service": "Flask Observability App",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/metrics": "Prometheus metrics",
            "/api/orders": "Order management",
            "/api/simulate-error": "Error simulation",
            "/api/simulate-slow": "Slow response simulation",
            "/api/memory-stress": "Memory stress test"
        }
    })

if __name__ == '__main__':
    # Initialize system metrics
    update_system_metrics()
    
    app.run(host='0.0.0.0', port=5000, debug=True)