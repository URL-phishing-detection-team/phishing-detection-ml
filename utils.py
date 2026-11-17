"""
utils.py - Normalisasi URL, validasi input, dan ekstraksi 16 fitur.
Dipakai bersama oleh train_model.py dan app.py agar preprocessing konsisten.
Alasan URL dinormalisasi (tanpa skema dan "www."): lihat README.
"""

import math
import re
from collections import Counter

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
MAX_URL_LENGTH = 2048  # batas wajar panjang URL untuk input aplikasi

IP_PATTERN = re.compile(
    r"^(([01]?\d\d?|2[0-4]\d|25[0-5])\.){3}([01]?\d\d?|2[0-4]\d|25[0-5])$"
)

# Dicocokkan terhadap host (bukan seluruh URL) agar "box.com" tidak dianggap "x.co"
SHORTENER_DOMAINS = {
    "bit.ly", "goo.gl", "shorte.st", "go2l.ink", "x.co", "ow.ly", "t.co",
    "tinyurl.com", "tr.im", "is.gd", "cli.gs", "buff.ly", "rebrand.ly",
    "cutt.ly", "rb.gy", "tiny.cc",
}

SENSITIVE_WORDS = [
    "login", "verify", "account", "update", "bank", "secure", "webscr",
    "signin", "password",
]

# Second-level umum pada TLD dua bagian (co.uk, com.au, co.id, ...)
_SECOND_LEVEL = {"co", "com", "org", "net", "ac", "go", "gov", "edu", "or", "web"}

FEATURE_NAMES = [
    "url_length",
    "has_ip",
    "count_at",
    "count_hyphen",
    "count_dot",
    "count_slash",
    "count_question",
    "count_equal",
    "is_shortened",
    "subdomain_count",
    "has_sensitive_word",
    "domain_length",
    "path_length",
    "digit_ratio",
    "host_digit_count",
    "url_entropy",
]


# ---------------------------------------------------------------------------
# Normalisasi & parsing
# ---------------------------------------------------------------------------
def normalize_url(url) -> str:
    """Huruf kecil, hapus spasi tepi, skema (http://, https://, ftp://) dan 'www.'."""
    s = str(url).strip().lower()
    s = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", s)
    s = re.sub(r"^www\d*\.", "", s)
    return s


def get_host(norm_url: str) -> str:
    """Ambil host dari URL ternormalisasi (tanpa userinfo dan port)."""
    host = re.split(r"[/?#]", norm_url, maxsplit=1)[0]
    if "@" in host:
        host = host.rsplit("@", 1)[1]
    host = host.split(":", 1)[0]
    return host


def get_registered_domain(url) -> str:
    """Perkiraan domain terdaftar (example.com / example.co.uk).

    Dipakai sebagai kunci grup pada split data agar domain yang sama tidak
    masuk ke data latih dan data uji sekaligus.
    """
    host = get_host(normalize_url(url))
    if IP_PATTERN.match(host):
        return host
    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    if len(parts[-1]) == 2 and parts[-2] in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in Counter(text).values())


# ---------------------------------------------------------------------------
# Validasi input aplikasi
# ---------------------------------------------------------------------------
def validate_url_input(raw):
    """Validasi input pengguna. Mengembalikan (True, '') atau (False, pesan_error)."""
    if raw is None or not isinstance(raw, str) or not raw.strip():
        return False, "URL tidak boleh kosong."
    s = raw.strip()
    if len(s) > MAX_URL_LENGTH:
        return False, f"URL terlalu panjang (maksimal {MAX_URL_LENGTH} karakter)."
    if re.search(r"\s", s):
        return False, "URL tidak boleh mengandung spasi."
    if re.match(r"^[a-z][a-z0-9+.\-]*://", s, flags=re.IGNORECASE) and not re.match(
        r"^https?://", s, flags=re.IGNORECASE
    ):
        return False, "Hanya URL dengan skema http atau https yang didukung."
    host = get_host(normalize_url(s))
    if not host:
        return False, "Host/domain tidak ditemukan pada URL."
    if not IP_PATTERN.match(host):
        # domain harus punya minimal satu titik dan karakter yang valid
        if "." not in host or not re.match(r"^[a-z0-9.\-_]+$", host) or host.startswith(".") or host.endswith("."):
            return False, "Format domain tidak valid (contoh: contoh.com/halaman)."
    return True, ""


# ---------------------------------------------------------------------------
# Ekstraksi fitur
# ---------------------------------------------------------------------------
def extract_url_features(url):
    """Ekstrak 16 fitur numerik dari satu URL mentah.

    Urutan nilai mengikuti FEATURE_NAMES.
    """
    norm = normalize_url(url)
    host = get_host(norm)
    authority = re.split(r"[/?#]", norm, maxsplit=1)[0]  # host + userinfo + port
    path = norm[len(authority):]

    url_length = len(norm)
    has_ip = 1 if IP_PATTERN.match(host) else 0

    count_at = norm.count("@")
    count_hyphen = norm.count("-")
    count_dot = norm.count(".")
    count_slash = norm.count("/")
    count_question = norm.count("?")
    count_equal = norm.count("=")

    is_shortened = 1 if any(host == d or host.endswith("." + d) for d in SHORTENER_DOMAINS) else 0

    # Jumlah subdomain (di luar domain terdaftar). IP tidak punya subdomain.
    if has_ip:
        subdomain_count = 0
    else:
        host_parts = [p for p in host.split(".") if p]
        reg_parts = len(get_registered_domain(norm).split("."))
        subdomain_count = max(0, len(host_parts) - reg_parts)

    has_sensitive_word = 1 if any(w in norm for w in SENSITIVE_WORDS) else 0

    domain_length = len(host)
    path_length = len(path)
    digit_ratio = (sum(ch.isdigit() for ch in norm) / url_length) if url_length else 0.0
    host_digit_count = sum(ch.isdigit() for ch in host)
    url_entropy = _entropy(norm)

    return [
        url_length,
        has_ip,
        count_at,
        count_hyphen,
        count_dot,
        count_slash,
        count_question,
        count_equal,
        is_shortened,
        subdomain_count,
        has_sensitive_word,
        domain_length,
        path_length,
        digit_ratio,
        host_digit_count,
        url_entropy,
    ]


def features_as_dict(url) -> dict:
    """Pasangan {nama_fitur: nilai}; berguna untuk tabel breakdown di aplikasi."""
    return dict(zip(FEATURE_NAMES, extract_url_features(url)))


if __name__ == "__main__":
    contoh = [
        "https://www.google.com/search?q=python",
        "http://192.168.1.5/secure-login/verify.php?acct=123",
        "http://bit.ly/3abcXYZ",
        "login.verify-account.paypal.example-secure.com/signin",
    ]
    for u in contoh:
        print(u)
        print("  valid :", validate_url_input(u))
        print("  fitur :", features_as_dict(u))
