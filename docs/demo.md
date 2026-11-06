# Canlı demo senaryosu

Süre: ~10 dakika. Her adımda **ne gösterildiği** ve **ne söyleneceği** yazıyor.

## Demo öncesi (5 dakika önce)

```bash
cd backend && .venv/bin/uvicorn app.main:app --port 8000      # terminal 1
cd frontend && npm run dev                                     # terminal 2
cd backend && .venv/bin/python -m app.warm_cache              # bir kez: demo rotalarını cache'e al
cd backend && .venv/bin/pytest -q                              # 105 passed
```

- `rules.yaml`'ın varsayılan sırada olduğundan emin olun: `total_cost`, sonra `hq_proximity` (`git diff rules.yaml` boş olmalı).
- Tarayıcıda http://localhost:3000 ve http://localhost:8000/docs açık olsun.

## 1. Yeni firma ekleme

**Taşıyıcılar → Yeni taşıyıcı:** `Z-Logistics`, merkez `Miami`, 40 ft, Dry, $0.30/mil, maks. mesafe boş.

> "Firmalar veritabanında; seçim kodunda hiçbir firma adı geçmiyor. Kaydettiğim anda bir sonraki seçime giriyor."

Doğrulama: Yeni Sipariş → Form: Miami → Orlando, 40 ft, Dry → **Z-Logistics $70.50** (S $94'ün önünde).
Sonra Z-Logistics'i silin (onay penceresi) → geçmişteki kaydı hâlâ açılır: *snapshot*.

## 2. Firma açıklamasını düzenleme

**S-Logistics → düzenle → Açıklama:** `Orlando hattında bu ay araç sıkıntısı yaşıyoruz, teslimatlar gecikebilir.`

> "Serbest metin açıklama asla kural değildir; yanlış okunursa firma haksız yere elenirdi. Jev'e Noul sorusu soruluyor ve sadece uyarı üretiyor."

## 3. Yeni taşıma siparişi (serbest metin)

**Yeni Sipariş → Serbest metin:** `Miami'den Orlando'ya 40'lık kuru yük konteyneri taşınacak.`

## 4. En uygun firma

Sonuç: **S-Logistics, $94** (case test #2). "Jev yorumu" tablosunda 4 alan, güvenler 1.00.

> "Jev sadece seçeneklerden seçti ve ne kadar emin olduğunu söyledi. Karar ve ücret kodda."

## 5. Seçim gerekçesi

Gösterin:
- Gerekçe: *"S-Logistics seçildi: toplam ücret daha avantajlı ($94.00; sıradaki M-Logistics: $235.00)."*
- **Diğer uygun firmalar** (elenmedi, geride kaldı) ve **Elenen firmalar** (tüm gerekçeleriyle) ayrı listeler.
- **Firma notu uyarısı**: S-Logistics'in notu (~0.9 olasılık); seçim değişmedi.

Ek gösterim (belirsizlik): `Need a reefer box from Ft. Lauderdale to Miami asap` → **needs_review**: *"Konteyner boyutu belirtilmemiş"*; form dolu açılır, 40 ft seçilip onaylanır → **M-Logistics $30** (case test #1).

> "Model emin değilse sistem tahmin etmiyor, soruyor."

## 6. Sıralama kuralını değiştirme

Önce Form ile **Jacksonville → Savannah, 45 ft, Dry** → **S-Logistics $56** (A-Logistics $280, geride).

**Kurallar → Merkez yakınlığı ↑ → Kaydet.** `git diff rules.yaml` ile dosyanın değiştiğini gösterin.

> "Kural sırası rules.yaml'da; arayüz dosyayı yazıyor, kod değişmiyor. Bilinmeyen bir kriter adı 400 ile reddedilir."

## 7. Aynı siparişi tekrar çalıştırma

**Seçim Sonuçları → Jacksonville → Savannah kaydı → Tekrar çalıştır** → **A-Logistics $280**: merkezi Jacksonville'de (0 mil), S'nin merkezi 200 mil uzakta.

İki kaydı karşılaştırın: eski kayıt hâlâ S-Logistics ve eski kural sırasını gösteriyor (audit trail).

Sonra **Kurallar → Toplam ücret ↑ → Kaydet** ile varsayılana dönün.

**Ek (yeni kriter canlı ekleme sorusu gelirse):** Taşıyıcılar'da S-Logistics'e Güvenilirlik %80, M-Logistics'e %95 girin → Kurallar'da **Güvenilirlik**'i açıp en üste alın → Miami → Orlando, 40 ft, Dry → **M-Logistics** ("S-Logistics: Güvenilirlik 15 puan daha düşük"). Kriter `ranking.py`'de tek bir sınıf; şema değişmedi.

**Ek (yazım hatası):** Form'da çıkış şehrine `Miammi` yazıp alandan çıkın → "Miami mi demek istediniz?".

**Ek (çoklu yük):** Miami → Fort Lauderdale, 20 ft, Reefer + Hazardous → tek uygun firma **M-Logistics**; S'nin iki ayrı yük tipi gerekçesi var.

## Olası sorular

| Soru | Kısa cevap |
|---|---|
| Neden ücret hesabını Jev yapmıyor? | Denetlenebilir, tekrarlanabilir ve test edilebilir olması gerekiyor; LLM aritmetiği garanti değil. ADR 0001. |
| Confidence 0.75 nereden? | Başlangıç eşiği; `rules.yaml`'da. Alan bazında, en zayıf alan belirleyici. |
| Tablo dışı rota? | Nominatim + OSRM yol mesafesi, cache'li. Cevap yoksa `unknown_route`; kuş uçuşu kullanılmıyor (fiyatı %13 düşük gösterirdi). |
| Yeni kriter (reliability) nasıl eklenir? | `ranking.py`'de bir sınıf + registry + `rules.yaml`'a ad. Şema değişmez; değer `attributes`'tan. |
| Jev çökerse? | Metin siparişler `jev_unavailable` ile forma yönlenir; yapılandırılmış siparişler ve tüm seçim mantığı çalışmaya devam eder. |
| Neden Next.js? | Ekip/aday deneyimi ve etkileşimli kural ekranı; iş mantığı tamamen API'de (API-first). |
