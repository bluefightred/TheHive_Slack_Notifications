#!/usr/bin/env python3

import json
import logging
import os
import time
from datetime import datetime
import requests
from flask import Flask, request, jsonify

# Get config from environment variables
hookURL = os.environ['hookURL']
slackChannel = os.environ['slackChannel']
orgName = os.environ['orgName']
orgIcon = os.environ['orgIcon']
hiveURL = os.environ.get('hiveURL', 'http://thehive:9000')
caseURL = hiveURL + "/index.html#/case/"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/app/logs/webhook.log'
)
logger = logging.getLogger()

def add_object(title, value, short):
    """Helper function to create field objects"""
    if value is None or value == "":
        value = "N/A"
    return {
        "title": title,
        "value": str(value),
        "short": short
    }

def get_severity_color(severity):
    """Get color based on severity level"""
    return {
        1: "#97A2A0",  # Grey for Low
        2: "#2684FF",  # Blue for Medium
        3: "#FFC107",  # Yellow for High
        4: "#FF5722"   # Red for Critical
    }.get(severity, "#97A2A0")

def process_observable_event(event):
    """Handle Observable creation events with better formatting"""
    fields = []
    
    if 'object' in event:
        obj = event['object']
        
        # Add data type if available
        if 'dataType' in obj:
            fields.append(add_object("Type", obj['dataType'], True))
            
        # Add observable value if available
        if 'data' in obj:
            fields.append(add_object("Value", obj['data'], False))
            
        # Add tags if available
        if 'tags' in obj and obj['tags']:
            fields.append(add_object("Tags", ", ".join(obj['tags']), False))
            
        # Add TLP if available
        if 'tlp' in obj:
            fields.append(add_object("TLP", obj['tlp'], True))
            
        # Add message if available
        if 'message' in obj:
            fields.append(add_object("Message", obj['message'], False))
            
        # Add ioc if available
        if 'ioc' in obj:
            fields.append(add_object("IOC", str(obj['ioc']), True))

    title = "Observable Details"
    if 'dataType' in obj and 'data' in obj:
        title = f"{obj['dataType']}: {obj['data']}"

    attachments = [{
        "fallback": "New Observable Created",
        "pretext": "🔍 New Observable Created",
        "title": title,
        "color": "#2684FF",  # Blue for observables
        "fields": fields,
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]

    send_to_slack(event, attachments)

def process_alert_event(event):
    """Handle Alert creation events with better formatting"""
    fields = []
    severity_color = "#97A2A0"  # Default color
    
    if 'object' in event:
        obj = event['object']
        
        # Add timestamp if available
        if 'date' in obj:
            fields.append(add_object("Timestamp", 
                datetime.fromtimestamp(obj['date']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                True))
            
        # Add severity/level if available
        if 'severity' in obj:
            severity = obj['severity']
            severity_color = get_severity_color(severity)
            fields.append(add_object("Severity", f"Level {severity}", True))
        
        # Add source if available
        if 'source' in obj:
            fields.append(add_object("Source", obj['source'], True))
            
        # Add MITRE ATT&CK ID if available
        if 'mitreId' in obj:
            fields.append(add_object("MITRE ATT&CK", obj['mitreId'], True))
            
        # Add case template if available
        if 'caseTemplate' in obj:
            fields.append(add_object("Case Template", obj['caseTemplate'], True))
            
        # Add tags if available
        if 'tags' in obj and obj['tags']:
            fields.append(add_object("Tags", ", ".join(obj['tags']), False))
            
        # Add description if available
        if 'description' in obj:
            # Format description if it's JSON
            try:
                desc_json = json.loads(obj['description'])
                formatted_desc = json.dumps(desc_json, indent=2)
                fields.append(add_object("Description", f"```{formatted_desc}```", False))
            except json.JSONDecodeError:
                fields.append(add_object("Description", obj['description'], False))

    attachments = [{
        "fallback": obj.get('title', 'New Alert Created'),
        "pretext": "🚨 New Alert Created",
        "title": obj.get('title', 'Alert Details'),
        "color": severity_color,
        "fields": fields,
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]

    send_to_slack(event, attachments)

def process_case_event(event):
    """Handle Case creation/update events"""
    fields = []
    
    if 'object' in event:
        obj = event['object']
        case_id = obj.get('caseId', 'N/A')
        fields.append(add_object("Case #", case_id, True))
        
        if 'title' in obj:
            fields.append(add_object("Title", obj['title'], False))
        
        if 'description' in obj:
            fields.append(add_object("Description", obj['description'], False))
            
        if 'severity' in obj:
            severity = obj['severity']
            fields.append(add_object("Severity", f"Level {severity}", True))
            
        if 'status' in obj:
            fields.append(add_object("Status", obj['status'], True))
            
        if 'owner' in obj:
            fields.append(add_object("Owner", obj['owner'], True))
            
        if 'tlp' in obj:
            fields.append(add_object("TLP", obj['tlp'], True))
            
        if 'tags' in obj and obj['tags']:
            fields.append(add_object("Tags", ", ".join(obj['tags']), False))

    operation = event.get('operation', 'Unknown')
    pretext = f"📁 Case {operation}"
    color = "#2196F3"  # Blue for cases

    attachments = [{
        "fallback": f"Case {operation}",
        "pretext": pretext,
        "title": obj.get('title', 'Case Details'),
        "title_link": f"{caseURL}{event.get('objectId')}/details",
        "color": color,
        "fields": fields,
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]

    send_to_slack(event, attachments)

def process_task_event(event):
    """Handle Task creation/update events"""
    fields = []
    
    if 'object' in event:
        obj = event['object']
        
        if 'title' in obj:
            fields.append(add_object("Title", obj['title'], False))
            
        if 'status' in obj:
            fields.append(add_object("Status", obj['status'], True))
            
        if 'owner' in obj:
            fields.append(add_object("Owner", obj['owner'], True))
            
        if 'description' in obj:
            fields.append(add_object("Description", obj['description'], False))

    operation = event.get('operation', 'Unknown')
    pretext = f"✅ Task {operation}"
    color = "#4CAF50"  # Green for tasks

    attachments = [{
        "fallback": f"Task {operation}",
        "pretext": pretext,
        "title": obj.get('title', 'Task Details'),
        "title_link": f"{caseURL}{event.get('rootId')}/tasks",
        "color": color,
        "fields": fields,
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]

    send_to_slack(event, attachments)

def process_event(event):
    """Main event processing function"""
    logger.info("Processing event: %s", event)
    
    try:
        event_type = event.get('objectType', '').lower()
        
        # Route to appropriate handler based on event type
        if event_type == 'observable':
            process_observable_event(event)
        elif event_type == 'alert':
            process_alert_event(event)
        elif event_type == 'case':
            process_case_event(event)
        elif event_type == 'case_task':
            process_task_event(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            # Send a generic formatted message for unknown types
            send_generic_message(event)
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        # Send error notification to Slack
        send_error_notification(str(e))

def send_to_slack(event, attachments):
    """Send formatted message to Slack"""
    slack_message = {
        'username': 'TheHive',
        'icon_emoji': ':honeybee:',
        'channel': slackChannel,
        'attachments': attachments
    }

    try:
        response = requests.post(hookURL, json=slack_message)
        response.raise_for_status()
        logger.info("Message posted to %s", slack_message['channel'])
    except requests.RequestException as e:
        logger.error(f"Failed to send message to Slack: {str(e)}")
        raise

def send_generic_message(event):
    """Handle unknown event types"""
    attachments = [{
        "fallback": "TheHive Event",
        "pretext": "📌 TheHive Event",
        "title": f"Event Type: {event.get('objectType', 'Unknown')}",
        "color": "#9E9E9E",  # Grey for generic events
        "fields": [
            add_object("Operation", event.get('operation', 'Unknown'), True),
            add_object("Details", json.dumps(event.get('object', {}), indent=2), False)
        ],
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]
    
    send_to_slack(event, attachments)

def send_error_notification(error_message):
    """Send error notification to Slack"""
    attachments = [{
        "fallback": "Error Processing Event",
        "pretext": "⚠ Error Processing TheHive Event",
        "title": "Error Details",
        "color": "#FF5722",  # Red for errors
        "fields": [
            add_object("Error", error_message, False)
        ],
        "footer": orgName,
        "footer_icon": orgIcon,
        "ts": int(time.time())
    }]
    
    try:
        slack_message = {
            'username': 'TheHive',
            'icon_emoji': ':warning:',
            'channel': slackChannel,
            'attachments': attachments
        }
        requests.post(hookURL, json=slack_message)
    except Exception as e:
        logger.error(f"Failed to send error notification: {str(e)}")

# Flask app setup
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for TheHive"""
    try:
        if not request.is_json:
            return jsonify({'status': 'error', 'message': 'Content-Type must be application/json'}), 400
            
        event = request.get_json()
        process_event(event)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
