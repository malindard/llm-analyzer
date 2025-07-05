import requests
import json
import logging
import os
from flask import Flask, jsonify, request
from prompt_builder import build_url_prompt, build_email_prompt
from pathlib import Path
from dotenv import load_dotenv

# Tentukan path ke file .env
dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Inisialisasi Flask app
app = Flask(__name__)

# Konfigurasi dari environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3-0324:free")

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validasi dan logging API Key saat startup
if not OPENROUTER_API_KEY:
    logger.critical("FATAL: OPENROUTER_API_KEY tidak ditemukan. Aplikasi akan berhenti.")
    raise ValueError("OPENROUTER_API_KEY tidak ditemukan. Pastikan variabel lingkungan sudah diatur dengan benar di file .env")
else:
    # Log versi tersamar dari key untuk verifikasi
    masked_key = f"{OPENROUTER_API_KEY[:5]}...{OPENROUTER_API_KEY[-4:]}"
    logger.info(f"OpenRouter API Key loaded successfully. (Key: {masked_key})")

# Endpoint LLM POST dari laravel
@app.route("/llm-analyze", methods=["POST"])
def llm_analyze():
    try:
        content = request.json.get("context", {})

        if not isinstance(content, dict):
            logger.error("Konten yang dikirim bukan dictionary.")
            return jsonify({"status": "error", "message": "Konten harus berupa dictionary"}), 400

        if not content:
            logger.error("Konten kosong atau tidak dikirim.")
            return jsonify({"status": "error", "message": "Konten kosong atau tidak dikirim"}), 400
        
        # Jika konten masih string JSON, decode ulang
        if isinstance(content, str):
            try:
                content = json.loads(content)
                while isinstance(content, str):  # tangani double encoding
                    content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Gagal decode JSON: {e}")
                return jsonify({"status": "error", "message": "Konten tidak valid JSON"}), 400
            
        if not isinstance(content, dict):
            logger.error("Konten yang dikirim bukan dictionary.")
            return jsonify({"status": "error", "message": "Konten harus berupa dictionary"}), 400

        # Generate prompt untuk LLM
        input_type = content.get("input_type", "").lower()
        if input_type == "email":
            prompt = build_email_prompt(content)
        else:
            prompt = build_url_prompt(content)
        
        logger.info(f"Generated prompt for id {id}: {prompt}")

        # Kirim request ke OpenRouter API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost", # Referer bisa penting untuk beberapa API
                "X-Title": "Phishing LLM Analyzer" # Nama aplikasi
            },
            json={
                "model": MODEL,
                "messages": prompt
            },
            timeout=90 # Tambahkan timeout untuk request yang lama
        )

        if response.status_code != 200:
            logger.error(f"LLM API gagal: {response.status_code} - {response.text}")
            return jsonify({
                "status": "error",
                "message": f"LLM API gagal: {response.status}"
                }), response.status_code

        result = response.json()
        logger.info(f"LLM Response: {json.dumps(result, indent=2)}")

        insight = result.get("choices", [{}])[0].get("message", {}).get("content", "No insight from LLM.")

        return jsonify({
            "status": "success",
            "llm_insight": insight
        })

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# Route utama untuk cek status
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask LLM Server Aktif"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)


# # Fungsi untuk mendapatkan koneksi database, menggunakan 'g' untuk cache per-request
# def get_db():
#     if 'db' not in g:
#         g.db = mysql.connector.connect(
#             host=os.getenv("DB_HOST", "127.0.0.1"),
#             user=os.getenv("DB_USER", "root"),
#             password=os.getenv("DB_PASSWORD", ""),
#             database=os.getenv("DB_NAME", "phishing-database")
#         )
#     return g.db

# # Fungsi untuk menutup koneksi database di akhir request
# @app.teardown_appcontext
# def teardown_db(exception):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()

# # Endpoint LLM
# @app.route("/llm-analyze/<int:id>", methods=["GET"])
# def analyze(id):
#     logger.info(f"Received request for analysis with id: {id}")
#     try:
#         # Koneksi ke database dan ambil data
#         db = get_db()
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("SELECT extracted_content FROM phishings WHERE id = %s", (id,))
#         row = cursor.fetchone()
#         cursor.close() # Tutup cursor segera setelah digunakan

#         if not row or not row["extracted_content"]:
#             logger.error(f"Extracted content not found for id {id}")
#             return jsonify({"error": "extracted_content kosong atau tidak ditemukan"}), 404

#         extracted_raw = row["extracted_content"]

#         # Log pratinjau konten
#         log_content_preview = (extracted_raw[:200] + '...') if len(extracted_raw) > 200 else extracted_raw
#         logger.info(f"Extracted raw content (preview): {log_content_preview}")

#         # Decode JSON, tangani kemungkinan double-encoding
#         try:
#             data_dict = json.loads(extracted_raw)
#             # Terus decode jika hasilnya masih string (JSON yang di-encode ganda)
#             while isinstance(data_dict, str):
#                 logger.info("Konten sepertinya double-encoded. Melakukan decode ulang.")
#                 data_dict = json.loads(data_dict)
#         except json.JSONDecodeError as e:
#             logger.error(f"JSON decode error for id {id}: {str(e)}")
#             return jsonify({"error": f"Gagal mem-parsing extracted_content: {str(e)}"}), 500
        
#         # Setelah decode, pastikan mendapatkan dictionary untuk diproses
#         if not isinstance(data_dict, dict):
#             error_msg = f"Konten yang di-parse bukan dictionary (tipe: {type(data_dict).__name__}). Tidak dapat diproses."
#             logger.error(error_msg)
#             return jsonify({"error": error_msg}), 500

#         # Generate prompt untuk LLM
#         prompt = build_prompt(data_dict)
#         logger.info(f"Generated prompt for id {id}: {prompt}")

#         # Kirim request ke OpenRouter API
#         response = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#                 "Content-Type": "application/json",
#                 "HTTP-Referer": "http://localhost", # Referer bisa penting untuk beberapa API
#                 "X-Title": "Phishing LLM Analyzer" # Nama aplikasi
#             },
#             json={
#                 "model": MODEL,
#                 "messages": prompt
#             },
#             timeout=90 # Tambahkan timeout untuk request yang lama
#         )

#         # Periksa status code HTTP sebelum mencoba parse JSON
#         if response.status_code != 200:
#             logger.error(f"LLM API request failed with status {response.status_code}: {response.text}")
#             return jsonify({
#                 "status": "error",
#                 "message": f"LLM API request failed with status {response.status_code}"
#             }), response.status_code

#         result = response.json()
#         logger.info(f"LLM Response for id {id}: {json.dumps(result, indent=2)}")

#         if "error" in result or "choices" not in result:
#             error_message = result.get('error', {}).get('message', 'Unknown LLM error')
#             logger.error(f"LLM API Error for id {id}: {error_message}")
#             return jsonify({"status": "error", "message": f"LLM Error: {error_message}"}), 500
        
#         insight = result.get("choices", [{}])[0].get("message", {}).get("content", "No insight from LLM.")

#         return jsonify({
#             "status": "success",
#             "llm_insight": insight
#         })

#     except mysql.connector.Error as db_err:
#         logger.error(f"Database error: {str(db_err)}")
#         return jsonify({"status": "error", "message": "Database error"}), 500
#     except requests.exceptions.RequestException as req_err:
#         logger.error(f"Request to LLM API failed: {str(req_err)}")
#         return jsonify({"status": "error", "message": "Failed to connect to LLM service"}), 500
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
#         return jsonify({
#             "status": "error",
#             "message": "An unexpected server error occurred."
#         }), 500

# # Route utama untuk cek status
# @app.route("/", methods=["GET"])
# def home():
#     return jsonify({"message": "Flask LLM Server Aktif"}), 200

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5002, debug=True)
