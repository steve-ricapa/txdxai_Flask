"""
Mock Security Tools Integrations
Simulated responses from Palo Alto, Splunk, Grafana, etc.
"""

from typing import List, Dict
from datetime import datetime, timedelta
import random


def get_palo_alto_alerts() -> List[Dict]:
    """Mock Palo Alto Networks alerts"""
    return [
        {
            "id": "PA-2025-001",
            "severity": "high",
            "message": "Suspicious outbound connection detected",
            "source_ip": "192.168.1.105",
            "destination": "suspicious-domain.com",
            "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            "action": "blocked"
        },
        {
            "id": "PA-2025-002",
            "severity": "medium",
            "message": "Multiple failed login attempts",
            "source_ip": "10.0.0.45",
            "attempts": 12,
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "action": "monitored"
        }
    ]


def get_splunk_logs(query: str = "*", limit: int = 10) -> List[Dict]:
    """Mock Splunk logs"""
    log_types = ["INFO", "WARN", "ERROR", "DEBUG"]
    sources = ["web-server", "api-gateway", "database", "auth-service"]
    
    return [
        {
            "id": f"SPL-{i:04d}",
            "level": random.choice(log_types),
            "source": random.choice(sources),
            "message": f"Mock log entry {i}: {query}",
            "timestamp": (datetime.utcnow() - timedelta(minutes=i*5)).isoformat(),
            "metadata": {"query": query, "mock": True}
        }
        for i in range(limit)
    ]


def get_grafana_metrics() -> Dict:
    """Mock Grafana system metrics"""
    return {
        "cpu_usage": round(random.uniform(20, 85), 2),
        "memory_usage": round(random.uniform(40, 90), 2),
        "disk_usage": round(random.uniform(30, 75), 2),
        "network_in": round(random.uniform(100, 1000), 2),
        "network_out": round(random.uniform(50, 800), 2),
        "active_connections": random.randint(50, 500),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy"
    }


def get_wazuh_alerts() -> List[Dict]:
    """Mock Wazuh security alerts"""
    return [
        {
            "id": "WZ-2025-101",
            "rule_id": 5501,
            "level": 8,
            "description": "Integrity checksum changed",
            "agent": "web-server-01",
            "file": "/etc/passwd",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
        },
        {
            "id": "WZ-2025-102",
            "rule_id": 5402,
            "level": 5,
            "description": "New file added to monitored directory",
            "agent": "api-server-02",
            "file": "/var/www/uploads/new_file.php",
            "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        }
    ]


def get_meraki_network_status() -> Dict:
    """Mock Cisco Meraki network status"""
    return {
        "organization": "Mock Organization",
        "network_id": "N_12345678",
        "status": "online",
        "device_count": 15,
        "active_clients": 42,
        "bandwidth_usage": {
            "upload_mbps": round(random.uniform(10, 100), 2),
            "download_mbps": round(random.uniform(50, 500), 2)
        },
        "alerts": [
            {
                "type": "latency",
                "message": "High latency detected on AP-3",
                "severity": "warning"
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


def execute_security_action(action_type: str, parameters: Dict) -> Dict:
    """
    Mock execution of security actions
    In production, this would call real security tools APIs
    """
    return {
        "status": "mock_success",
        "action": action_type,
        "parameters": parameters,
        "message": f"[MOCK] Would execute {action_type} with params: {parameters}",
        "execution_time": datetime.utcnow().isoformat(),
        "requires_victoria": action_type in ["block_ip", "quarantine_device", "emergency_response"]
    }
