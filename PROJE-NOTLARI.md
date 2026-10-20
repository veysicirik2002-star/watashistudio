# Watashi Studio / SmartLead AI — Proje Notları

> Bu dosya Claude'un proje hafızasıdır. Her oturumda önce burası okunur, yapılan her iş en alttaki **Çalışma Günlüğü**'ne eklenir.

---

## 1. Proje Özeti

- **Ne:** Yapay zekâ ile ziyaretçiyle sohbet eden ve iletişim bilgilerini (lead) toplayan sistem. Konu: **Watashi Studio** (çizgi film / 2D animasyon stüdyosu).
- **Mimari kaynağı:** SmartLead AI şablonu (eğitmenin yönergesi). Mimari sabit, konu (BUSINESS_CONTEXT, arayüz metinleri, marka) öğrenciye ait.
- **Stack:** Python 3.9+ · Flask · SQLite · Groq API · Wix Velo (frontend) · Render (yayın) · GitHub.
- **Süre:** 10 günlük bitirme projesi (MVP).
- **İki arayüz:** (1) Karşılama sayfası: AI sohbet + "Bize Ulaşın" formu. (2) Yönetim paneli: lead tablosu. Sohbet için ayrı sayfa şart değil, siteye gömülebilir.
- **Opsiyonel (zorunlu değil):** Admin girişi (şifre / admin-key).

## 2. Hedef Mimari ve Kurallar (Değerlendirme: Mimari %30)

```
smartlead_watashi_studio/
├── run.py              ← giriş noktası (app = create_app())
├── config.py           ← tüm ayarlar (.env okur), BUSINESS_CONTEXT
├── requirements.txt
├── .env                ← gizli (Git'e GİTMEZ)
├── .gitignore
└── app/
    ├── __init__.py     ← create_app() fabrikası
    ├── database.py     ← SQL SADECE burada
    ├── routes.py       ← sadece yönlendirme, SQL/AI kodu YOK
    ├── templates/      ← index.html, dashboard.html
    ├── static/img/
    └── services/ai_service.py  ← AI çağrısı SADECE burada
```

**Sözleşme:**
- `database.py` dışında SQL yok. `ai_service.py` dışında AI API çağrısı yok. `routes.py` yalnız bu ikisini çağırır.
- Spagetti kod yasak; her sınıf/fonksiyon tek amaca hizmet eder.
- SQL'de `?` yer tutucusu zorunlu (SQL birleştirme yasak).
- Dış servis çağrıları `try/except` (Python) ve `try/catch` (JS) ile sarılır; hata güvenli JSON döner; hatanın kaynağı terminale/loga yazılmalı.
- API anahtarı `.env`'de; `config.py` içine anahtar/şifre yazılmaz; Render'da Environment alanına ayrıca girilir.
- Kritik yerlere yorum satırı yazılır.
- Her API uç noktası `basari` alanlı JSON döner. Kodlar: eksik veri **400**, AI hatası **503**, yeni kayıt **201**.
- İki Blueprint: sayfalar ve `/api`.
- JSON alan adları frontend ↔ backend birebir aynı olmalı (bir harf farkı bağlantıyı koparır).
- Hazır koddan ilham alınabilir ama öğrenci her satırı açıklayabilmeli (sözlü savunma). Satır satır ezber beklenmez; sayfanın/sınıfın/fonksiyonun amacı bilinmeli.

## 3. Kod Tabanının Mevcut Durumu (2026-10-20 tarihli inceleme)

| Dosya | Ne yapıyor |
|---|---|
| `config.py` | `Config` + `DevelopmentConfig`/`ProductionConfig` + `config_by_name`. Ayarlar: `SECRET_KEY`, `DATABASE_URL`, `ADMIN_PASSWORD`, `GROQ_API_KEY`, `GROQ_MODEL` (varsayılan `llama-3.3-70b-versatile`), `AI_PROVIDER`, `CORS_ORIGINS`, `CHAT_RATE_LIMIT` (20/dk), `BUSINESS_CONTEXT` (Watashi AI kişiliği, 4 seri, kesin kurallar: fiyat/tarih/iletişim uydurma). |
| `run.py` | `FLASK_ENV`'e göre `create_app`, `0.0.0.0:5000`. |
| `app/__init__.py` | Fabrika: config yükle → CORS (`/api/*`) → `init_db` → blueprint'ler → `/health`. |
| `app/database.py` | `get_db`, `init_db` (leads: id, isim, telefon, mesaj, tarih), `lead_ekle`, `tum_leadler`, `lead_sil`. Hepsi `?` parametreli. |
| `app/routes.py` | `pages_bp` (`/`, `/dashboard`) ve `api_bp` (`POST /api/sohbet`, `POST /api/leads`, `GET /api/leads`, `DELETE /api/leads/<id>`). IP başına rate limit (bellekte), HTTP Basic ile `admin_gerekli` (parola = `ADMIN_PASSWORD`). |
| `app/services/ai_service.py` | `AIService.yanit_uret`: niyet eşleştirme (anahtar kelime) + Groq canlı mod; anahtar yoksa/hata olursa "akıllı demo" modu. Fikir/şaka üretici, ad ve telefon yakalama, öneri butonları, `form_oner`. |
| `app/templates/index.html`, `dashboard.html` | Karşılama ve panel arayüzleri. |
| `README.md` | **Dikkat:** dosyanın sonunda UTF-16 bozuk satırlar (`# watashistudio`) var; düzenlerken kodlamaya dikkat. |

**API sözleşmesi (kodda şu an):**
- `POST /api/sohbet` ← `{mesaj, gecmis}` → `{basari, cevap, oneriler, form_oner, ad, telefon, etkilesim, mod}`
- `POST /api/leads` ← `{isim, telefon, mesaj, kaynak}` → `{basari, mesaj, id}` (201)
- `GET /api/leads` (admin) → `{basari, leads:[...]}`
- `DELETE /api/leads/<id>` (admin)
- `GET /health` → `{durum, basari}`

> Not: Eğitmen dokümanlarında liste anahtarı `leadler`/`adaylar` geçiyor, kodda `leads` kullanılıyor. Wix Velo tarafı `veri.leads` okumalı.

## 4. Eğitmenin Ders Notlarından Çıkan Kritik Noktalar

1. **Groq modeli:** Eğitim dokümanındaki eski model (`llama-3.1-8b-instant`) artık çalışmıyor; değiştirilmesi gerekiyor. Ders sırasında önerilen: OpenAI'nin Groq'ta sunduğu ücretsiz **gpt-oss-20b** (dökümdeki model adı bozuk, kesin değil; Groq dokümanından doğrula). Groq sağlayıcısını silmek değil, **modeli değiştirmek** gerekiyor. Mevcut kod `llama-3.3-70b-versatile` kullanıyor → çalıştığı doğrulanmalı.
2. **requirements.txt:** Sürüm sabitlemeden (yalnız paket adı) kullanma tavsiyesi veriliyor; mevcut dosyada sürümler sabit (`flask==3.0.0` vb.).
3. **Render + SQLite:** Ücretsiz planda Render uyur ve disk kalıcı değil → deploy/uyanma sonrası lead verileri sıfırlanabilir. Bu aşamada yeni veritabanına (ör. Supabase) geçiş istenmiyor, SQLite yeterli. Admin kullanıcı/parola gibi kalıcı olması gerekenler Render Environment'a konmalı.
4. **CORS:** Atölyede `*` kolaylık için kabul; **canlı üründe doğru değil**, Wix adresine daraltılmalı (`CORS_ORIGINS`). Wix + Render haberleşmesinde en sık hata kaynağı.
5. **Rota adresi:** Render ana adresi + blueprint öneki (`/api`) + rota (`/sohbet`) birlikte doğru yazılmalı. Wix'te ana adres değişken olarak tutulup uzantılar eklenir. Yanlışsa terminal/log'da 404 görülür.
6. **Hata ayıklama:** Önce **Render logları** (200/300/400/500 kodları). Python'da `try/except`, JS'te `try/catch` + hata terminale/konsola yazdırılır.
7. **Commit mesajları:** Yapılan değişikliği/çözülen hatayı anlatmalı (ör. `fix: sohbet rotasında 404 — url_prefix düzeltildi`).
8. **.env ve Render:** `.env` repoya gitmez; Render'da Environment bölümüne anahtarlar tek tek elle girilir.
9. **Veri tipi:** Özel (Türkçe) karakterler için metin sütunlarında `NVARCHAR` önerildi (dökümde terim bozuk, kesin değil). **SQLite'ta TEXT zaten Unicode'u destekler**, değişiklik gerekmeyebilir.
10. **BUSINESS_CONTEXT:** Önce proje sahibi kendi bilgisiyle yazar; AI sadece dil düzeltir. Botun kimliği, kiminle konuştuğu, amacı ve bilgi sınırı net olmalı.
11. **Wix tarafı:** JavaScript (AI ile yazdırılabilir); bileşenlere ID ver, `wix-fetch` kullan, alan adlarını backend ile eşle.
12. **Sanal ortam (venv):** Kütüphaneleri projeye izole eder; zorunlu değil ama önerilir.

## 5. Teslim Edilecekler ve Değerlendirme

**Teslim:** GitHub deposu (`.env` hariç) · Canlı Render adresi · Wix site bağlantısı (2 arayüz) · Kısa README · Kısa sunum/demo.

| Kriter | Ağırlık |
|---|---|
| Mimari (SoC) | %30 |
| Çalışırlık (uçtan uca) | %25 |
| Kod kalitesi | %15 |
| Güvenlik (`?`, `.env`, CORS) | %10 |
| Hata yönetimi | %10 |
| Yayın + sunum | %10 |

**Zaman çizelgesi:** Gün1 config · 2 database · 3–4 ai_service · 5 routes · 6 fabrika · 7 test · 8 Wix · 9 GitHub+Render · 10 düzeltme/README/sunum.

**Render ayarları:** Build `pip install -r requirements.txt` · Start `gunicorn run:app` · Region Frankfurt · Env: `GROQ_API_KEY`, `SECRET_KEY`, `ADMIN_PASSWORD`, `FLASK_ENV=production`, `CORS_ORIGINS`.

**Wix Velo özeti:** `import { fetch } from 'wix-fetch'`; `$w.onReady`; Repeater'da her objede `_id` zorunlu, satır içinde `$item('#...')` kullan (asla `$w`). UX: karşılama = Z-pattern + glassmorphism sohbet kartı, panel = F-pattern (isim solda).

## 6. Eğitim Referansı: Python Cheat Sheet (özet)

Değişkenler/f-string, list/tuple/dict (comprehension, slicing, iç içe yapılar), if/elif/else, while (break/continue), fonksiyonlar (varsayılan, `*args`, `**kwargs`, return), sınıflar/kalıtım, `pathlib` ile dosya, `try/except/else` (çıplak `except` yerine `except Exception as e`), `json.dumps/loads`.

## 7. Bilinen Açıklar / Yapılacaklar (öneri; onay bekliyor)

- [ ] Groq modelinin güncelliğini doğrula (`GROQ_MODEL`).
- [x] (2026-10-20 yapıldı) `routes.py`'de hata yakalayan `except Exception:` blokları hatayı loglamıyor → `current_app.logger.exception(...)` / `print` ekle (eğitmen: hata terminale yazılmalı).
- [x] (2026-10-20 yapıldı) `ai_service.py` içinde AI hatası sessizce `pass` ediliyor → hata loglanmalı.
- [ ] Yönergeye göre AI hatasında **503** dönülmeli; `sohbet` şu an `500` dönüyor (servis içeride demo moduna düşüyor, bu bilinçli olabilir).
- [ ] `ADMIN_PASSWORD` `.env`'de `degistir-beni` → canlıya çıkmadan güçlü parolayla değiştir.
- [ ] `CORS_ORIGINS=*` → canlıda Wix adresine daralt.
- [ ] README.md'deki bozuk UTF-16 satırları temizle (UTF-8 yeniden yaz).
- [ ] `.gitignore` `*.db` içeriyor → canlıda DB sıfırlanma riski (bkz. 4.3).
- [ ] Wix Velo kodu henüz projede yok (docs/ klasörü yok).
- [ ] Commit mesaj standardı: tek commit var (`first commit`).

---

## 8. Çalışma Günlüğü (her işlemden sonra buraya eklenir)

| Tarih | Yapılan | Dosyalar |
|---|---|---|
| 2026-10-20 | Kullanıcının verdiği 5 kaynak (ayıklanmış notlar, ham transkript, Python cheat sheet PDF, SmartLead Proje Yönergesi PDF, Teknik Rehber PDF) incelendi; mevcut kod tabanı (config, run, app/*) okundu; bu not dosyası oluşturuldu. Kod değiştirilmedi. `.env` içeriği (anahtarlar) okunurken maskelendi, bu dosyaya yazılmadı. | `PROJE-NOTLARI.md` (yeni) |
| 2026-10-20 | Hata loglama eklendi: `routes.py` 4 `except` bloğunda `current_app.logger.exception(...)`, `ai_service.py`'de canlı AI hatası `print` ile loglanıyor. Playwright (Python) kuruldu; yerel e2e testi yazıldı ve geçti: health, sohbet (demo mod), form→lead 201, boş form 400, dashboard yetkisiz 401, dashboard kayıt listesi, silme, JS hatası yok. Test betiği repoda değil (geçici klasörde). | `app/routes.py`, `app/services/ai_service.py`, `PROJE-NOTLARI.md` |
| 2026-10-20 | Commit `afa0185` GitHub'a pushlandı (yalnız kullanıcı yazar; Co-Authored-By yok; contributors API'si tek kişi gösteriyor). `render.yaml` Blueprint eklendi (gizli değerler `sync:false`). Render hesabına erişimim yok → deploy adımları kullanıcıya bırakıldı. | `render.yaml`, `PROJE-NOTLARI.md` |
| 2026-10-20 | Render API anahtarıyla yeni servis açıldı: `watashistudio-ai` (srv-dbbt2n8473hc73cenh3g), https://watashistudio-ai.onrender.com, repo `watashistudio`, start `gunicorn run:app`, free/Frankfurt, autoDeploy açık. Eski `watashi_studio` servisine (başka repo, `gunicorn app:app`, update_failed) dokunulmadı. Canlı Playwright e2e: 10/10 geçti. **Bulgu:** `.env`'deki `GROQ_API_KEY` Groq'ta 401 Invalid API Key (36 karakter, kısa/yanlış) → sohbet `mod=demo`. Yeni anahtar Render Environment'a girilmeli. Render API anahtarı bu oturumda kullanıldı; kullanıcı silmeli. | `PROJE-NOTLARI.md` |
| 2026-10-20 | Yeni Groq anahtarı geçerli ama `llama-3.3-70b-versatile` Groq'ta artık yok (404). Hesaptaki modeller listelendi; eğitmenin önerdiği `openai/gpt-oss-20b` Türkçe testte doğru çalıştı → `config.py` ve `render.yaml` varsayılanı değiştirildi. Anahtar ve `GROQ_MODEL` Render Environment'a API ile girildi, yerel `.env` güncellendi (gitignore'lu). | `config.py`, `render.yaml`, `PROJE-NOTLARI.md` |
| 2026-10-20 | Deploy `c8dbb32` canlıda. Playwright e2e 10/10 geçti, sohbet artık `mod=canli` (gpt-oss-20b). Ek canlı sohbet kontrolleri: kimlik sorusu, fiyat sorusu (fiyat uydurmadı, formu önerdi, `form_oner=True`), konu dışı soru (siyaset → animasyona yönlendirdi) doğru. | `PROJE-NOTLARI.md` |
| 2026-10-20 | **Wix chatbot tasarımı (devam ediyor, YAYINLANMADI):** Site `My Site 1` (id aa35cbec-…, Studio editör, `veysicirik2002.wixstudio.com/watashistudio`). Playwright ile (gerçek Chrome, kalıcı profil, CDP 9333) Wix'e kullanıcı kendisi giriş yaptı. Anasayfaya eklenenler: (1) yuvarlak Düğme, simge = sohbet balonu, erişilebilir ad 'Sohbeti aç / kapat', 64px, Konum türü Sabitlenmiş / yeri Sayfa / sağ 24px alt 24px → önizlemede sağ altta çalışıyor. (2) Boş Kapsayıcı (sohbet paneli), Sabitlenmiş/Sayfa, sağ 24 alt 100. **Sorun:** panel boyutu 340×440 girilse de önizlemede 449×190 kalıyor; panel varsayılan görünür. **Kalan:** panel boyutu, içerik (başlık, mesaj metni, giriş kutusu, gönder, kapat), Etkileşimler ile balon→göster / ✕→gizle, 'yüklenince gizle', mobil. Mesajları Render API'ye bağlamak ayrıca Velo gerektirir (site şu an Velo kapalı). İlk denemede yanlışlıkla eklenen çizgi öğesi geri alındı. | Wix editör (repo dışı), `PROJE-NOTLARI.md` |
| 2026-10-20 | **Wix chatbot TAMAMLANDI ve YAYINLANDI** (My Site 1 → https://veysicirik2002.wixstudio.com/watashistudio). Wix'in kendi öğeleriyle (HTML gömme yok): sağ altta ekrana sabit balon düğme `#button1` (tek buton, aç/kapa), panel `#box1`, başlık `#text15`, cevap metni `#text16`, giriş `#input1`, gönder `#button4`. Velo etkinleştirildi; kod `wix/anasayfa-chatbot.velo.js` (repoda kopya) → `POST https://watashistudio-ai.onrender.com/api/sohbet`, cevap markdown'dan temizlenip ~230 karaktere kısaltılıyor. Panel boyutu alanları kabul etmiyordu; kenardan sürükleyerek 340×438 yapıldı. Mobil düzen ayrıca düzeltildi (yazı 5px→15px, panel balonun üstüne alındı). Canlı Playwright testi (masaüstü + mobil): balon sağ-alt, açılış gizli, aynı butonla aç/kapa, API 200 `mod=canli`, JS hatası yok. Kullanıcı revizyon verecek. Not: ilk denemede Wix siteyi istenmeden yayınlamıştı; sonradan bilinçli yayınlandı. | `wix/anasayfa-chatbot.velo.js`, `PROJE-NOTLARI.md` |
| 2026-10-21 | **Backend sadeleştirildi (yalnız API):** `app/templates` ve `app/static` silindi (arayüz Wix'te). `routes.py` yeniden yazıldı: tek Blueprint `/api`; sohbet/lead uçları, hepsi try/except + `current_app.logger.exception`. `ai_service.py` sadeleştirildi (demo/niyet motoru kaldırıldı; Groq hatası → `AIServiceError` → 503). Yeni: `app/error_log.py` (son 50 hata bellekte) + `GET /api/hatalar`; `app/rate_limit.py` (rate limit routes'tan ayrıldı); JSON 404/405/500 işleyicileri. **Admin girişi Basic Auth yerine `X-Admin-Key` başlığı** (değer = `ADMIN_PASSWORD`). `/dashboard` ve `/` kalktı → **lead paneli artık Wix'te yapılmalı** (GET /api/leads + başlık) ve 'Bize Ulaşın' formu Wix'ten POST /api/leads çağırmalı. `requirements.txt` sürümsüz (eğitmen tavsiyesi). README yeniden yazıldı (UTF-8). Yerel Playwright API testi 13/13, hata akışı doğrulandı (bozuk anahtar → 503 + /api/hatalar). Yanıt anahtarları: sohbet `{basari, cevap}`, hata `{basari:false, hata}` → Wix kodu uyumlu. | `app/*`, `requirements.txt`, `README.md`, `PROJE-NOTLARI.md` |
