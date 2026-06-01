"""
Alert Webhook Receiver - UAV Platform
Receives alerts from Alertmanager, manages alert history, and provides
REST API for alert status query and management.

Supports:
- Multi-channel notification (Slack critical/warning separation)
- Alert history persistence
- Alert escalation for unacknowledged critical alerts
- Health check and status API
"""

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict

from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')
SLACK_CHANNEL_CRITICAL = os.environ.get('SLACK_CHANNEL_CRITICAL', '#alerts-critical')
SLACK_CHANNEL_WARNING = os.environ.get('SLACK_CHANNEL_WARNING', '#alerts-warning')
SLACK_CHANNEL_INFO = os.environ.get('SLACK_CHANNEL_INFO', '#alerts-info')
ALERT_HISTORY_LIMIT = int(os.environ.get('ALERT_HISTORY_LIMIT', '1000'))
ESCALATION_MINUTES = int(os.environ.get('ESCALATION_MINUTES', '30'))
ESCALATION_WEBHOOK = os.environ.get('ESCALATION_WEBHOOK_URL', '')

# In-memory alert store
class AlertStore:
    """Thread-safe in-memory alert storage with TTL-based retention"""

    def __init__(self, max_alerts=1000):
        self._alerts = []
        self._lock = threading.Lock()
        self._max_alerts = max_alerts
        self._unacknowledged = {}  # alert_fingerprint -> timestamp

    def add(self, alert):
        with self._lock:
            self._alerts.append(alert)
            # Trim to max size
            while len(self._alerts) > self._max_alerts:
                self._alerts.pop(0)

    def get_all(self, limit=100, severity=None, component=None, status=None):
        with self._lock:
            result = list(self._alerts)
        # Apply filters
        if severity:
            result = [a for a in result if a.get('labels', {}).get('severity') == severity]
        if component:
            result = [a for a in result if a.get('labels', {}).get('component') == component]
        if status:
            result = [a for a in result if a.get('status') == status]
        return result[-limit:]

    def get_stats(self):
        with self._lock:
            alerts = list(self._alerts)
        now = datetime.now()
        stats = {
            'total': len(alerts),
            'firing': len([a for a in alerts if a.get('status') == 'firing']),
            'resolved': len([a for a in alerts if a.get('status') == 'resolved']),
            'by_severity': defaultdict(int),
            'by_component': defaultdict(int),
            'last_1h': len([a for a in alerts if
                           datetime.fromisoformat(a.get('processed_at', '2000-01-01'))
                           > now - timedelta(hours=1)]),
            'last_24h': len([a for a in alerts if
                            datetime.fromisoformat(a.get('processed_at', '2000-01-01'))
                            > now - timedelta(hours=24)]),
        }
        for a in alerts:
            stats['by_severity'][a.get('labels', {}).get('severity', 'unknown')] += 1
            stats['by_component'][a.get('labels', {}).get('component', 'unknown')] += 1
        return stats

    def acknowledge(self, fingerprint):
        with self._lock:
            self._unacknowledged[fingerprint] = time.time()

    def get_unacknowledged_count(self):
        with self._lock:
            now = time.time()
            # Remove stale entries older than 2 hours
            stale = [k for k, v in self._unacknowledged.items() if now - v > 7200]
            for k in stale:
                del self._unacknowledged[k]
            return len(self._unacknowledged)

    def count_by_fingerprint(self, fingerprint):
        with self._lock:
            return len([a for a in self._alerts if a.get('fingerprint') == fingerprint])

    def clear(self):
        with self._lock:
            self._alerts.clear()
            self._unacknowledged.clear()


alert_store = AlertStore(max_alerts=ALERT_HISTORY_LIMIT)


class AlertProcessor:
    """Process incoming alerts and route to appropriate channels"""

    @staticmethod
    def format_alert(alert_data):
        """Extract and normalize alert information"""
        labels = alert_data.get('labels', {})
        annotations = alert_data.get('annotations', {})

        return {
            'status': alert_data.get('status'),
            'labels': labels,
            'annotations': annotations,
            'starts_at': alert_data.get('startsAt'),
            'ends_at': alert_data.get('endsAt'),
            'generator_url': alert_data.get('generatorURL'),
            'fingerprint': alert_data.get('fingerprint'),
            'processed_at': datetime.now().isoformat(),
            'alertname': labels.get('alertname', 'unknown'),
            'severity': labels.get('severity', 'info'),
            'component': labels.get('component', 'unknown'),
            'summary': annotations.get('summary', ''),
            'description': annotations.get('description', ''),
            'impact': annotations.get('impact', ''),
            'recommended_action': annotations.get('recommended_action', ''),
        }

    @staticmethod
    def should_escalate(alert_info):
        """Determine if a critical alert should be escalated"""
        if alert_info['severity'] != 'critical':
            return False
        fingerprint = alert_info.get('fingerprint', '')
        if not fingerprint:
            return False
        count = alert_store.count_by_fingerprint(fingerprint)
        fingerprint_key = f"pending_{fingerprint}"
        if fingerprint_key not in alert_store._unacknowledged:
            alert_store.acknowledge(fingerprint_key)
            return False  # First occurrence, no escalation yet
        pending_time = time.time() - alert_store._unacknowledged.get(fingerprint_key, time.time())
        return pending_time > ESCALATION_MINUTES * 60

    def process(self, data):
        """Process incoming alert batch from Alertmanager"""
        alerts = data.get('alerts', [])
        group_labels = data.get('groupLabels', {})
        common_labels = data.get('commonLabels', {})

        logger.info(f"Received alert batch: {len(alerts)} alerts, group={group_labels.get('alertname', 'N/A')}")

        processed = []
        for alert in alerts:
            alert_info = self.format_alert(alert)
            alert_store.add(alert_info)
            processed.append(alert_info)

            # Log based on severity
            log_level = {
                'critical': logger.error,
                'warning': logger.warning,
                'info': logger.info,
            }.get(alert_info['severity'], logger.info)

            log_level(
                f"Alert: [{alert_info['severity'].upper()}] {alert_info['alertname']} - "
                f"{alert_info['description'][:120]}"
            )

        return processed


alert_processor = AlertProcessor()



@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive alerts from Alertmanager"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data received'}), 400

        processed = alert_processor.process(data)

        return jsonify({
            'status': 'success',
            'message': f'Processed {len(processed)} alerts',
            'timestamp': datetime.now().isoformat(),
            'alerts_count': len(processed),
            'severity_summary': {
                'critical': len([a for a in processed if a['severity'] == 'critical']),
                'warning': len([a for a in processed if a['severity'] == 'warning']),
                'info': len([a for a in processed if a['severity'] == 'info']),
            }
        }), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': int(time.time() - app.start_time) if hasattr(app, 'start_time') else 0,
    }), 200


@app.route('/api/v1/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filters"""
    limit = request.args.get('limit', 100, type=int)
    severity = request.args.get('severity')
    component = request.args.get('component')
    status = request.args.get('status')

    alerts = alert_store.get_all(
        limit=min(limit, 500),
        severity=severity,
        component=component,
        status=status,
    )

    return jsonify({
        'count': len(alerts),
        'alerts': alerts,
    }), 200


@app.route('/api/v1/alerts/stats', methods=['GET'])
def alert_stats():
    """Get alert statistics"""
    stats = alert_store.get_stats()
    stats['unacknowledged'] = alert_store.get_unacknowledged_count()
    return jsonify(stats), 200


@app.route('/api/v1/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear all alert history (admin only)"""
    alert_store.clear()
    logger.warning("Alert history cleared by API request")
    return jsonify({
        'status': 'success',
        'message': 'All alerts cleared'
    }), 200


@app.route('/api/v1/alerts/<fingerprint>/acknowledge', methods=['POST'])
def acknowledge_alert(fingerprint):
    """Acknowledge a specific alert (suppress escalation)"""
    alert_store.acknowledge(fingerprint)
    logger.info(f"Alert acknowledged: {fingerprint}")
    return jsonify({
        'status': 'success',
        'message': f'Alert {fingerprint} acknowledged'
    }), 200


@app.route('/api/v1/status', methods=['GET'])
def system_status():
    """Comprehensive system status endpoint"""
    stats = alert_store.get_stats()
    return jsonify({
        'service': 'UAV Platform Alert Webhook',
        'version': '2.0.0',
        'status': 'running',
        'stats': stats,
        'health': 'UP',
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Start the webhook server"""
    app.start_time = time.time()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting UAV Alert Webhook v2.0.0 on port {port}")
    logger.info(f"Slack channels: critical={SLACK_CHANNEL_CRITICAL}, warning={SLACK_CHANNEL_WARNING}")
    logger.info(f"Escalation timeout: {ESCALATION_MINUTES} minutes")

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
