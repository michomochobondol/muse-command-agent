"""Custom Tools - ini "tangan" buat agen AI.

Prinsip: tulis fungsi Python biasa yang jalan manual dulu,
baru bungkus jadi CrewAI BaseTool biar bisa dipanggil agen.
"""

from crewai.tools import BaseTool
import requests
from bs4 import BeautifulSoup


class ScrapeWebsiteTool(BaseTool):
    name: str = "scrape_website"
    description: str = (
        "Mengambil teks utama dari sebuah URL. "
        "Input harus URL lengkap, contoh: https://example.com"
    )

    def _run(self, url: str) -> str:
        try:
            resp = requests.get(
                url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            # batasi biar tidak kepanjangan buat LLM
            return "\n".join(lines[:200])
        except Exception as e:
            return f"Gagal scrape {url}: {e}"


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = (
        "Menulis teks ke file lokal. "
        "Input format: 'path|isi'. Contoh: '/tmp/hasil.md|# Halo'"
    )

    def _run(self, input_str: str) -> str:
        try:
            path, content = input_str.split("|", 1)
            path = path.strip()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Berhasil tulis ke {path}"
        except Exception as e:
            return f"Gagal tulis file: {e}"


# Instance yang dipakai agen
scrape_website_tool = ScrapeWebsiteTool()
write_file_tool = WriteFileTool()
