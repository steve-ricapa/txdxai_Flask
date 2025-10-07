from datetime import datetime

def normalize_system_data(provider, raw_data):
    if provider == 'grafana':
        return {
            'system': raw_data.get('title', 'Unknown System'),
            'status': 'online',
            'alerts': [],
            'metrics': {
                'dashboards': len(raw_data.get('panels', [])),
                'last_update': datetime.utcnow().isoformat()
            }
        }
    elif provider == 'palo_alto':
        return {
            'system': 'Palo Alto Firewall',
            'status': raw_data.get('status', 'online'),
            'alerts': raw_data.get('alerts', []),
            'metrics': {
                'uptime': raw_data.get('uptime', 99.9),
                'threat_count': raw_data.get('threat_count', 0)
            }
        }
    elif provider == 'splunk':
        return {
            'system': 'Splunk SIEM',
            'status': raw_data.get('status', 'online'),
            'alerts': raw_data.get('alerts', []),
            'metrics': {
                'events_indexed': raw_data.get('events_indexed', 0),
                'search_count': raw_data.get('search_count', 0)
            }
        }
    elif provider == 'wazuh':
        return {
            'system': 'Wazuh Security',
            'status': raw_data.get('status', 'online'),
            'alerts': raw_data.get('alerts', []),
            'metrics': {
                'agents_active': raw_data.get('agents_active', 0),
                'alerts_today': raw_data.get('alerts_today', 0)
            }
        }
    elif provider == 'meraki':
        return {
            'system': 'Cisco Meraki',
            'status': raw_data.get('status', 'online'),
            'alerts': raw_data.get('alerts', []),
            'metrics': {
                'devices_online': raw_data.get('devices_online', 0),
                'network_health': raw_data.get('network_health', 100)
            }
        }
    else:
        return {
            'system': f'{provider} System',
            'status': 'unknown',
            'alerts': [],
            'metrics': {}
        }


def normalize_alert_data(provider, raw_alert):
    base_alert = {
        'id': raw_alert.get('id', ''),
        'title': raw_alert.get('title', 'Unknown Alert'),
        'severity': raw_alert.get('severity', 'medium'),
        'source': provider,
        'time': raw_alert.get('time', datetime.utcnow().isoformat())
    }
    
    if provider == 'palo_alto':
        base_alert.update({
            'description': raw_alert.get('description', ''),
            'category': raw_alert.get('category', 'security')
        })
    elif provider == 'splunk':
        base_alert.update({
            'description': raw_alert.get('message', ''),
            'search_id': raw_alert.get('search_id', '')
        })
    elif provider == 'wazuh':
        base_alert.update({
            'description': raw_alert.get('rule_description', ''),
            'rule_id': raw_alert.get('rule_id', '')
        })
    
    return base_alert


def normalize_vulnerability_data(provider, raw_vuln):
    return {
        'cve_id': raw_vuln.get('cve_id', ''),
        'title': raw_vuln.get('title', 'Unknown Vulnerability'),
        'severity': raw_vuln.get('severity', 'medium'),
        'cvss_score': raw_vuln.get('cvss_score', 0.0),
        'description': raw_vuln.get('description', ''),
        'affected_systems': raw_vuln.get('affected_systems', []),
        'source': provider,
        'discovered_at': raw_vuln.get('discovered_at', datetime.utcnow().isoformat())
    }
