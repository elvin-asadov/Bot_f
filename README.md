# 🤖 Standup Bot — Quraşdırma Təlimatı

## Addım 1 — Telegram Bot Token Al

1. Telegram-da `@BotFather`-ə yaz
2. `/newbot` göndər
3. Bota ad ver (məs: `DroneTeamStandupBot`)
4. Token alacaqsan — saxla (`123456:ABC-DEF...` formatında)

---

## Addım 2 — Sənin Telegram ID-ni öyrən

1. Telegram-da `@userinfobot`-a yaz
2. `/start` göndər
3. ID-ni kopyala (məs: `987654321`)

---

## Addım 3 — Railway.app-da Deploy Et

1. [railway.app](https://railway.app) — GitHub ilə qeydiyyat
2. **New Project → Deploy from GitHub repo**
3. Bu qovluğu GitHub-a yüklə
4. Railway-də **Variables** bölməsinə get və əlavə et:

| Dəyişən | Dəyər |
|---------|-------|
| `BOT_TOKEN` | BotFather-dən aldığın token |
| `MANAGER_ID` | Sənin Telegram ID-n |
| `STANDUP_HOUR` | `9` (səhər 9-da başlasın) |
| `STANDUP_MINUTE` | `0` |
| `TIMEZONE` | `Asia/Baku` |

5. **Deploy** düyməsinə bas — bot işə düşür ✅

---

## Addım 4 — Mühəndisləri Əlavə Et

Hər mühəndis bota `/start` yazmalıdır — ID-lərini sənə göndərəcəklər.

Sonra sən bota yazırsan:
```
/adduser 123456789 Əli Həsənov
/adduser 987654321 Vüsal Məmmədov
```

---

## Botun Əmrləri

| Əmr | Nə edir |
|-----|---------|
| `/standupnow` | Dərhal standupı başladır |
| `/report` | Bu günün hesabatını göndər |
| `/listusers` | Komanda siyahısı |
| `/adduser [id] [ad]` | Mühəndis əlavə et |
| `/removeuser [id]` | Mühəndis sil |

---

## Bot Necə İşləyir

```
Hər səhər 09:00
      ↓
Bot hər mühəndisə şəxsən yazır
      ↓
3 sual soruşur (ardıcıl)
      ↓
Hər cavabdan sonra sənə bildiriş
      ↓
Hamı cavab verdikdə tam hesabat gəlir
      ↓
🔴 Maneəsi olanlar qırmızı işarələnir
```

---

## Nümunə Hesabat

```
📋 Günlük Standup Hesabatı
📅 2025-01-15

👤 Əli Həsənov (09:07)
✅ Kamera modulunu sınadım
🎯 AI modelini drona qoşacağam
🔴 Maneə: Lazım olan kabel yoxdur

👤 Vüsal Məmmədov (09:12)
✅ Uçuş kontrollerini test etdim
🎯 Avtopilot kodunu yeniliyəcəm
🟢 Maneə yoxdur

⚠️ Cavab verməyənlər:
• Rauf Əliyev
```
