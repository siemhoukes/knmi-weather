# Deploy op de Raspberry Pi (weather.siem.codes)

De dashboard-site is volledig statisch: nginx serveert `dashboard/`, een
systemd timer ververst de data dagelijks, en cloudflared routeert
`weather.siem.codes` naar nginx — zelfde patroon als de andere apps.

Vervang `<pi-user>`, `<pi-host>` en `<poort>` hieronder door je eigen waarden
(`<poort>`: een vrije lokale poort voor nginx).

## 1. Clone + data bouwen

```bash
ssh <pi-user>@<pi-host>
git clone https://github.com/siemhoukes/knmi-weather.git ~/personal/knmi
cd ~/personal/knmi
python3 -m venv .venv && .venv/bin/pip install pandas requests
.venv/bin/python scripts/build_data.py     # vult dashboard/data/ (± 1 min)
```

## 2. Dagelijkse data-refresh (systemd timer)

```bash
sed "s|<pi-user>|$USER|g" services/knmi-data-refresh.service | sudo tee /etc/systemd/system/knmi-data-refresh.service >/dev/null
sudo cp services/knmi-data-refresh.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now knmi-data-refresh.timer
systemctl list-timers knmi-data-refresh.timer --no-pager   # check volgende run
```

## 3. Nginx (statisch, lokale poort)

`/etc/nginx/sites-available/knmi-weather`:

```nginx
server {
    listen <poort>;
    server_name weather.siem.codes;
    root /home/<pi-user>/personal/knmi/dashboard;
    index index.html;
    gzip on;
    gzip_types application/json text/html;
    location /data/ {
        expires 1h;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/knmi-weather /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
curl -sS http://127.0.0.1:<poort>/ | head -3    # moet HTML geven
```

## 4. Cloudflare Tunnel

Voeg in `/etc/cloudflared/config.yml` een ingress-regel toe (boven de
catch-all):

```yaml
  - hostname: weather.siem.codes
    service: http://localhost:<poort>
```

```bash
cloudflared tunnel route dns <tunnel-naam> weather.siem.codes   # maakt het DNS record
sudo systemctl restart cloudflared
```

Daarna is https://weather.siem.codes live.

## Updaten na een code-wijziging

```bash
ssh <pi-user>@<pi-host> "cd ~/personal/knmi && git pull --ff-only && sudo systemctl start knmi-data-refresh.service"
```

(Geen app-restart nodig — de site is statisch.)

## Alternatief: GitHub Pages

De repo kan dezelfde site ook naar GitHub Pages deployen (`gh-pages` branch,
dagelijks ververst door GitHub Actions); die workflow staat nu uit, zet hem
eerst weer aan. Wil je de Pi er niet tussen hebben, maak dan een DNS record in
Cloudflare:
`CNAME weather → siemhoukes.github.io` (DNS only). Gebruik één van de twee,
niet allebei.
