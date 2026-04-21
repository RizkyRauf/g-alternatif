# SearX Multi-Keyword Scraper API

FastAPI-based API untuk melakukan scraping hasil pencarian dari SearX secara efisien dan parallel menggunakan `ProcessPoolExecutor`. Project ini menggunakan **SeleniumBase (UC Mode)** untuk menembus proteksi anti-bot dan memberikan hasil yang stabil.

## Fitur Utama

- **Parallel Scraping**: Menggunakan `ProcessPoolExecutor` untuk menjalankan beberapa proses scraping secara bersamaan, meningkatkan kecepatan secara signifikan untuk banyak keyword.
- **Anti-Bot Bypass**: Implementasi **SeleniumBase Undetected ChromeDriver (UC Mode)** untuk menghindari deteksi bot oleh mesin pencari.
- **Batch Processing**: Endpoint khusus untuk mencari banyak keyword sekaligus dalam satu request dengan kontrol konkurensi.
- **Flexible Categories**: Mendukung berbagai kategori pencarian SearX (General, News, IT, dll).
- **Structured Logging**: Log aktivitas dan error dicatat secara otomatis di folder `logs/app.log` untuk memudahkan debugging.
- **Health Check**: Endpoint untuk memantau status kesehatan server dan konfigurasi worker.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Scraping**: [SeleniumBase](https://github.com/seleniumbase/SeleniumBase) (UC Mode), [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- **Parallelism**: `concurrent.futures.ProcessPoolExecutor`
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Environment**: Python 3.11+

## Instalasi & Menjalankan

### 1. Setup Pertama Kali
Project ini menyediakan script `run.sh` untuk mempermudah setup environment dan instalasi dependencies secara otomatis.

```bash
# Clone Repository
git clone <repository-url>
cd google_alternatif

# Berikan Izin Eksekusi
chmod +x run.sh

# Jalankan Setup & Server
./run.sh
```

**Apa yang dilakukan oleh `run.sh`?**
- Membuat virtual environment (`venv`).
- Menginstall semua dependencies dari `requirements.txt`.
- Membuat file `.env` dari `.env.example`.
- Menjalankan server FastAPI.

### 2. Menjalankan Kembali (Subsequent Runs)
Setelah setup pertama selesai, Anda tidak perlu menjalankan `run.sh` lagi. Cukup aktifkan virtual environment dan jalankan server menggunakan Uvicorn:

```bash
# Aktifkan virtual environment
source venv/bin/activate

# Jalankan server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔌 API Endpoints

Server berjalan secara default di `http://0.0.0.0:8000`.
Dokumentasi interaktif Swagger UI tersedia di: `http://localhost:8000/docs`

### 1. Single Search
`GET /search`

| Parameter | Tipe | Wajib | Default | Deskripsi |
| :--- | :--- | :---: | :--- | :--- |
| `q` | string | ✅ | - | Kata kunci pencarian |
| `max_pages` | integer | ❌ | 3 | Jumlah halaman yang akan di-scrape (1-10) |
| `category` | string | ❌ | `general` | Kategori pencarian SearX |

**Contoh Request:**
`GET /search?q=teknologi+ai&max_pages=2&category=news`

---

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

| Field | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `keywords` | list[str] | Daftar kata kunci (maksimal 50 keyword) |
| `max_pages` | integer | Jumlah halaman per keyword (1-10) |
| `category` | string | Kategori pencarian (general, news, dll) |
| `concurrency` | integer | Jumlah task parallel (1-10) |

---

### 3. System Endpoints
- `GET /health`: Mengecek status kesehatan API, versi, dan jumlah worker.
- `GET /`: Informasi dasar API dan shortcut endpoint.

## Konfigurasi (`.env`)

Sesuaikan konfigurasi aplikasi melalui file `.env`:

| Variable | Deskripsi | Default |
| :--- | :--- | :--- |
| `BASE_URL` | URL instance SearX yang digunakan | - |
| `DEFAULT_MAX_PAGES` | Jumlah halaman default untuk search | 3 |
| `DEFAULT_CATEGORY` | Kategori default | `general` |
| `HEADLESS` | Jalankan browser tanpa GUI (`True`/`False`) | `True` |
| `MAX_WORKERS` | Jumlah maksimal process worker untuk parallel scraping | 4 |
| `MAX_BATCH_KEYWORDS` | Maksimal keyword dalam satu request batch | 50 |
| `MAX_BATCH_CONCURRENCY` | Maksimal konkurensi dalam satu request batch | 10 |
| `LOG_LEVEL` | Level logging (`INFO`, `DEBUG`, `ERROR`) | `INFO` |
| `BLOCK_IMAGES` | Blokir loading gambar untuk kecepatan | `True` |
| `DISABLE_CSP` | Nonaktifkan Content Security Policy | `True` |

## Struktur Project

```text
google_alternatif/
├── app/
│   ├── core/               # Konfigurasi, logging, dan settings
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── models/             # Pydantic models untuk request/response
│   │   └── search.py
│   ├── services/           # Logika utama scraping
│   │   ├── scraper.py      # Single search logic
│   │   └── batch_scraper.py # Parallel batch logic
│   └── main.py             # Entry point FastAPI
├── logs/                   # Folder penyimpanan log aplikasi
│   └── app.log
├── downloaded_files/       # Tempat penyimpanan file hasil download (jika ada)
├── google_search.py        # Utility script untuk search
├── test_batch.py           # Script untuk testing batch scraping
├── requirements.txt        # Dependencies project
├── run.sh                  # Script setup dan run otomatis
└── .env                    # Konfigurasi environment
```

## Testing

Untuk menguji fungsionalitas batch scraping tanpa melalui API, Anda dapat menjalankan script `test_batch.py`:

```bash
source venv/bin/activate
python test_batch.py
```

## 📝 Logging

Semua aktivitas scraper, permintaan API, dan error dicatat secara real-time. Anda dapat memantau log menggunakan command:

```bash
tail -f logs/app.log
```

