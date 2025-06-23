# Teams Assistant Bot

Ein KI-gestützter Microsoft Teams Bot, der als persönlicher HR-Assistent fungiert und Mitarbeitern in privaten 1:1-Chats zur Verfügung steht.

## 🎯 Überblick

Der Teams Assistant Bot ist eine Python-basierte Anwendung, die die Microsoft Bot Framework SDK mit der OpenAI Assistant API kombiniert. Der Bot wurde speziell für HR-Support entwickelt und bietet Mitarbeitern einen intelligenten, datenschutzkonformen Assistenten direkt in Microsoft Teams.

### Hauptfunktionen

- **1:1 Konversationen**: Persönliche Unterstützung durch private Teams-Chats
- **KI-Integration**: Nutzt OpenAI's Assistant API für intelligente Antworten
- **Kontextbewusstsein**: Behält Gesprächskontext über mehrere Nachrichten
- **DSGVO-konform**: Keine Protokollierung von Benutzerinhalten
- **Multi-Tenant-fähig**: Unterstützt mehrere Azure AD Tenants
- **Deutsche Sprache**: Vollständig auf Deutsch lokalisiert

## 🛠️ Technologie-Stack

- **Python 3.11**
- **Microsoft Bot Framework SDK** (v4.14.8)
- **FastAPI** (v0.109.0) - Web Framework
- **OpenAI SDK** (v1.35.0) - Assistant API v2
- **Docker** & **Docker Compose** - Containerisierung
- **Uvicorn** - ASGI Server

## 📋 Voraussetzungen

- Python 3.11+
- Docker und Docker Compose
- Microsoft Azure Konto mit Bot Service
- OpenAI API Zugang mit Assistant API
- Microsoft Teams Zugang

## 🚀 Installation & Setup

### 1. Repository klonen

```bash
git clone <repository-url>
cd teams-assistant-bot
```

### 2. Azure Bot erstellen

1. Erstellen Sie einen neuen Bot im [Azure Portal](https://portal.azure.com)
2. Notieren Sie sich die `App ID` und das `App Password`
3. Konfigurieren Sie den Messaging Endpoint: `https://YOUR-DOMAIN/api/messages`

### 3. OpenAI Assistant erstellen

1. Gehen Sie zu [OpenAI Platform](https://platform.openai.com)
2. Erstellen Sie einen neuen Assistant
3. Notieren Sie sich die `Assistant ID`
4. Generieren Sie einen API Key

### 4. Umgebungsvariablen konfigurieren

Kopieren Sie `.env.example` zu `.env` und füllen Sie die Werte aus:

```bash
cp .env.example .env
```

Bearbeiten Sie `.env`:

```env
# Azure Bot Configuration
APP_ID=ihre-azure-app-id
APP_PASSWORD=ihr-azure-app-password

# OpenAI Configuration
OPENAI_API_KEY=ihr-openai-api-key
ASSISTANT_ID=ihre-assistant-id

# Server Configuration
PORT=3978
LOG_LEVEL=INFO

# Optional: Tenant-Einschränkungen (kommasepariert)
ALLOWED_TENANT_IDS=tenant-id-1,tenant-id-2

# Optional: Monitoring
HEALTH_CHECK_INTERVAL=30
```

### 5. Lokale Entwicklung

#### Mit Python Virtual Environment:

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Bot starten
python src/bot.py
```

#### Mit Docker:

```bash
# Container bauen und starten
docker-compose up --build
```

### 6. Teams App installieren

1. Navigieren Sie zum `teams/` Ordner
2. Erstellen Sie ein ZIP-Archiv mit:
   - `manifest.json`
   - `color.png`
   - `outline.png`
3. In Teams:
   - Gehen Sie zu "Apps" → "Apps verwalten" → "App hochladen"
   - Laden Sie die ZIP-Datei hoch
   - Installieren Sie die App für sich selbst oder Ihre Organisation

## 📁 Projektstruktur

```
teams-assistant-bot/
├── src/                      # Quellcode
│   ├── bot.py               # Haupt-Bot-Anwendung & FastAPI Server
│   ├── config.py            # Konfigurationsverwaltung
│   ├── assistant_manager.py # OpenAI Assistant API Integration
│   └── teams_handler.py     # Teams-spezifische Bot-Logik
├── teams/                   # Teams App-Paket
│   ├── manifest.json        # Teams App-Manifest
│   ├── color.png           # App-Icon (farbig)
│   └── outline.png         # App-Icon (Umriss)
├── scripts/                 # Deployment-Skripte
│   ├── deploy.sh           # Deployment-Automatisierung
│   ├── health_check.sh     # Health-Monitoring
│   └── update_bot_ips_script.sh # Microsoft Bot Service IP-Updates
├── docker-compose.yml       # Docker-Orchestrierung
├── Dockerfile              # Container-Definition
├── requirements.txt        # Python-Abhängigkeiten
├── .env.example           # Umgebungsvariablen-Vorlage
└── README.md              # Diese Datei
```

## 🔧 Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Erforderlich | Standard |
|----------|--------------|--------------|----------|
| `APP_ID` | Azure Bot Application ID | ✅ | - |
| `APP_PASSWORD` | Azure Bot Application Password | ✅ | - |
| `OPENAI_API_KEY` | OpenAI API Schlüssel | ✅ | - |
| `ASSISTANT_ID` | OpenAI Assistant ID | ✅ | - |
| `PORT` | Server Port | ❌ | 3978 |
| `LOG_LEVEL` | Logging Level (DEBUG, INFO, WARNING, ERROR) | ❌ | INFO |
| `ALLOWED_TENANT_IDS` | Kommaseparierte Liste erlaubter Tenant IDs | ❌ | - |
| `HEALTH_CHECK_INTERVAL` | Health Check Intervall in Sekunden | ❌ | 30 |

### Teams App Manifest

Das Manifest (`teams/manifest.json`) definiert:
- Bot ID: `cb86ae26-54e5-4368-8759-0e8ce43246f9`
- Verfügbare Befehle: "Hilfe", "Krankmeldung"
- Berechtigungen: Identity, MessageTeamMembers
- Scope: Nur persönliche Chats

## 💬 Verwendung

### Bot-Befehle

Der Bot unterstützt folgende Befehle:

- **Hilfe**: Zeigt verfügbare Befehle und Informationen
- **Krankmeldung**: Informationen zur Krankmeldung

### Interaktion

1. Öffnen Sie einen Chat mit dem HR Assistant in Teams
2. Senden Sie Ihre Frage oder verwenden Sie einen Befehl
3. Der Bot zeigt Tipp-Indikatoren während der Verarbeitung
4. Erhalten Sie eine KI-gestützte Antwort

## 🚢 Deployment

### Docker Deployment

```bash
# Build und Start
docker-compose up -d --build

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

### Deployment-Skript

Nutzen Sie das bereitgestellte Deployment-Skript:

```bash
./scripts/deploy.sh
```

### Health Checks

Der Bot bietet einen Health-Endpoint:

```bash
curl http://localhost:3978/health
```

Automatisiertes Health-Monitoring:

```bash
./scripts/health_check.sh
```

## 🔒 Sicherheit & Datenschutz

### Implementierte Sicherheitsmaßnahmen

- **JWT-Token-Validierung**: Alle Teams-Anfragen werden authentifiziert
- **Tenant-Filterung**: Optional Beschränkung auf spezifische Azure AD Tenants
- **IP-Whitelist**: Nginx konfiguriert mit Microsoft Bot Service IP-Bereichen
- **Automatische IP-Updates**: Wöchentliche Aktualisierung der Bot Service IPs
- **Keine Nachrichtenprotokollierung**: Benutzerinhalte werden nicht geloggt (DSGVO-konform)
- **Container-Sicherheit**: Läuft als non-root User
- **HTTPS-Only**: Für Produktionsumgebungen empfohlen

### Microsoft Bot Service IP-Whitelist

Das Projekt enthält ein automatisiertes System zur Verwaltung der Microsoft Bot Service IP-Adressen in der Nginx-Konfiguration:

#### Automatische IP-Updates mit `update-bot-ips.sh`

Das Script `scripts/update-bot-ips.sh` lädt automatisch die aktuellen Microsoft Service Tags herunter und aktualisiert die Nginx-Konfiguration mit den neuesten Bot Service IP-Bereichen.

**Funktionen:**
- Lädt die aktuellen Microsoft Service Tags von der offiziellen Microsoft-URL
- Extrahiert globale und europäische Bot Service IP-Bereiche
- Erstellt automatisch Backups der bestehenden Nginx-Konfiguration
- Validiert die neue Konfiguration vor der Anwendung
- Führt automatisches Rollback bei Fehlern durch
- Bereinigt alte Backup-Dateien automatisch

#### Installation des IP-Update-Scripts

**1. Script-Berechtigungen setzen:**

```bash
chmod +x scripts/update-bot-ips.sh
```

**2. Abhängigkeiten installieren:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install wget jq nginx

# CentOS/RHEL
sudo yum install wget jq nginx
```

**3. Nginx-Konfiguration vorbereiten:**

Stellen Sie sicher, dass Ihre Nginx-Konfiguration (`/etc/nginx/sites-available/teams-bot`) den IP-Whitelist-Block enthält:

```nginx
# IP Whitelist für Microsoft Bot Service
geo $bot_allowed {
    default 0;
    
    # Lokaler Zugriff für Health Checks
    127.0.0.1 1;
    ::1 1;
    
    # Microsoft Bot Service IPs werden hier automatisch eingefügt
}

# HTTP Server
server {
    listen 80;
    server_name your-domain.com;
    
    # Nur Bot Service IPs erlauben
    if ($bot_allowed = 0) {
        return 403;
    }
    
    location /api/messages {
        proxy_pass http://localhost:3978;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**4. Erste manuelle Ausführung:**

```bash
sudo ./scripts/update-bot-ips.sh
```

#### Cronjob für automatische Updates einrichten

**1. Cronjob als root erstellen:**

```bash
sudo crontab -e
```

**2. Wöchentlichen Cronjob hinzufügen:**

```bash
# Jeden Sonntag um 3:00 Uhr - Microsoft Bot Service IPs aktualisieren
0 3 * * 0 /path/to/your/project/scripts/update-bot-ips.sh >> /var/log/nginx/bot-ip-cron.log 2>&1
```

**3. Alternativer monatlicher Cronjob:**

```bash
# Am ersten Tag des Monats um 3:00 Uhr
0 3 1 * * /path/to/your/project/scripts/update-bot-ips.sh >> /var/log/nginx/bot-ip-cron.log 2>&1
```

**4. Cronjob-Status prüfen:**

```bash
# Aktive Cronjobs anzeigen
sudo crontab -l

# Log-Datei überwachen
sudo tail -f /var/log/nginx/bot-ip-update.log
```

#### Script-Konfiguration anpassen

Das Script kann durch Bearbeitung der Konfigurationsvariablen am Anfang der Datei angepasst werden:

```bash
# Pfad zur Nginx-Konfigurationsdatei
NGINX_CONFIG="/etc/nginx/sites-available/teams-bot"

# Backup-Verzeichnis
BACKUP_DIR="/etc/nginx/config-backups"

# Log-Datei
LOG_FILE="/var/log/nginx/bot-ip-update.log"

# URL für Microsoft Service Tags (wird regelmäßig aktualisiert)
SERVICE_TAGS_URL="https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_20250616.json"
```

#### Monitoring und Troubleshooting

**Log-Dateien überwachen:**

```bash
# Script-Logs anzeigen
sudo tail -f /var/log/nginx/bot-ip-update.log

# Nginx-Fehler-Logs
sudo tail -f /var/log/nginx/error.log
```

**Manuelle Validierung:**

```bash
# Nginx-Konfiguration testen
sudo nginx -t

# Aktuelle IP-Anzahl prüfen
grep -c "1;" /etc/nginx/sites-available/teams-bot
```

**Backup wiederherstellen:**

```bash
# Verfügbare Backups anzeigen
ls -la /etc/nginx/config-backups/

# Backup wiederherstellen
sudo cp /etc/nginx/config-backups/teams-bot.YYYYMMDD_HHMMSS.backup /etc/nginx/sites-available/teams-bot
sudo nginx -t && sudo systemctl reload nginx
```

### Datenschutz-Hinweise

- Benutzer-IDs werden zu Debug-Zwecken protokolliert
- Nachrichteninhalte werden NICHT protokolliert
- Konversationskontext wird nur im Speicher gehalten
- Bei Neustart gehen Konversationskontexte verloren

## 🐛 Fehlerbehebung

### Häufige Probleme

1. **Bot antwortet nicht**
   - Prüfen Sie die Azure Bot Konfiguration
   - Verifizieren Sie den Messaging Endpoint
   - Kontrollieren Sie die Logs: `docker-compose logs`

2. **OpenAI API Fehler**
   - Überprüfen Sie den API Key
   - Verifizieren Sie die Assistant ID
   - Prüfen Sie das API-Kontingent

3. **Teams App Installation schlägt fehl**
   - Validieren Sie das Manifest
   - Stellen Sie sicher, dass die Bot ID übereinstimmt
   - Prüfen Sie die Berechtigungen in Teams

### Debug-Modus

Aktivieren Sie detailliertes Logging:

```env
LOG_LEVEL=DEBUG
```

## 📊 Monitoring

### Verfügbare Metriken

- Request Counter: `/health` endpoint
- Message Counter: In Logs verfügbar
- Response Times: In Debug-Logs
- Error Rates: Über Log-Analyse

### Log-Format

```
2024-01-15 10:30:45 - INFO - Received message from user: user123
2024-01-15 10:30:46 - INFO - Processing with OpenAI Assistant
2024-01-15 10:30:48 - INFO - Sent response to user
```

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Pushen Sie zum Branch
5. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt unterliegt der Lizenz von IFP Labs GmbH.

## 👥 Support

Bei Fragen oder Problemen:
- Erstellen Sie ein Issue im Repository
- Kontaktieren Sie das Entwicklungsteam
- Dokumentation: [IFP Labs](https://www.ifp-labs.com)

## 🔄 Versionshistorie

### Version 1.1
- DSGVO-konforme Nachrichtenbehandlung
- Verbesserte Fehlerbehandlung
- Optimierte Logging-Funktionalität

### Version 1.0
- Initiale Veröffentlichung
- Grundlegende Teams Bot Funktionalität
- OpenAI Assistant Integration