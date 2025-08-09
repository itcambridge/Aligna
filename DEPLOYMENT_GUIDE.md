# Multi-Tenant CV Generator Deployment Guide

This guide covers deploying the Grounded CV Generator as a production-ready multi-tenant SaaS application on Linode with Supabase authentication.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    Supabase     │    │     Qdrant      │
│   Web App       │◄──►│  Authentication │    │   Vector DB     │
│  (Port 8501)    │    │   & User Mgmt   │    │  (Port 6333)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         └──────────────────────────────────────────────┘
                    User-Specific Collections
```

## 📋 Prerequisites

### 1. Linode Server
- **Recommended**: Linode 4GB (Nanode 1GB minimum for testing)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: At least 25GB SSD

### 2. Supabase Project
- Create account at [supabase.com](https://supabase.com)
- Create new project
- Note down: Project URL, Anon Key, Service Key

### 3. Domain & SSL (Optional but Recommended)
- Domain name pointing to your Linode server
- Let's Encrypt SSL certificate

## 🚀 Step-by-Step Deployment

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and pip
sudo apt install python3.11 python3.11-pip python3.11-venv -y

# Install system dependencies
sudo apt install git nginx certbot python3-certbot-nginx -y

# Create application user
sudo useradd -m -s /bin/bash cvgen
sudo usermod -aG sudo cvgen
```

### Step 2: Application Deployment

```bash
# Switch to application user
sudo su - cvgen

# Clone repository
git clone https://github.com/your-username/grounded-cv-generator.git
cd grounded-cv-generator

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp env.example .env
```

### Step 3: Environment Configuration

Edit `.env` file with your production values:

```bash
nano .env
```

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key

# Qdrant Configuration (local installation)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-secure-qdrant-key

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Application Configuration
ENVIRONMENT=production
ORCHESTRATOR=langchain
LOG_LEVEL=INFO
```

### Step 4: Qdrant Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker cvgen

# Logout and login again for docker group to take effect
exit
sudo su - cvgen

# Run Qdrant container
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  -e QDRANT__SERVICE__HTTP_PORT=6333 \
  -e QDRANT__SERVICE__API_KEY=your-secure-qdrant-key \
  --restart unless-stopped \
  qdrant/qdrant:latest
```

### Step 5: Supabase Setup

1. **Create Authentication Tables** (if needed):
```sql
-- Supabase automatically creates auth.users table
-- You can add custom user profiles if needed

CREATE TABLE public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  subscription_tier TEXT DEFAULT 'free',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policy for users to access their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
  FOR UPDATE USING (auth.uid() = id);
```

2. **Configure Authentication Settings**:
   - Go to Authentication > Settings in Supabase dashboard
   - Enable email confirmation (recommended for production)
   - Set up email templates
   - Configure redirect URLs

### Step 6: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/cvgen
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support for Streamlit
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cvgen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: SSL Certificate (Let's Encrypt)

```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 8: Systemd Service

Create a systemd service for the Streamlit app:

```bash
sudo nano /etc/systemd/system/cvgen.service
```

```ini
[Unit]
Description=Grounded CV Generator
After=network.target

[Service]
Type=simple
User=cvgen
WorkingDirectory=/home/cvgen/grounded-cv-generator
Environment=PATH=/home/cvgen/grounded-cv-generator/venv/bin
ExecStart=/home/cvgen/grounded-cv-generator/venv/bin/streamlit run web_app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cvgen
sudo systemctl start cvgen

# Check status
sudo systemctl status cvgen
```

### Step 9: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 6333  # Qdrant (if accessing externally)
sudo ufw enable
```

## 🔧 Production Optimizations

### 1. Database Connection Pooling

For high-traffic applications, consider implementing connection pooling for Qdrant:

```python
# utils/connection_pool.py
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.http import models

class QdrantConnectionPool:
    def __init__(self, url, api_key, pool_size=10):
        self.url = url
        self.api_key = api_key
        self.pool_size = pool_size
        self._pool = []
        self._initialize_pool()
    
    def _initialize_pool(self):
        for _ in range(self.pool_size):
            client = QdrantClient(url=self.url, api_key=self.api_key)
            self._pool.append(client)
    
    def get_client(self):
        if self._pool:
            return self._pool.pop()
        else:
            return QdrantClient(url=self.url, api_key=self.api_key)
    
    def return_client(self, client):
        if len(self._pool) < self.pool_size:
            self._pool.append(client)
```

### 2. Caching Layer

Implement Redis caching for frequently accessed data:

```bash
# Install Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
```

```python
# utils/cache.py
import redis
import json
from typing import Any, Optional

class CacheManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
    
    def get(self, key: str) -> Optional[Any]:
        value = self.redis_client.get(key)
        return json.loads(value) if value else None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis_client.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        self.redis_client.delete(key)
```

### 3. Monitoring & Logging

Set up comprehensive monitoring:

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Set up log rotation
sudo nano /etc/logrotate.d/cvgen
```

```
/home/cvgen/grounded-cv-generator/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 cvgen cvgen
    postrotate
        systemctl reload cvgen
    endscript
}
```

### 4. Backup Strategy

```bash
# Create backup script
nano /home/cvgen/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/cvgen/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Qdrant data
docker exec qdrant tar czf - /qdrant/storage > $BACKUP_DIR/qdrant_$DATE.tar.gz

# Backup application code
tar czf $BACKUP_DIR/app_$DATE.tar.gz /home/cvgen/grounded-cv-generator

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable and add to crontab
chmod +x /home/cvgen/backup.sh
crontab -e
# Add: 0 2 * * * /home/cvgen/backup.sh
```

## 🔐 Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate keys regularly

### 2. Network Security
- Use firewall to restrict access
- Consider VPN for administrative access
- Monitor access logs regularly

### 3. Application Security
- Implement rate limiting
- Validate all user inputs
- Use HTTPS everywhere
- Regular security updates

### 4. Data Privacy
- Each user's data is isolated in separate Qdrant collections
- Implement data retention policies
- Provide data export/deletion capabilities

## 📊 Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Multiple Streamlit instances
- Shared Qdrant cluster
- Centralized session storage (Redis)

### Vertical Scaling
- Monitor resource usage
- Upgrade server specs as needed
- Optimize database queries
- Implement caching strategies

## 🚨 Troubleshooting

### Common Issues

1. **Streamlit not starting**:
```bash
# Check logs
sudo journalctl -u cvgen -f

# Check port availability
sudo netstat -tlnp | grep 8501
```

2. **Qdrant connection issues**:
```bash
# Check Qdrant container
docker logs qdrant

# Test connection
curl http://localhost:6333/
```

3. **Supabase authentication errors**:
- Verify environment variables
- Check Supabase project settings
- Review authentication policies

### Performance Monitoring

```bash
# Monitor system resources
htop

# Monitor disk usage
df -h

# Monitor network
nethogs

# Check application logs
tail -f /var/log/nginx/access.log
sudo journalctl -u cvgen -f
```

## 📈 Production Checklist

- [ ] Server hardened and updated
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Environment variables secured
- [ ] Database optimized
- [ ] Caching implemented
- [ ] Rate limiting configured
- [ ] Error tracking set up
- [ ] Documentation updated
- [ ] Team access configured

## 🎯 Next Steps

1. **User Management**: Implement admin dashboard for user management
2. **Analytics**: Add usage analytics and reporting
3. **API**: Create REST API for programmatic access
4. **Mobile**: Consider mobile-responsive design improvements
5. **Integrations**: Add integrations with job boards and ATS systems

This deployment guide provides a solid foundation for running the Grounded CV Generator in production. Adjust configurations based on your specific requirements and scale.
