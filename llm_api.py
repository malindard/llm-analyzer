from flask import Flask, jsonify
import mysql.connector
import requests
import json
import logging
import re  # Regular expressions
import os
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv() 

# Inisialisasi Flask app
app = Flask(__name__)

# Konfigurasi dari environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free")

# Fungsi koneksi ke database
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "phishing-database")
    )

# Fungsi menyusun prompt untuk LLM hanya dengan 'form'
def build_prompt(data):
    def limit_text(arr, max_len=400):
        """Memotong teks jika panjangnya lebih dari max_len"""
        if not isinstance(arr, list):
            return ""
        joined = "\n".join(arr)
        return (joined[:max_len] + '...') if len(joined) > max_len else joined

    # Menggunakan semua bagian yang relevan dengan batas panjang yang berbeda
    titles = limit_text(data.get("titles", []), max_len=200)
    heads = limit_text(data.get("heads", []), max_len=500)
    forms = limit_text(data.get("forms", []), max_len=500)
    scripts = limit_text(data.get("scripts", []), max_len=500)

    full_content = (
        f"Judul Halaman (Title):\n{titles}\n\n"
        f"Bagian Head:\n{heads}\n\n"
        f"Formulir (Forms):\n{forms}\n\n"
        f"Skrip (Scripts):\n{scripts}"
    ).strip()

    return [
        {"role": "system", "content": (
            "Anda adalah seorang pakar keamanan siber dan analis konten web. "
            "Tugas utama Anda adalah menganalisis data yang diekstrak dari halaman web dan memberikan dua hal: "
            "1. Ringkasan singkat mengenai isi dan tujuan halaman web tersebut. "
            "2. Analisis risiko phishing: Tentukan apakah halaman tersebut berpotensi phishing atau tidak, beserta alasan yang jelas dan ringkas. "
            "Seluruh respons Anda harus dalam Bahasa Indonesia yang baku, jelas, dan mudah dipahami."
            "Hindari penggunaan bahasa campur, singkatan tidak resmi, atau rekomendasi tambahan. "
            "Fokus pada ringkasan dan analisis phishing saja."
        )},
        {"role": "user", "content": (
            f"Berikut adalah data yang diekstrak dari sebuah halaman web:\n\n{full_content}\n\n"
            "Mohon berikan analisis Anda dalam format berikut, selalu dalam Bahasa Indonesia:\n\n"
            "Ringkasan Halaman:\n[Ringkasan singkat tentang isi halaman]\n\n"
            "Analisis Phishing:\n[Kesimpulan apakah halaman ini phishing atau bukan, diikuti dengan alasan-alasan utama yang mendukung kesimpulan tersebut.]"
        )}
    ]

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Endpoint LLM
@app.route("/llm-analyze/<int:id>", methods=["GET"])
def analyze(id):
    logger.info(f"Received request for analysis with id: {id}")
    try:
        # Koneksi ke database dan ambil data
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT extracted_content FROM phishings WHERE id = %s", (id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row or not row["extracted_content"]:
            logger.error(f"Extracted content not found for id {id}")
            return jsonify({"error": "extracted_content kosong atau tidak ditemukan"}), 404

        extracted_raw = row["extracted_content"]
        logger.info(f"Extracted raw content: {extracted_raw}")

        # Decode JSON, tangani kemungkinan double-encoding
        try:
            data_dict = json.loads(extracted_raw)
            # Terus decode jika hasilnya masih string (JSON yang di-encode ganda)
            while isinstance(data_dict, str):
                logger.info("Konten sepertinya double-encoded. Melakukan decode ulang.")
                data_dict = json.loads(data_dict)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for id {id}: {str(e)}")
            return jsonify({"error": f"Gagal mem-parsing extracted_content: {str(e)}"}), 500
        
        # Setelah decode, pastikan kita mendapatkan dictionary untuk diproses
        if not isinstance(data_dict, dict):
            error_msg = f"Konten yang di-parse bukan dictionary (tipe: {type(data_dict).__name__}). Tidak dapat diproses."
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

        # Generate prompt untuk LLM
        prompt = build_prompt(data_dict)
        logger.info(f"Generated prompt for id {id}: {prompt}")

        # Kirim request ke OpenRouter API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "LLM Analyzer"
            },
            json={
                "model": MODEL,
                "messages": prompt
            }
        )

        result = response.json()
        logger.info(f"LLM Response for id {id}: {json.dumps(result, indent=2)}")

        if "error" in result or "choices" not in result:
            error_message = result.get('error', {}).get('message', 'Unknown LLM error')
            logger.error(f"LLM API Error for id {id}: {error_message}")
            return jsonify({"status": "error", "message": f"LLM Error: {error_message}"}), 500
        
        # Ambil insight dari respons dan kirim dengan kunci yang benar
        insight = result.get("choices", [{}])[0].get("message", {}).get("content", "No insight from LLM.")

        return jsonify({
            "status": "success",
            "llm_insight": insight
        })

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Prompt error: {str(e)}"
        }), 500

# Route utama untuk cek status
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask LLM Server Aktif"}), 200

if __name__ == "__main__":
    # Jalankan server Flask di port 5002
    app.run(port=5002, debug=True)
