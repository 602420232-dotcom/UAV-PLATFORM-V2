"""
Alert Webhook Receiver
Receives alerts from Alertmanager and forwards to various channels
"""

from flask import Flask, request, jsonify
import logging
import requests
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
SLACK_CHANNEL_CRITICAL = '#alerts-critical'
SLACK_CHANNEL_WARNING = '#alerts-warning'

class AlertHandler:
    """Handle incoming alerts"""
    
    def __init__(self):
        self.alerts = []
    
    def process_alert(self, data):
        """Process incoming alert data"""
        alerts = data.get('alerts', [])
        
        for alert in alerts:
            alert_info = {
                'status': alert.get('status'),
                'labels': alert.get('labels', {}),
                'annotations': alert.get('annotations', {}),
                'starts_at': alert.get('startsAt'),
                'ends_at': alert.get('endsAt'),
                'fingerprint': alert.get('fingerprint'),
                'processed_at': datetime.now().isoformat()
            }
            
            self.alerts.append(alert_info)
            
            # Log alert
            logger.info(f"Received alert: {alert_info['labels'].get('alertname', 'unknown')}")
            
            # Send notifications based on severity
            severity = alert_info['labels'].get('severity', 'info')
            
            if severity == 'critical':
                self.send_critical_alert(alert_info)
            elif severity == 'warning':
                self.send_warning_alert(alert_info)
    
    def send_critical_alert(self, alert):
        """Send critical alert to Slack"""
        message = self.format_slack_message(alert, 'danger')
        self.send_to_slack(message, SLACK_CHANNEL_CRITICAL)
        
        # Also send to PagerDuty if configured
        self.send_to_pagerduty(alert)
    
    def send_warning_alert(self, alert):
        """Send warning alert to Slack"""
        message = self.format_slack_message(alert, 'warning')
        self.send_to_slack(message, SLACK_CHANNEL_WARNING)
    
    def format_slack_message(self, alert, color):
        """Format alert as Slack message"""
        labels = alert['labels']
        annotations = alert['annotations']
        
        status_emoji = "🔴" if alert['status'] == 'firing' else "✅"
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} {labels.get('alertname', 'Unknown Alert')}",
                    "fields": [
                        {
                            "title": "Severity",
                            "value": labels.get('severity', 'unknown'),
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": alert['status'].upper(),
                            "short": True
                        },
                        {
                            "title": "Component",
                            "value": labels.get('component', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Service",
                            "value": labels.get('job', 'N/A'),
                            "short": True
                        }
                    ],
                    "text": annotations.get('description', 'No description'),
                    "footer": f"UAV Platform | {alert['processed_at']}",
                    "ts": datetime.now().timestamp()
                }
            ]
        }
        
        # Add runbook link if available
        if 'runbook_url' in annotations:
            message['attachments'][0]['title_link'] = annotations['runbook_url']
        
        return message
    
    def send_to_slack(self, message, channel):
        """Send message to Slack"""
        try:
            payload = {
                'channel': channel,
                **message
            }
            
            response = requests.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent to {channel}")
            else:
                logger.error(f"Failed to send Slack notification: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    def send_to_pagerduty(self, alert):
        """Send alert to PagerDuty (if configured)"""
        # This is a placeholder for PagerDuty integration
        logger.info(f"PagerDuty alert sent: {alert['labels'].get('alertname')}")

# Global handler
alert_handler = AlertHandler()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive alerts from Alertmanager"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process alerts
        alert_handler.process_alert(data)
        
        return jsonify({
            'status': 'success',
            'message': 'Alerts processed',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'alerts_received': len(alert_handler.alerts)
    }), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all processed alerts"""
    return jsonify({
        'count': len(alert_handler.alerts),
        'alerts': alert_handler.alerts[-100:]  # Last 100 alerts
    }), 200

@app.route('/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear all alerts"""
    alert_handler.alerts = []
    return jsonify({
        'status': 'success',
        'message': 'Alerts cleared'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
