from typing import List, Dict, Any

def build_url_prompt(data: Dict[str, Any]) -> List[Dict[str, str]]:
    def limit_text(arr, max_len=400):
        if not isinstance(arr, list):
            return ""
        joined = "\n".join(arr)
        return (joined[:max_len] + '...') if len(joined) > max_len else joined

    titles = limit_text(data.get("titles", []), max_len=200)
    heads = limit_text(data.get("heads", []), max_len=500)
    forms = limit_text(data.get("forms", []), max_len=500)
    scripts = limit_text(data.get("scripts", []), max_len=500)
    prediction = data.get("prediction", "tidak tersedia").upper()
    confidence = round(data.get("confidence", 0) * 100, 2)
    trusted = data.get("trusted_domain", False)
    trusted_str = "YA" if trusted else "TIDAK"

    full_content = (
        f"Judul Halaman (Title):\n{titles}\n\n"
        f"Bagian Head:\n{heads}\n\n"
        f"Formulir (Forms):\n{forms}\n\n"
        f"Skrip (Scripts):\n{scripts}"
    ).strip()

    return [
        {"role": "system", 
         "content": (
            "Anda adalah seorang pakar keamanan siber yang ditugaskan untuk menganalisis halaman web berdasarkan "
            "struktur HTML dan prediksi awal dari sistem deteksi phishing berbasis machine learning. "
            "Tugas Anda adalah:\n"
            "1. Memberikan prediksi akhir (PHISHING atau TIDAK PHISHING) dan alasan yang logis\n"
            "2. Menyimpulkan tujuan halaman web\n"
            "3. Menganalisis potensi phishing\n"
            "Gunakan Bahasa Indonesia. Jawaban harus terstruktur dan profesional."
        )},
        {"role": "user", 
         "content": (
            f"Berikut adalah data yang diekstrak dari model:\n"
            f"- Prediksi awal model: {prediction}\n"
            f"- Confidence: {confidence}%\n\n"
            f"- Domain terpercaya: {trusted_str}\n"
            f"== DATA HALAMAN WEB ==\n{full_content}\n\n"
            "Silakan berikan analisis Anda dalam format berikut:\n\n"
            "Prediksi: [PHISHING / TIDAK PHISHING]\n\n"
            "Alasan: \n[...]\n\n"
            "Ringkasan Halaman:\n[...]\n\n"
            "Analisis Phishing:\n[...]"
        )}
    ]

def build_email_prompt(data: Dict[str, Any]) -> List[Dict[str, str]]:
    prediction = data.get("prediction", "tidak tersedia").upper()
    confidence = round(data.get("confidence", 0) * 100, 2)
    adjusted = round(data.get("adjusted_confidence", 0) * 100, 2)
    trusted = data.get("trusted_domain", False)
    trusted_str = "YA" if trusted else "TIDAK"
    email = data.get("value", "alamat tidak tersedia")
    features = data.get("features", {})

    # Format fitur menjadi daftar bullet
    features_str = "\n".join(f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in features.items())

    return [
        {
            "role": "system",
            "content": (
                "Anda adalah pakar keamanan siber yang ditugaskan untuk menganalisis alamat email dan memberikan "
                "penilaian terhadap potensi phishing berdasarkan fitur-fitur teknis dan prediksi awal dari model machine learning.\n"
                "Tugas Anda adalah:\n"
                "1. Menentukan apakah email tersebut tergolong PHISHING atau TIDAK PHISHING, disertai alasan logis\n"
                "2. Menjelaskan karakteristik teknis email tersebut\n"
                "3. Menyimpulkan apakah email tersebut dapat dipercaya\n"
                "Gunakan Bahasa Indonesia. Jawaban harus profesional dan terstruktur."
            )
        },
        {
            "role": "user",
            "content": (
                f"Berikut adalah data yang tersedia:\n"
                f"- Alamat Email: {email}\n"
                f"- Prediksi awal model: {prediction}\n"
                f"- Confidence awal: {confidence}%\n"
                f"- Confidence setelah penyesuaian: {adjusted}%\n"
                f"- Termasuk domain terpercaya: {trusted_str}\n\n"
                #f"== FITUR EMAIL ==\n{features_str}\n\n"
                "Silakan berikan analisis Anda dalam format berikut:\n\n"
                "Prediksi: [PHISHING / TIDAK PHISHING]\n\n"
                "Alasan: \n[...]\n\n"
                "Karakteristik Teknis:\n[...]\n\n"
                "Kesimpulan Kepercayaan:\n[...]"
            )
        }
    ]
