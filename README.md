# SearX Multi-Keyword Scraper API

FastAPI-based API untuk melakukan scraping hasil pencarian dari SearX secara efisien dan parallel menggunakan `ProcessPoolExecutor`. Project ini menggunakan pendekatan hybrid dengan **SeleniumBase (UC Mode)** dan **Playwright** untuk menembus proteksi anti-bot.

## Fitur Utama

- **Parallel Scraping**: Menggunakan `ProcessPoolExecutor` untuk menjalankan beberapa proses scraping secara bersamaan.
- **Anti-Bot Bypass**: Implementasi SeleniumBase UC (Undetected ChromeDriver) dan CDP Mode untuk menghindari deteksi bot.
- **Hybrid Architecture**: Integrasi SeleniumBase dan Playwright untuk stabilitas maksimal.
- **Batch Processing**: Endpoint khusus untuk mencari banyak keyword sekaligus dalam satu request.
- **Flexible Categories**: Mendukung berbagai kategori SearX (General, News, IT, dll).
- **Structured Logging**: Log tersimpan secara otomatis di folder `logs/app.log`.

## Tech Stack

- **Framework**: FastAPI
- **Scraping**: SeleniumBase, Playwright, BeautifulSoup4
- **Parallelism**: `concurrent.futures.ProcessPoolExecutor`
- **Environment**: Python 3.13+, Virtualenv

## Instalasi & Menjalankan

Project ini menyediakan script `run.sh` untuk mempermudah setup environment dan instalasi dependencies.

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd google_alternatif
   ```

2. **Berikan Izin Eksekusi pada run.sh**
   ```bash
   chmod +x run.sh
   ```

3. **Jalankan Aplikasi**
   ```bash
   ./run.sh
   ```
   *Script ini akan otomatis:*
   - Membuat virtual environment (`venv`) jika belum ada.
   - Menginstall semua dependencies dari `requirements.txt`.
   - Menginstall browser binary Playwright.
   - Membuat file `.env` dari `.env.example`.
   - Menjalankan server FastAPI.

## API Endpoints

Server berjalan secara default di `http://0.0.0.0:8000`.
Dokumentasi interaktif tersedia di: `http://localhost:8000/docs`

### 1. Single Search
`GET /search`

**Parameter:**
- `q` (required): Kata kunci pencarian.
- `max_pages`: Jumlah halaman yang akan di-scrape (default: 3).
- `category`: Kategori pencarian (default: `general`).

**Contoh:**
`GET /search?q=pertamina&max_pages=2&category=news`

### 2. Batch Search
`POST /search/batch`

**Request Body:**
```json
{
  "keywords": ["pertamina", "telkom", "bca"],
  "max_pages": 2,
  "category": "general",
  "concurrency": 3
}
```

## Konfigurasi (`.env`)

Anda dapat menyesuaikan konfigurasi aplikasi melalui file `.env`:
- `BASE_URL`: URL instance SearX yang digunakan.
- `DEFAULT_MAX_PAGES`: Jumlah halaman default.
- `HEADLESS`: Set `True` untuk menjalankan browser di background.
- `MAX_WORKERS`: Jumlah maksimal process worker untuk parallel scraping.
- `LOG_LEVEL`: Level logging (`INFO`, `DEBUG`, `ERROR`).

## Logging

Semua aktivitas scraper dan error dicatat secara real-time ke dalam file:
`logs/app.log`

