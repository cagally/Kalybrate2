# Metabase Enterprise Deployment Guide

## Overview

This guide covers comprehensive deployment strategies for Metabase in enterprise environments, focusing on scalability, security, and reliability.

## Deployment Options

### 1. Docker Deployment

#### Basic Docker Setup
\`\`\`bash
docker run -d -p 3000:3000   -v /path/to/metabase-data:/metabase-data   -e "MB_DB_TYPE=postgres"   -e "MB_DB_DBNAME=metabase"   -e "MB_DB_HOST=your-postgres-host"   metabase/metabase
\`\`\`

#### Docker Compose for Enterprise
\`\`\`yaml
version: '3.8'
services:
  metabase:
    image: metabase/metabase-enterprise
    ports:
      - "3000:3000"
    environment:
      - MB_DB_TYPE=postgres
      - MB_DB_HOST=postgres
      - MB_ENCRYPTION_SECRET_KEY=${ENCRYPTION_KEY}
    volumes:
      - metabase-data:/metabase-data
    depends_on:
      - postgres

  postgres:
    image: postgres:13
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  metabase-data:
  postgres-data:
\`\`\`

### 2. Kubernetes Deployment

#### Kubernetes Deployment Manifest
\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metabase
spec:
  replicas: 3
  selector:
    matchLabels:
      app: metabase
  template:
    metadata:
      labels:
        app: metabase
    spec:
      containers:
      - name: metabase
        image: metabase/metabase-enterprise
        ports:
        - containerPort: 3000
        env:
        - name: MB_DB_TYPE
          value: postgres
        - name: MB_DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: db-host
\`\`\`

### 3. Bare Metal Installation

#### Manual Installation Steps
1. Download Metabase JAR
\`\`\`bash
wget https://downloads.metabase.com/enterprise/metabase.jar
\`\`\`

2. Configure Environment
\`\`\`bash
export MB_DB_TYPE=postgres
export MB_DB_HOST=your-postgres-server
export MB_ENCRYPTION_SECRET_KEY=your-secret-key
\`\`\`

3. Run Metabase
\`\`\`bash
java -jar metabase.jar
\`\`\`

## Load Balancing

### Nginx Load Balancer Configuration
\`\`\`nginx
upstream metabase_servers {
    server metabase1.example.com:3000;
    server metabase2.example.com:3000;
    server metabase3.example.com:3000;
}

server {
    listen 80;
    server_name metabase.example.com;

    location / {
        proxy_pass http://metabase_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
\`\`\`

## SSL Configuration

### Let's Encrypt SSL with Certbot
\`\`\`bash
# Install Certbot
sudo certbot --nginx -d metabase.example.com

# Auto-renew configuration
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer
\`\`\`

## Backup Strategies

### PostgreSQL Backup Script
\`\`\`bash
#!/bin/bash
BACKUP_DIR="/var/backups/metabase"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

pg_dump -h $DB_HOST -U $DB_USER metabase_db >   ${BACKUP_DIR}/metabase_backup_${TIMESTAMP}.sql

# Rotate backups (keep last 7 days)
find ${BACKUP_DIR} -type f -mtime +7 -delete
\`\`\`

## Monitoring Setup

### Prometheus Metrics Configuration
\`\`\`yaml
scrape_configs:
  - job_name: 'metabase'
    static_configs:
    - targets: ['metabase-server:3000']
    metrics_path: '/api/health/prometheus'
\`\`\`

## Security Hardening

### Best Practices
1. Use strong, unique passwords
2. Enable two-factor authentication
3. Limit admin access
4. Use VPN for admin interfaces
5. Regularly update Metabase

### Firewall Configuration
\`\`\`bash
# Restrict access to Metabase
sudo ufw allow from 192.168.1.0/24 to any port 3000
sudo ufw deny to any port 3000
\`\`\`

## Troubleshooting

### Common Issues
- Check logs: `/var/log/metabase/metabase.log`
- Verify database connection
- Ensure correct Java version

## Conclusion

By following these guidelines, you can deploy Metabase securely and efficiently in enterprise environments.
