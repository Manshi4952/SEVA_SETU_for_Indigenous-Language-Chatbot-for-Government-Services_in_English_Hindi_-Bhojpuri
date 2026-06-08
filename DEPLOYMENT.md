# 🚀 SevaSetu – Deployment Guide

## Option 1: Docker Compose (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- A Groq API key

### Steps

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env: set GROQ_API_KEY and SECRET_KEY

# 2. Build and start
docker-compose up --build -d

# 3. View logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

App will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Option 2: Manual (VPS / Cloud VM)

### Backend (systemd service)

```bash
# Install dependencies
cd /opt/sevasetu/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/sevasetu-backend.service
```

Paste:
```ini
[Unit]
Description=SevaSetu Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/sevasetu/backend
Environment="PATH=/opt/sevasetu/backend/venv/bin"
ExecStart=/opt/sevasetu/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sevasetu-backend
sudo systemctl start sevasetu-backend
```

### Frontend (nginx)

```bash
cd /opt/sevasetu/frontend
npm install
npm run build

# Serve with nginx
sudo cp -r dist /var/www/sevasetu
```

`/etc/nginx/sites-available/sevasetu`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/sevasetu;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sevasetu /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Production Checklist

- [ ] `SECRET_KEY` is a strong random string (not the default)
- [ ] `DEBUG=False` in `.env`
- [ ] `ALLOWED_ORIGINS` set to your actual domain
- [ ] HTTPS configured (use Certbot / Let's Encrypt)
- [ ] Regular database backups (`sevasetu.db`)
- [ ] Groq API key stored securely (not in git)

---

## Environment Variables for Production

```env
DATABASE_URL=sqlite:///./sevasetu.db
SECRET_KEY=<strong-random-64-char-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=https://yourdomain.com
GROQ_API_KEY=gsk_your_key
LLM_MODEL=llama-3.3-70b-versatile
DEBUG=False
```
