# Deploy op de Raspberry Pi (weather.siem.codes)

De dashboard-site is volledig statisch: nginx serveert `dashboard/`, een
systemd timer ververst de data dagelijks, en cloudflared routeert
`weather.siem.codes` naar nginx — zelfde patroon als de andere apps.

## 1. Clone + data bouwen

```bash
ssh sausje@raspberrypi
git clone https://github.com/siemhoukes/knmi-weather.git ~/personal/knmi
cd ~/personal/knmi
python3 -m venv .venv && .venv/bin/pip install pandas requests
.venv/bin/python scripts/build_data.py     # vult dashboard/data/ (± 1 min)
```

## 2. Dagelijkse data-refresh (systemd timer)

```bash
sudo cp services/knmi-data-refresh.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now knmi-data-refresh.timer
systemctl list-timers knmi-data-refresh.timer --no-pager   # check volgende run
```

## 3. Nginx (statisch, poort 8093)

`/etc/nginx/sites-available/knmi-weather`:

```nginx
server {
    listen 8093;
    server_name weather.siem.codes;
    root /home/sausje/personal/knmi/dashboard;
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
curl -sS http://127.0.0.1:8093/ | head -3    # moet HTML geven
```

## 4. Cloudflare Tunnel

Voeg in `/etc/cloudflared/config.yml` een ingress-regel toe (boven de
catch-all):

```yaml
  - hostname: weather.siem.codes
    service: http://localhost:8093
```

```bash
cloudflared tunnel route dns <tunnel-naam> weather.siem.codes   # maakt het DNS record
sudo systemctl restart cloudflared
```

Daarna is https://weather.siem.codes live.

## Updaten na een code-wijziging

```bash
ssh sausje@raspberrypi "cd ~/personal/knmi && git pull --ff-only && sudo systemctl start knmi-data-refresh.service"
```

(Geen app-restart nodig — de site is statisch.)

## Alternatief: GitHub Pages

De repo deployt dezelfde site ook automatisch naar GitHub Pages
(`gh-pages` branch, dagelijks ververst door GitHub Actions). Wil je de Pi
er niet tussen hebben, maak dan alleen een DNS record in Cloudflare:
`CNAME weather → siemhoukes.github.io` (DNS only). Gebruik één van de twee,
niet allebei.
