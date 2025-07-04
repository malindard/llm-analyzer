from typing import List, Dict, Any

def build_prompt(data: Dict[str, Any]) -> List[Dict[str, str]]:
    def limit_text(arr, max_len=400):
        if not isinstance(arr, list):
            return ""
        joined = "\n".join(arr)
        return (joined[:max_len] + '...') if len(joined) > max_len else joined

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
            "1. PHISHING atau TIDAK PHISHING?"
            "1. Ringkasan singkat mengenai isi dan tujuan halaman web tersebut. "
            "2. Analisis risiko phishing..."
            "3. Hasil akhir prediksi menurut Anda dan alasannya"
        )},
        {"role": "user", "content": (
            f"Berikut adalah data yang diekstrak dari sebuah halaman web:\n\n{full_content}\n\n"
            "Mohon berikan analisis Anda dalam format berikut, selalu dalam Bahasa Indonesia:\n\n"
            "Prediksi:..."
            "Ringkasan Halaman:\n[...]\n\n"
            "Analisis Phishing:\n[...]"
            "Hasil Akhir prediksi dari LLM:\n[...]"
        )}
    ]
