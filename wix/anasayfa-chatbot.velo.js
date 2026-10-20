// Watashi AI sohbet balonu: tek buton (#button1) paneli açar/kapatır.
// Mesajlar Render'daki Flask API'ye gider: POST /api/sohbet
const API_URL = 'https://watashistudio-ai.onrender.com';
let gecmis = [];
let bekliyor = false;

$w.onReady(function () {
    // Açılışta panel kapalı
    $w('#box1').hide();
    $w('#input1').placeholder = 'Bir şey sor...';
    $w('#input1').label = '';
    $w('#button4').label = 'Gönder';

    // Tek buton: açıksa kapatır, kapalıysa açar
    $w('#button1').onClick(() => {
        if ($w('#box1').hidden) {
            $w('#box1').show('fade', { duration: 200 });
        } else {
            $w('#box1').hide('fade', { duration: 200 });
        }
    });

    $w('#button4').onClick(mesajGonder);
    $w('#input1').onKeyPress((event) => {
        if (event.key === 'Enter') { mesajGonder(); }
    });
});

async function mesajGonder() {
    const mesaj = ($w('#input1').value || '').trim();
    if (!mesaj || bekliyor) { return; }

    bekliyor = true;
    $w('#input1').value = '';
    $w('#text16').text = 'Düşünüyorum... 🎬';

    try {
        // Render ana adresi + /api öneki + /sohbet rotası
        const res = await fetch(API_URL + '/api/sohbet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mesaj: mesaj, gecmis: gecmis.slice(-8) })
        });
        const veri = await res.json();

        if (veri.basari) {
            $w('#text16').text = cevapSigdir(veri.cevap);
            gecmis.push({ role: 'user', content: mesaj });
            gecmis.push({ role: 'assistant', content: veri.cevap });
        } else {
            $w('#text16').text = veri.hata || 'Bir sorun oluştu, tekrar dener misin?';
        }
    } catch (err) {
        // Hata kaynağı tarayıcı konsolunda görünsün
        console.error('[chatbot] /api/sohbet hatası:', err);
        $w('#text16').text = 'Şu an bağlanamıyorum, birazdan tekrar dene. 🐢';
    } finally {
        bekliyor = false;
    }
}

// Markdown işaretlerini temizler ve cevabı panele sığacak uzunluğa kısaltır
function cevapSigdir(metin) {
    let t = String(metin || '').replace(/[*_#`>]/g, '').replace(/\s+/g, ' ').trim();
    const SINIR = 230;
    if (t.length > SINIR) {
        const kes = t.slice(0, SINIR);
        const son = Math.max(kes.lastIndexOf('. '), kes.lastIndexOf('! '), kes.lastIndexOf('? '));
        t = (son > 80 ? kes.slice(0, son + 1) : kes.trim() + '…');
    }
    return t;
}
