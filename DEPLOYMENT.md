# Deploy WeeklyRoulette Bot na Fly.io 🚀

Ten przewodnik opisuje jak wdrożyć WeeklyRoulette Slack Bota na platformie Fly.io.

## Wymagania

- Konto na [Fly.io](https://fly.io)
- Zainstalowane [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)
- Skonfigurowany Slack bot (patrz README.md)

## Kroki Deployment

### 1. Zaloguj się do Fly.io

```bash
fly auth login
```

### 2. Stwórz aplikację

```bash
# Zastąp "weeklyroulette-bot" swoją nazwą
fly apps create weeklyroulette-bot
```

### 3. Stwórz volume dla bazy danych

```bash
# Volume będzie przechowywać SQLite database
fly volumes create weeklyroulette_data --region fra --size 1
```

### 4. Ustaw zmienne środowiskowe

Ustaw secrety dla tokenerów Slack i Anthropic:

```bash
# Slack tokens (wymagane)
fly secrets set SLACK_BOT_TOKEN=xoxb-your-bot-token
fly secrets set SLACK_APP_TOKEN=xapp-your-app-token
fly secrets set SLACK_SIGNING_SECRET=your-signing-secret

# Anthropic API (opcjonalne - dla AI wiadomości)
fly secrets set ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 5. Deploy aplikacji

```bash
fly deploy
```

### 6. Sprawdź status

```bash
fly status
fly logs
```

## Zarządzanie

### Sprawdzenie logów
```bash
fly logs --app weeklyroulette-bot
```

### Restart aplikacji
```bash
fly restart
```

### Aktualizacja konfiguracji
```bash
# Po zmianach w fly.toml
fly deploy --no-cache
```

### Backup bazy danych
```bash
# Pobierz kopię SQLite database
fly ssh sftp get /data/weeklyroulette.db ./backup-$(date +%Y%m%d).db
```

### Monitoring
```bash
# Real-time monitoring
fly dashboard
```

## Troubleshooting

### Bot nie odpowiada
1. Sprawdź logi: `fly logs`
2. Zweryfikuj secrety: `fly secrets list`
3. Sprawdź status: `fly status`

### Database errors
1. Sprawdź czy volume jest mounted: `fly volumes list`
2. Restart aplikacji: `fly restart`

### Performance issues
1. Sprawdź metryki: `fly dashboard`
2. Rozważ zwiększenie resources w `fly.toml`

## Konfiguracja regionów

Domyślnie aplikacja jest deployowana w regionie Frankfurt (`fra`).
Żeby zmienić region, edytuj `primary_region` w `fly.toml`:

```toml
primary_region = "lhr"  # London
# lub
primary_region = "waw"  # Warsaw (jeśli dostępny)
```

## Ceny

- **Aplikacja**: ~$5-10/miesiąc dla basic tier
- **Volume**: ~$0.15/GB/miesiąc
- **Network**: Transfer zazwyczaj w ramach limitów free tier

Dokładne ceny sprawdź na: https://fly.io/docs/about/pricing/

## Security

- Wszystkie tokeny są przechowywane jako encrypted secrets
- Database jest na persistent volume (nie w kontenerze)
- Socket Mode nie wymaga publicznych webhooków

---

Gotowe! Twój bot powinien teraz działać 24/7 na Fly.io 🎉
