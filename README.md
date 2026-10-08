# Web Command Center - Backend (MVP, Groq free tier)

Backend FastAPI + CrewAI pakai Groq yang gratis. Siap deploy ke Railway.

## Deploy dari HP ke Railway

1. Download zip backend dari chat ini, extract di HP (pakai app ZArchiver atau sejenisnya).

2. Bikin repo baru di github.com via browser HP, upload semua file backend ke sana.
   Pastikan file `.env` TIDAK ikut ke-upload (sudah ada di `.gitignore`).

3. Buka railway.app via browser HP, login, klik New Project > Deploy from GitHub Repo, pilih repo kamu.

4. Di dashboard Railway, buka tab Variables, tambahkan:
   - `GROQ_API_KEY` = key baru kamu dari console.groq.com
   - `GROQ_MODEL` = `groq/llama-3.3-70b-versatile`
   
   Jangan taruh key di kode atau di chat, cukup di sini.

5. Railway otomatis deploy. Tunggu sampai status Active, buka URL yang dikasih Railway buat tes.

6. Test:
   - POST `https://url-railway-kamu.up.railway.app/api/jobs` dengan body `{"objective": "Riset harga kopi arabika 2026"}`
   - GET `https://url-railway-kamu.up.railway.app/api/jobs/{job_id}` buat lihat hasil

## Jalanin lokal (kalau ada laptop)

```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# isi GROQ_API_KEY di .env
uvicorn app.main:app --reload --port 8000
```

## Struktur

- `app/main.py` - FastAPI, job queue in-memory, WebSocket log streaming
- `app/crew.py` - definisi agen Researcher dan Writer + task-nya, LLM via Groq
- `app/tools.py` - contoh custom tools: `scrape_website` dan `write_file`
- `Procfile`, `railway.json` - config deploy Railway
- `.gitignore` - memastikan `.env` tidak ke-push

## Custom tool baru

Lihat `app/tools.py`. Polanya:
1. Bikin fungsi Python biasa, tes manual dulu sampai jalan
2. Bungkus jadi `BaseTool` dengan `name` dan `description` yang jelas
3. Daftarkan ke `tools=[...]` di agen yang butuh di `app/crew.py`
