# TheHive-Slack Webhook Integration Installation Guide

An integration script for TheHive webhook to publish notifications to Slack Channels, such as mobile which can be handy. 

# Installations and Configurations Overview

## 1. Preparation
### 1.1 Components
- My existing SOC build consist of a VM running TheHive, Cortex, MISP, and all supporting software and Databases using Docker-Compose. So it is logical that this integration code is also running as part of the Docker-compose construct.
- TheHive's built-in webhook sender
- Python Flask webhook server
- Slack incoming webhook

### 1.2 Information Flow
```
TheHive --> Webhook Server --> Slack Notifications
```

### 1.3 Directory Structure
```
/home/user/soc/webhook/
├── Dockerfile                # Container build instructions
├── requirements.txt          # Python dependencies
├── thehive-slack-webhook.py  # Main webhook script
├── .env                      # Environment variables
└── logs/                     # Log directory
```

## 2. Prerequisites
- Docker and Docker Compose installed
- TheHive is running and functional
- Slack workspace with permissions to add integrations
- Access to TheHive's web interface

## 3. Installation Steps

### 3.1 Create Directory Structure
```bash
mkdir -p /home/user/soc/webhook/logs   ## SOC is TheHive working diectory
cd /home/user/soc/webhook
```

### 3.2 Create Requirements File (requirements.txt)
```txt
flask==3.0.0
requests==2.31.0
python-dateutil==2.8.2
```

### 3.3 Create Dockerfile
- refer to the Dockerfile published.

### 3.4 Create Environment File (.env)
- refer to the .env published.

### 3.5 Add to Docker Compose

Add this section to your existing docker-compose.yml:
```yaml
  webhook:
    container_name: soc_webhook_1
    build:
      context: ./webhook
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - ./webhook/.env    # Load all environment variables from .env file   
    ports:
      - "5000:5000"       # adjust according your actual docker port used.
    volumes:
      - ./webhook/logs:/app/logs
    networks:
      - SOC_NET           # adjust according to your actual docker-compose network name
```

## 4. Slack Configuration

### 4.1 Create Slack App
1. Go to api.slack.com/apps
2. Create New App
3. Enable Incoming Webhooks
4. Create a webhook for your channel
5. Copy webhook URL to .env file

### 4.2 Create Channel
1. Create #soc-alert channel in Slack
2. Set notification preferences:
   - Desktop: Mentions & DMs only
   - Mobile: Critical & High severity only

## 5. TheHive Configuration

### 5.1 Configure Webhook
1. Go to Organization → Endpoints
2. Click + to add new endpoint
3. Fill in:
   - Name: thehive-slack-webhook
   - Type: Webhook
   - URL/TOKEN: http://soc_webhook_1:5000/webhook

## 6. Alert Configuration

### 6.1 Severity Levels

```python
colors = {
    1: "#97A2A0",  # Low - grey
    2: "#2684FF",  # Medium - blue
    3: "#FFC107",  # High - yellow
    4: "#FF5722"   # Critical - red
}
```

### 6.2 Mobile Alert Filtering Recommendations

- Only forward Critical (4) and High (3) to mobile
- Keep all alerts in Slack channel
- Configure notification preferences in Slack app

### 6.3 TheHive notifications settings

TheHive offers two liscences; The free version has one webhook function built-in. This is what we are leveraging to turn this into a slack notiifcation channel.
In the TheHive menu, enable the webhook function and configure the URL/Token as follows:

http://soc_webhook_1:5000/webhook
- soc_webhook_1 is the docker name
- default webhook port number is 5000

<img src="https://github.com/bluefightred/TheHive_Slack_Notifications/blob/main/image/Pasted%20image%2020241126204115.png" alt="Sample Image" style="width:50%; height:auto;">


Once the notification channel is created, set up the notification filter to suit your use case. Reference as follows
```
{
    "_and": [
        {
            "_is": {
                "objectType": "Alert"
            }
        },
        {
            "_gte": {
                "object.severity": 3
            }
        }
    ]
}
```
<img src="https://github.com/bluefightred/TheHive_Slack_Notifications/blob/main/image/Pasted%20image%2020241126204151.png" alt="Sample Image" style="width:30%; height:auto;">

## Sample screen shot of Slack Notification on Mobile

<img src="https://github.com/bluefightred/TheHive_Slack_Notifications/blob/main/image/IMG_2545.PNG" alt="Sample Image" style="width:30%; height:auto;">

# Contributors

This TheHive Slack code is forked from ReconInfoSec/thehive-slack-webhook. Huge thanks to ReconInfoSec.












