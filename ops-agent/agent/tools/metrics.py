import random
from datetime import datetime, timezone


def query_prometheus(service: str, metric: str, duration: str = "5m") -> dict:
    """
    Mock Prometheus query — returns simulated metric data.
    Week 11: replace with real Prometheus HTTP API call.
    """
    # Simulate different error scenarios per service
    scenarios = {
        "payments-api": {"error_rate": 18.4, "latency_p99": 2340, "request_rate": 450},
        "auth-service": {"error_rate": 0.2, "latency_p99": 120, "request_rate": 890},
        "inventory-api": {"error_rate": 4.1, "latency_p99": 890, "request_rate": 230},
    }

    data = scenarios.get(service, {
        "error_rate": round(random.uniform(0.1, 2.0), 2),
        "latency_p99": random.randint(100, 500),
        "request_rate": random.randint(100, 1000),
    })

    return {
        "service": service,
        "metric": metric,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "threshold_breached": data["error_rate"] > 5.0,
    }


# Tool schema — this is what you pass to the LLM
PROMETHEUS_TOOL = {
    "name": "query_prometheus",
    "description": (
        "Query Prometheus metrics for a given service. "
        "Use this to get error rates, latency, and request rates "
        "when investigating an alert."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "description": "The service name to query e.g. payments-api"
            },
            "metric": {
                "type": "string",
                "description": "The metric type to query e.g. error_rate, latency_p99"
            },
            "duration": {
                "type": "string",
                "description": "Time window for the query e.g. 5m, 15m, 1h",
                "default": "5m"
            }
        },
        "required": ["service", "metric"]
    }
}