import random
import re
import requests
from config import Config

TR_MAP = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iissgguuoocc")


def normalize(metin):
    return (metin or "").translate(TR_MAP).lower()


class AIServiceError(Exception):
    pass


FIKIR_KAHRAMAN = ["kocaman kalpli ama sürekli bozulan bir robot", "ejderhalardan korkan cesur bir şövalye", "her şeyi ters yapan uykucu bir büyücü",
                  "ışık hızında koşan ama hep geç kalan bir kaplumbağa", "mor pelerinli, kedileri seven bir süper kahraman", "çizimleri canlanan küçük bir ressam"]
FIKIR_MEKAN = ["sisli bir vadide unutulmuş bir krallıkta", "şehrin en yüksek çatısında", "hareketli bir ortaçağ pazar yerinde",
               "bulutların üstündeki uçan bir adada", "sihirli bir çizim defterinin içinde", "gece yarısı açılan gizemli bir stüdyoda"]
FIKIR_SORUN = ["kaybolan tacı bulmaya çalışıyor", "yanlışlıkla tüm şehri güldürüyor", "kendi gölgesinden kaçıyor",
               "dev bir sırrı saklamaya uğraşıyor", "bir dostluğu kurtarmak için yarışıyor", "herkesi şaşırtan bir icat yapıyor"]

SAKALAR = [
    "Şövalye neden hep geç kalırmış? Zırhını giymesi bir saat, çıkarması iki saat sürdüğü için! 🛡️",
    "Mor Adam'a sormuşlar: 'Neden hep gece çıkıyorsun?' Demiş ki: 'Pelerinim gündüz ütüsüz görünüyor!' 🟣",
    "Animatör kahve içer mi? Hayır, kare kare içer! ☕🎞️",
    "Ejderha Sakar Şövalye'ye demiş ki: 'Bu sefer ben kaçıyorum, sen kovala!' 🐉",
]

# Anahtar kelime -> cevap, öneriler, form önerisi
NIYETLER = [
    {"ad": "selam", "anahtar": ["merhaba", "selam", "hey", "gunaydin", "iyi aksamlar", "naber", "sa "],
     "cevap": "Selam maceracı! 🎬 Ben Watashi AI. Dizilerimizi, karakterlerimizi ya da kendi çizgi film fikrini bana sorabilirsin. Hatta sana çizgi film fikri bile uydurabilirim! Nereden başlayalım?",
     "oneriler": ["Bana bir fikir ver", "Dizileriniz neler?", "Çizgi film yaptırmak istiyorum"], "form": False},
    {"ad": "kimsin", "anahtar": ["kimsin", "sen kimsin", "adin ne", "yapay zeka misin", "robot musun", "ne yapabilirsin"],
     "cevap": "Ben Watashi AI, stüdyonun neşeli rehberiyim! 🤖 Dizilerimizi anlatabilir, süreci açıklayabilir, sana çizgi film fikri üretebilir, şaka yapabilir, 'Hangi karakterim?' testini yaptırabilir ve proje teklifini ekibe iletebilirim.",
     "oneriler": ["Bana bir fikir ver", "Hangi karakterim?", "Bir şaka yap"], "form": False},
    {"ad": "fikir", "anahtar": ["fikir", "oner bana", "hikaye uydur", "yaratici", "ilham", "senaryo oner"],
     "cevap": None, "oneriler": ["Başka bir fikir ver", "Bunu yaptırmak istiyorum", "Süreç nasıl işliyor?"], "form": False, "uret": "fikir"},
    {"ad": "saka", "anahtar": ["saka", "espri", "fikra", "güldür", "guldur", "komik bir sey"],
     "cevap": None, "oneriler": ["Bir şaka daha", "Sakar Şövalye'yi anlat", "Bana bir fikir ver"], "form": False, "uret": "saka"},
    {"ad": "test", "anahtar": ["hangi karakter", "karakter testi", "quiz", "test yap", "hangisiyim"],
     "cevap": "🎲 Harika, küçük bir test yapalım! Üç soruda hangi Watashi karakterine benzediğini bulacağız.",
     "oneriler": [], "form": False, "etkilesim": "test"},
    {"ad": "sakar", "anahtar": ["sakar", "sovalye"],
     "cevap": "⚔️ Sakar Şövalye, zırhı kendinden büyük ama kalbi altın gibi olan şövalyemizin komik maceraları! Ortaçağ pazar yerinde devrilen fıçılar, kaçışan soğanlar ve her seferinde ters giden kahramanlık anları. Tam bir kahkaha serisi!",
     "oneriler": ["Kırık Taç Vadisi nedir?", "Mor Adam kim?", "Bir şaka yap"], "form": False},
    {"ad": "kirik_tac", "anahtar": ["kirik tac", "vadi", "vadisi", "kirik"],
     "cevap": "👑 Kırık Taç Vadisi, unutulmuş krallıkların, yıkık kalelerin ve kadim sırların saklandığı sinematik bir fantastik evren. Sisli vadiler, dev taş kalıntılar, şelaleler ve dostluk hikâyeleriyle atmosferik bir macera sunuyor.",
     "oneriler": ["Sakar Şövalye'yi anlat", "Raw To Real nedir?", "Hangi karakterim?"], "form": False},
    {"ad": "mor_adam", "anahtar": ["mor adam", "super kahraman", "superhero", "kahraman"],
     "cevap": "🟣 Mor Adam, göğsünde parlayan W amblemiyle gece şehrin çatılarında nöbet tutan süper kahramanımız! Aksiyon, mizah ve gizemli enerjiyi bir araya getiriyor. Mor pelerini rüzgârda dalgalanırken şehir ışıkları altında maceralar başlıyor.",
     "oneriler": ["Karakter tasarımı yapıyor musunuz?", "Kırık Taç Vadisi nedir?", "Teklif almak istiyorum"], "form": False},
    {"ad": "raw", "anahtar": ["raw to real", "raw", "eskiz", "tel kafes", "model", "3d", "3 boyut"],
     "cevap": "⚡ Raw To Real, ham fikrin ve tel kafes modelin renkli, canlı final karaktere dönüşmesini anlatan serimiz ve aynı zamanda prodüksiyon mutfağımız. Eskizden modele, modelden ışıklı finale her adımı gösteriyoruz.",
     "oneriler": ["Süreç nasıl işliyor?", "Karakterimi tasarlar mısınız?", "Teklif almak istiyorum"], "form": False},
    {"ad": "sure", "anahtar": ["ne kadar surer", "kac gun", "kac hafta", "teslim suresi", "sure", "ne zaman biter"],
     "cevap": "⏱️ Süre; animasyonun uzunluğuna, karakter sayısına ve detay seviyesine göre değişiyor, o yüzden net bir gün sözü uydurmak istemem. Fikrini anlatırsan ekibimiz sana özel bir takvim çıkarır!",
     "oneriler": ["Süreç nasıl işliyor?", "Teklif almak istiyorum"], "form": True},
    {"ad": "surec", "anahtar": ["surec", "asama", "nasil calisiyor", "nasil isliyor", "nasil yapiyorsunuz", "uretim"],
     "cevap": "🎞️ Genel akışımız: 1) Fikir ve senaryo, 2) Storyboard, 3) Karakter tasarımı, 4) Animasyon, 5) Ses ve müzik, 6) Final teslim. Fikrini anlatırsan sana özel bir yol haritası çıkarabiliriz!",
     "oneriler": ["Teklif almak istiyorum", "Karakter tasarımı yapıyor musunuz?", "Süre ne kadar?"], "form": True},
    {"ad": "hizmet", "anahtar": ["hizmet", "ne yapiyorsunuz", "neler yapiyorsunuz", "karakter tasarim", "storyboard", "reklam", "tanitim", "yaptir", "uretir misiniz", "yapar misiniz", "yapiyor musunuz"],
     "cevap": "🎨 Markalar, içerik üreticileri ve bireyler için 2D karakter tasarımı, storyboard, çizgi film prodüksiyonu ve reklam/tanıtım animasyonu yapıyoruz. Kendi dizilerimizi de üretiyoruz. Projen ne tür bir şey?",
     "oneriler": ["Süreç nasıl işliyor?", "Teklif almak istiyorum", "Bana bir fikir ver"], "form": True},
    {"ad": "teklif", "anahtar": ["fiyat", "ucret", "teklif", "kac para", "butce", "maliyet", "iletisim", "ulas", "telefon", "mail", "e-posta", "adres", "whatsapp", "instagram", "is birligi", "siparis", "proje baslat", "calismak istiyorum", "yaptirmak istiyorum"],
     "cevap": "🌟 Harika! Fiyat ve süre projenin kapsamına göre belirleniyor, herkese özel teklif hazırlıyoruz. Aşağıdaki mini forma adını, telefonunu ve projeni yaz, ekibimiz seni arasın!",
     "oneriler": ["Süreç nasıl işliyor?", "Dizileriniz neler?"], "form": True},
    {"ad": "diziler", "anahtar": ["dizi", "seri", "hangi", "neler var", "karakterler", "evren"],
     "cevap": "📺 Dört evrenimiz var: ⚔️ Sakar Şövalye (komedi), 👑 Kırık Taç Vadisi (fantastik macera), 🟣 Mor Adam (süper kahraman) ve ⚡ Raw To Real (eskizden ekrana). Hangisini merak ediyorsun?",
     "oneriler": ["Sakar Şövalye'yi anlat", "Mor Adam kim?", "Hangi karakterim?"], "form": False},
    {"ad": "tesekkur", "anahtar": ["tesekkur", "sag ol", "sagol", "eyvallah", "harika", "super"],
     "cevap": "Rica ederim! 🌈 Aklına başka bir şey gelirse buradayım. Çizgi film fikrin varsa bize bırakmayı unutma!",
     "oneriler": ["Teklif almak istiyorum", "Bana bir fikir ver"], "form": False},
]

VARSAYILAN = {
    "cevap": "Hmm, bunu tam anlayamadım ama yardımcı olmak isterim! 🎬 Dizilerimizi, hizmetlerimizi ya da sürecimizi sorabilir, benden çizgi film fikri veya şaka isteyebilirsin.",
    "oneriler": ["Bana bir fikir ver", "Dizileriniz neler?", "Teklif almak istiyorum"], "form": False,
}

AD_RE = re.compile(r"(?:ad[ıiİI]m|ismim)\s+([A-Za-zÇĞİÖŞÜçğıöşü]{2,20})", re.IGNORECASE)
TEL_RE = re.compile(r"(\+?\d[\d\s\-()]{8,}\d)")


def niyet_bul(mesaj):
    n = " " + normalize(mesaj) + " "
    en_iyi, en_puan = None, 0
    for niyet in NIYETLER:
        puan = sum(1 for a in niyet["anahtar"] if normalize(a) in n)
        if puan > en_puan:
            en_iyi, en_puan = niyet, puan
    return en_iyi


def gecmisi_temizle(gecmis):
    temiz = []
    for iz in (gecmis or [])[-10:]:
        if isinstance(iz, dict) and iz.get("role") in ("user", "assistant") and isinstance(iz.get("content"), str):
            temiz.append({"role": iz["role"], "content": iz["content"][:1000]})
    return temiz


def ad_bul(mesaj, gecmis):
    for metin in [mesaj] + [m["content"] for m in reversed(gecmis) if m["role"] == "user"]:
        m = AD_RE.search(metin)
        if m:
            return m.group(1).capitalize()
    return ""


def telefon_bul(mesaj):
    m = TEL_RE.search(mesaj or "")
    return m.group(1).strip() if m else ""


def uret(tur):
    if tur == "fikir":
        return ("💡 İşte sıcak sıcak bir fikir: " + random.choice(FIKIR_KAHRAMAN) + ", " + random.choice(FIKIR_MEKAN) + " " +
                random.choice(FIKIR_SORUN) + ". Bunu çizgi filme dönüştürmek ister misin?")
    return random.choice(SAKALAR)


class AIService:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _canli_mi(self):
        key = Config.GROQ_API_KEY
        return bool(key) and key.startswith("gsk_") and "BURAYA" not in key

    def yanit_uret(self, mesaj, gecmis=None):
        """Sözlük döner: cevap, oneriler, form_oner, mod, ad, telefon, etkilesim."""
        mesaj = (mesaj or "").strip()[:600]
        gecmis = gecmisi_temizle(gecmis)
        niyet = niyet_bul(mesaj)
        secili = niyet or VARSAYILAN
        ad = ad_bul(mesaj, gecmis)
        telefon = telefon_bul(mesaj)
        form = secili["form"] or bool(telefon)
        sonuc = {"oneriler": secili["oneriler"], "form_oner": form, "ad": ad, "telefon": telefon,
                 "etkilesim": secili.get("etkilesim", "")}

        # Eğlence/üretim niyetleri her zaman yerel çalışır
        if niyet and niyet.get("uret"):
            sonuc.update(cevap=uret(niyet["uret"]), mod="yerel")
            return sonuc

        if self._canli_mi() and not sonuc["etkilesim"]:
            try:
                ek = (" Ziyaretçinin adı: " + ad + ".") if ad else ""
                sonuc.update(cevap=self._canli_cevap(mesaj, gecmis, ek), mod="canli")
                return sonuc
            except AIServiceError as e:
                print("[ai_service] Canlı AI başarısız, demo moda geçildi:", e)  # Render loglarında görünür

        cevap = secili["cevap"]
        if ad and niyet and niyet["ad"] in ("selam", "teklif", "tesekkur"):
            cevap = ad + ", " + (cevap[0].lower() + cevap[1:] if cevap[0].isalpha() else cevap)
        if telefon and not niyet:
            cevap = "Numaranı aldım, teşekkürler! 📞 Mini formu doldurup göndersen ekibimiz seni arayacak."
        sonuc.update(cevap=cevap, mod="demo")
        return sonuc

    def _canli_cevap(self, mesaj, gecmis, ek=""):
        mesajlar = [{"role": "system", "content": Config.BUSINESS_CONTEXT + ek}] + gecmis
        mesajlar.append({"role": "user", "content": mesaj})
        headers = {"Authorization": "Bearer " + Config.GROQ_API_KEY, "Content-Type": "application/json"}
        payload = {"model": Config.GROQ_MODEL, "messages": mesajlar, "temperature": 0.6, "max_tokens": 450}
        try:
            r = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise AIServiceError("Yapay zeka servisine şu an ulaşılamıyor: " + str(e))


ai_service = AIService()
