import requests
from config import Config


class AIServiceError(Exception):
    """Yapay zeka servisine ulaşılamadığında veya cevap bozuk geldiğinde fırlatılır."""


class AIService:
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def yanit_uret(self, mesaj, gecmis=None):
        """Mesajı Groq'a gönderir, cevap metnini döner. Hata olursa AIServiceError."""
        if not Config.GROQ_API_KEY:
            raise AIServiceError("GROQ_API_KEY tanımlı değil")

        mesajlar = [{"role": "system", "content": Config.BUSINESS_CONTEXT}]
        mesajlar += self._gecmisi_temizle(gecmis)
        mesajlar.append({"role": "user", "content": mesaj})

        try:
            r = requests.post(
                self.API_URL,
                headers={"Authorization": "Bearer " + Config.GROQ_API_KEY},
                json={"model": Config.GROQ_MODEL, "messages": mesajlar,
                      "temperature": 0.6, "max_tokens": 450},
                timeout=20,
            )
            r.raise_for_status()
            cevap = r.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            raise AIServiceError("Groq isteği başarısız: " + str(e)) from e
        except (KeyError, IndexError, ValueError) as e:
            raise AIServiceError("Groq cevabı beklenen biçimde değil") from e

        if not cevap:
            raise AIServiceError("Groq boş cevap döndü")
        return cevap

    @staticmethod
    def _gecmisi_temizle(gecmis):
        """Sadece son 10 geçerli mesajı alır (role/content doğrulaması)."""
        temiz = []
        for iz in (gecmis or [])[-10:]:
            if (isinstance(iz, dict) and iz.get("role") in ("user", "assistant")
                    and isinstance(iz.get("content"), str)):
                temiz.append({"role": iz["role"], "content": iz["content"][:1000]})
        return temiz


ai_service = AIService()
