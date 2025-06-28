
# 🧠 LLM Analyzer

LLM Analyzer adalah aplikasi Flask yang menggunakan LLM (Large Language Model) melalui [OpenRouter](https://openrouter.ai) 
untuk menganalisis konten halaman web yang telah diekstrak, dan memberikan ringkasan isi serta evaluasi apakah halaman 
tersebut berpotensi sebagai phishing.

---

## 🚀 Fitur Utama

- 🔍 Mengambil data `extracted_content` dari database MySQL.
- 🤖 Menggunakan LLM untuk menghasilkan ringkasan isi dan analisis phishing.
- 🛡 Analisis berbasis konten `title`, `form`, `script`, dan `head` dari HTML.
- 📦 Struktur modular: fungsi prompt terpisah dari main app (`prompt_builder.py`).
- 🌐 API berbasis Flask dengan respons JSON.

---

## 📁 Struktur Proyek

```
llm-analyzer/
├── llm_api.py              # Aplikasi utama Flask
├── prompt_builder.py       # Penyusun prompt LLM
├── .env.example            # Contoh konfigurasi environment
├── .gitignore              # File untuk mengecualikan folder tertentu
├── requirements.txt        # Dependensi Python
└── README.md               # Dokumentasi proyek
```

---

## ⚙️ Instalasi & Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/llm-analyzer.git
cd llm-analyzer
```

### 2. Buat dan Aktifkan Virtual Environment

```bash
python -m venv llm-env
source llm-env/bin/activate      # Linux/macOS
llm-env\Scripts\activate       # Windows
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

### 4. Buat dan Isi File .env

```bash
cp .env.example .env
```

Isi file `.env` seperti ini:

```env
OPENROUTER_API_KEY=your-openrouter-api-key
LLM_MODEL=deepseek/deepseek-chat-v3-0324:free
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=
DB_NAME=phishing-database
```

---

## ▶️ Menjalankan Server

```bash
python llm_api.py
```

Server akan berjalan di: [http://localhost:5002](http://localhost:5002)

---

## 🔌 API Endpoint

### `GET /llm-analyze/<id>`

Melakukan analisis terhadap konten halaman web berdasarkan ID data pada database `phishings`.

Contoh Respons:

```json
{
  "status": "success",
  "llm_insight": "Ringkasan Halaman: ...\n\nAnalisis Phishing: ..."
}
```

### `GET /`

Endpoint tes status server:

```json
{
  "message": "Flask LLM Server Aktif"
}
```

---

## 📌 Catatan

- Data diambil dari kolom `extracted_content` yang berformat JSON.
- Sistem menangani konten JSON yang ter-encode dua kali (double-encoded).
- Model LLM dapat diubah melalui file `.env`.

---

## 📃 Lisensi

Proyek ini menggunakan lisensi MIT.
