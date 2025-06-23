#!/bin/bash
# update-bot-ips.sh - Updates Microsoft Bot Service IPs in nginx config
# Sollte als Cron-Job laufen (z.B. wöchentlich)

set -e

# Konfiguration
WORK_DIR="/tmp/bot-ip-update"
NGINX_CONFIG="/etc/nginx/sites-available/teams-bot"
BACKUP_DIR="/etc/nginx/config-backups"
LOG_FILE="/var/log/nginx/bot-ip-update.log"
SERVICE_TAGS_URL="https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_20250616.json"

# Logging Funktion
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fehlerbehandlung
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Prüfe ob als root
if [[ $EUID -ne 0 ]]; then
   error_exit "Dieses Script muss als root ausgeführt werden"
fi

# Erstelle Arbeitsverzeichnis
mkdir -p "$WORK_DIR" || error_exit "Kann Arbeitsverzeichnis nicht erstellen"
mkdir -p "$BACKUP_DIR" || error_exit "Kann Backup-Verzeichnis nicht erstellen"

log "Starting Bot IP update process"

# Download aktuelle Service Tags
log "Downloading latest Microsoft Service Tags..."
cd "$WORK_DIR"

# Versuche Download mit Retry
for i in {1..3}; do
    if wget -q -O ServiceTags_Public.json "$SERVICE_TAGS_URL"; then
        log "Download successful"
        break
    else
        log "Download attempt $i failed"
        if [ $i -eq 3 ]; then
            error_exit "Failed to download Service Tags after 3 attempts"
        fi
        sleep 5
    fi
done

# Validiere JSON
if ! jq empty ServiceTags_Public.json 2>/dev/null; then
    error_exit "Downloaded file is not valid JSON"
fi

# Extrahiere Bot Service IPs
log "Extracting Bot Service IPs..."

# Global Bot Service IPs
jq -r '.values[] | select(.name == "AzureBotService") | .properties.addressPrefixes[]' ServiceTags_Public.json > botservice-global.txt

# Regional Bot Service IPs (Europa)
jq -r '.values[] | select(.name | test("AzureBotService\\.(NorthEurope|WestEurope|GermanyNorth|GermanyWestCentral)")) | .properties.addressPrefixes[]' ServiceTags_Public.json > botservice-europe.txt

# Kombiniere und sortiere
cat botservice-global.txt botservice-europe.txt | sort -u > all-bot-ips.txt

# Zähle IPs
IP_COUNT=$(wc -l < all-bot-ips.txt)
log "Found $IP_COUNT unique Bot Service IPs"

# Validierung - sollten mindestens 50 IPs sein
if [ "$IP_COUNT" -lt 50 ]; then
    error_exit "Unexpectedly low number of IPs ($IP_COUNT). Aborting for safety."
fi

# Erstelle neue nginx geo config
log "Creating new nginx configuration..."

cat > nginx-geo-config.tmp << 'EOF'
# IP Whitelist für Microsoft Bot Service
geo $bot_allowed {
    default 0;
    
    # Lokaler Zugriff für Health Checks
    127.0.0.1 1;
    ::1 1;
    
    # Microsoft Bot Service IPs
EOF

# Füge IPs hinzu
while IFS= read -r ip; do
    echo "    $ip 1;" >> nginx-geo-config.tmp
done < all-bot-ips.txt

echo "}" >> nginx-geo-config.tmp

# Backup aktuelle Config
BACKUP_FILE="$BACKUP_DIR/teams-bot.$(date +%Y%m%d_%H%M%S).backup"
cp "$NGINX_CONFIG" "$BACKUP_FILE" || error_exit "Failed to backup current config"
log "Backed up current config to $BACKUP_FILE"

# Erstelle neue Config durch Ersetzen des geo Blocks
log "Updating nginx configuration..."

# Extrahiere Config vor dem geo Block
awk '/^# IP Whitelist/{exit}1' "$NGINX_CONFIG" > new-config.tmp

# Füge neuen geo Block hinzu
cat nginx-geo-config.tmp >> new-config.tmp

# Füge Rest der Config hinzu (nach dem geo Block)
awk '/^}$/{f=1;next} f&&/^# HTTP Server/{print; f=0} f==0' "$NGINX_CONFIG" >> new-config.tmp

# Teste neue Config
cp new-config.tmp "$NGINX_CONFIG.test"
if nginx -t -c "$NGINX_CONFIG.test" 2>/dev/null; then
    log "New configuration syntax is valid"
else
    error_exit "New configuration has syntax errors"
fi

# Ersetze Config
mv new-config.tmp "$NGINX_CONFIG" || error_exit "Failed to update configuration"

# Teste nginx config nochmal
if ! nginx -t; then
    log "ERROR: Nginx configuration test failed, rolling back..."
    cp "$BACKUP_FILE" "$NGINX_CONFIG"
    error_exit "Rolled back to previous configuration"
fi

# Reload nginx
log "Reloading nginx..."
if systemctl reload nginx; then
    log "Nginx reloaded successfully"
else
    log "ERROR: Failed to reload nginx, rolling back..."
    cp "$BACKUP_FILE" "$NGINX_CONFIG"
    systemctl reload nginx
    error_exit "Rolled back and reloaded with previous configuration"
fi

# Aufräumen
rm -rf "$WORK_DIR"

# Behalte nur die letzten 10 Backups
log "Cleaning up old backups..."
ls -t "$BACKUP_DIR"/teams-bot.*.backup | tail -n +11 | xargs -r rm

log "Bot IP update completed successfully!"
log "Updated with $IP_COUNT IPs"

# Optional: Sende Benachrichtigung
# echo "Bot IPs updated successfully with $IP_COUNT IPs" | mail -s "Bot IP Update" admin@example.com

exit 0