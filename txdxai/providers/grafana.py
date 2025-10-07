import requests
from datetime import datetime

def list_dashboards(grafana_url, api_token):
    try:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f'{grafana_url}/api/search?type=dash-db',
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f'Failed to list Grafana dashboards: {str(e)}')


def fetch_panel_data(grafana_url, api_token, dashboard_uid, panel_id, from_ts=None, to_ts=None):
    try:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        if not from_ts:
            from_ts = int((datetime.utcnow().timestamp() - 3600) * 1000)
        if not to_ts:
            to_ts = int(datetime.utcnow().timestamp() * 1000)
        
        dashboard_response = requests.get(
            f'{grafana_url}/api/dashboards/uid/{dashboard_uid}',
            headers=headers,
            timeout=10
        )
        dashboard_response.raise_for_status()
        dashboard = dashboard_response.json()
        
        panels = dashboard.get('dashboard', {}).get('panels', [])
        panel = next((p for p in panels if p.get('id') == panel_id), None)
        
        if not panel:
            raise Exception(f'Panel {panel_id} not found in dashboard {dashboard_uid}')
        
        return {
            'panel_id': panel_id,
            'title': panel.get('title', 'Unknown Panel'),
            'type': panel.get('type', 'unknown'),
            'targets': panel.get('targets', []),
            'from': from_ts,
            'to': to_ts
        }
    except Exception as e:
        raise Exception(f'Failed to fetch Grafana panel data: {str(e)}')


def get_dashboard_snapshot(grafana_url, api_token, dashboard_uid):
    try:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'{grafana_url}/api/dashboards/uid/{dashboard_uid}',
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        dashboard = response.json()
        
        return {
            'uid': dashboard_uid,
            'title': dashboard.get('dashboard', {}).get('title', 'Unknown'),
            'panels': [
                {
                    'id': p.get('id'),
                    'title': p.get('title', 'Unknown'),
                    'type': p.get('type', 'unknown')
                }
                for p in dashboard.get('dashboard', {}).get('panels', [])
            ]
        }
    except Exception as e:
        raise Exception(f'Failed to get Grafana dashboard snapshot: {str(e)}')


def execute_grafana_action(credentials, action, params):
    grafana_url = params.get('grafana_url')
    api_token = credentials.get('api_token')
    
    if not grafana_url or not api_token:
        raise Exception('Grafana URL and API token are required')
    
    if action == 'list_dashboards':
        return list_dashboards(grafana_url, api_token)
    elif action == 'fetch_panel_data':
        dashboard_uid = params.get('dashboard_uid')
        panel_id = params.get('panel_id')
        from_ts = params.get('from_ts')
        to_ts = params.get('to_ts')
        return fetch_panel_data(grafana_url, api_token, dashboard_uid, panel_id, from_ts, to_ts)
    elif action == 'get_dashboard_snapshot':
        dashboard_uid = params.get('dashboard_uid')
        return get_dashboard_snapshot(grafana_url, api_token, dashboard_uid)
    else:
        raise Exception(f'Unknown Grafana action: {action}')
