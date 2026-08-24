from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response

import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import csv
from io import StringIO
import datetime
import re # Şifre güvenlik kontrolü için gerekli kütüphane

app = Flask(__name__)
app.secret_key = 'imece_kral_proje_2026'

# ==========================================
# --- İSİM MASKELEME FİLTRESİ ---
def isim_maskele(isim):
    if not isim: return ""
    kelimeler = str(isim).split()
    maskeli_kelimeler = [k[0] + "*" * (len(k) - 1) for k in kelimeler]
    return " ".join(maskeli_kelimeler)

app.jinja_env.filters['maskele'] = isim_maskele

# ==========================================
# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='290505', 
        database='ImeceDB'
    )

# ==========================================
# --- DİNAMİK FİYAT SÖZLÜĞÜ ---
FIYATLAR = {
    "Temel Erzak Kolisi": 1250.0, "Bebek Maması": 650.0, "Glutensiz Paket": 850.0,
    "Kışlık Bot": 900.0, "Kışlık Mont": 1400.0, "Okul Üniforması": 950.0, "Bebek Zıbın Seti": 450.0,
    "Kırtasiye Seti": 400.0, "Eğitim Tableti": 4500.0, "Okul Çantası": 600.0,
    "Tekerlekli Sandalye": 6500.0, "Hasta Bezi": 550.0, "Hijyen Paketi": 450.0,
    "Yakacak (Kömür)": 2500.0, "İşitme Cihazı Pili": 300.0,
    "Eğitim": 750.0, "Giyim": 1000.0, "Erzak / Gıda": 1250.0, "Yakacak": 2500.0,
    "Sağlık": 800.0, "Fatura Desteği": 500.0, "Barınma": 3000.0
}

def fiyat_bul(kategori_adi):
    if not kategori_adi: return 100.0
    aranan = str(kategori_adi).strip().lower()
    for k, v in FIYATLAR.items():
        if k.strip().lower() == aranan: return v
    return 100.0

# ==========================================
# --- LOG KAYIT MOTORU ---
def log_kaydet(kullanici_id, islem):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO SistemLog (KullaniciID, Islem) VALUES (%s, %s)", (kullanici_id, islem))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        pass

# ==========================================
# --- GİRİŞ VE KAYIT SİSTEMİ ---
@app.route('/')
def index():
    # === ANA SAYFA SAYAÇ İSTATİSTİKLERİ ===
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Kullanici WHERE Rol = 'Bagisci'")
        t_bagisci = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Talep")
        t_talep = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Kupon WHERE Durum = 'Used'")
        t_teslim = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Talep WHERE Durum = 'Karşılandı'")
        t_tamamlanan = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
    except Exception as e:
        t_bagisci, t_talep, t_teslim, t_tamamlanan = 0, 0, 0, 0
        
    return render_template('index.html', t_bagisci=t_bagisci, t_talep=t_talep, t_teslim=t_teslim, t_tamamlanan=t_tamamlanan)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        adsoyad = request.form['adsoyad']
        email = request.form['email']
        sifre = request.form['sifre']
        rol = request.form['rol']
        anahtar = request.form.get('anahtar') 
        # === YENİ EKLENEN: ŞEHİR BİLGİSİ ===
        sehir = request.form.get('sehir', 'Belirtilmedi')

        # === ŞİFRE GÜVENLİK KONTROLÜ ===
        if len(sifre) < 6 or not re.search(r"[A-Z]", sifre) or not re.search(r"[0-9]", sifre) or not re.search(r"[^A-Za-z0-9]", sifre):
            flash('Şifreniz en az 6 karakter olmalı; en az 1 büyük harf, 1 rakam ve 1 özel karakter (-, ., vb.) içermelidir.', 'danger')
            return redirect(url_for('kayit'))

        sifre_hash = generate_password_hash(sifre)
        
        kayit_rolu = 'BekleyenEsnaf' if rol == 'Esnaf' else rol
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Kullanici WHERE Email = %s", (email,))
        if cursor.fetchone():
            flash('Bu e-posta adresi zaten sistemde kayıtlı!', 'danger')
            return redirect(url_for('kayit'))
            
        # Sorgu Şehir Parametresiyle Güncellendi
        cursor.execute("INSERT INTO Kullanici (AdSoyad, Email, SifreHash, Rol, KurtarmaAnahtari, Sehir) VALUES (%s, %s, %s, %s, %s, %s)", (adsoyad, email, sifre_hash, kayit_rolu, anahtar, sehir))
        
        yeni_id = cursor.lastrowid
        conn.commit()
        
        if kayit_rolu == 'BekleyenEsnaf':
            flash('İşletme kaydınız alındı! Yöneticilerimiz doğruladıktan sonra hesabınız aktifleştirilecektir.', 'warning')
        else:
            flash('Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
            
        log_kaydet(yeni_id, f"Sisteme yeni kayıt oldu ({kayit_rolu} - {sehir})")
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('kayit.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    sifre = request.form['sifre']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT KullaniciID, AdSoyad, Email, SifreHash, Rol FROM Kullanici WHERE Email = %s", (email,))
    kullanici = cursor.fetchone()
    cursor.close()
    conn.close()

    if kullanici and check_password_hash(kullanici[3], sifre):
        if kullanici[4] == 'BekleyenEsnaf':
            flash('Hesabınız güvenlik onayı aşamasındadır. Yöneticilerimiz doğruladıktan sonra giriş yapabilirsiniz.', 'warning')
            return redirect(url_for('index'))

        session['kullanici_id'] = kullanici[0]
        session['adsoyad'] = kullanici[1]
        session['rol'] = kullanici[4]
        log_kaydet(kullanici[0], "Sisteme giriş yaptı.")
        
        if kullanici[4] == 'Admin': return redirect(url_for('admin_panel'))
        elif kullanici[4] == 'Bagisci': return redirect(url_for('bagisci_panel'))
        elif kullanici[4] == 'IhtiyacSahibi': return redirect(url_for('ihtiyac_panel'))
        elif kullanici[4] == 'Esnaf': return redirect(url_for('esnaf_panel'))
    else:
        flash('Hatalı e-posta veya şifre!', 'danger')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if 'kullanici_id' in session: 
        log_kaydet(session['kullanici_id'], "Çıkış yaptı.")
    session.clear()
    return redirect(url_for('index'))

# ==========================================
# --- İHTİYAÇ SAHİBİ MODÜLÜ ---
@app.route('/ihtiyac')
def ihtiyac_panel():
    if 'kullanici_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Talep WHERE KullaniciID = %s ORDER BY OlusturmaTarihi DESC", (session['kullanici_id'],))
    talepler = cursor.fetchall()
    toplam = len(talepler)
    bekleyen = sum(1 for t in talepler if t[5] == 'Beklemede')
    karsilanan = sum(1 for t in talepler if t[5] == 'Karşılandı')
    
    cursor.execute("SELECT k.KuponKodu, p.PaketAdi, k.Durum FROM Kupon k JOIN UrunPaketi p ON k.PaketID = p.PaketID WHERE k.KullaniciID = %s ORDER BY k.KuponID DESC", (session['kullanici_id'],))
    kuponlar = cursor.fetchall()
    
    # === YENİ: SİSTEMDEKİ ESNAFLARI ÇEKİYORUZ ===
    cursor.execute("SELECT KullaniciID, AdSoyad, Sehir FROM Kullanici WHERE Rol = 'Esnaf' ORDER BY Sehir, AdSoyad")
    aktif_esnaflar = cursor.fetchall()
    
    cursor.close()
    conn.close()
    # esnaflar verisi de template'e gönderildi
    return render_template('ihtiyac.html', talepler=talepler, toplam=toplam, bekleyen=bekleyen, karsilanan=karsilanan, kuponlar=kuponlar, esnaflar=aktif_esnaflar)

@app.route('/talep_olustur', methods=['POST'])
def talep_olustur():
    if 'kullanici_id' not in session or session['rol'] != 'IhtiyacSahibi': return redirect(url_for('index'))
    
    kategori = request.form['kategori']
    konum = request.form['konum']
    detay = request.form['detay']
    adet = int(request.form['adet'])
    
    # === YENİ: SEÇİLEN ESNAFI YAKALIYORUZ ===
    esnaf_id = request.form.get('esnaf_id')
    if not esnaf_id: esnaf_id = None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Sorgu TeslimatEsnafID ile güncellendi
    cursor.execute("INSERT INTO Talep (KullaniciID, Kategori, Konum, Detay, Adet, KarsilananAdet, TeslimatEsnafID) VALUES (%s, %s, %s, %s, %s, 0, %s)", (session['kullanici_id'], kategori, konum, detay, adet, esnaf_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    log_kaydet(session['kullanici_id'], f"Yeni talep oluşturdu: {kategori} (Hedef Esnaf ID: {esnaf_id})")
    flash('Talep başarıyla oluşturuldu!', 'success')
    return redirect(url_for('ihtiyac_panel'))

# ==========================================
# --- BAĞIŞÇI VE KISMİ ÖDEME MODÜLÜ ---
@app.route('/bagisci')
def bagisci_panel():
    if 'kullanici_id' not in session or session['rol'] != 'Bagisci': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT t.TalepID, t.Kategori, t.Konum, t.Detay, t.OlusturmaTarihi, k.AdSoyad, t.Adet, t.KarsilananAdet FROM Talep t JOIN Kullanici k ON t.KullaniciID = k.KullaniciID WHERE t.Durum = 'Beklemede' ORDER BY t.OlusturmaTarihi DESC")
    ham_talepler = cursor.fetchall()
    
    guncel_talepler = []
    for t in ham_talepler:
        istenen_adet = t[6] if t[6] is not None and t[6] > 0 else 1
        mevcut_karsilanan = t[7] if t[7] is not None else 0
        kalan_adet = istenen_adet - mevcut_karsilanan
        yuzde_oran = int((mevcut_karsilanan / istenen_adet) * 100)
        
        if kalan_adet > 0:
            guncel_talepler.append({
                'id': t[0], 
                'kategori': t[1], 
                'konum': t[2], 
                'detay': t[3],
                'tarih': t[4].strftime('%d.%m.%Y') if t[4] else '',
                'kullanici': t[5], 
                'istenen': istenen_adet, 
                'karsilanan': mevcut_karsilanan,
                'yuzde': yuzde_oran, 
                'kalan': kalan_adet
            })
    
    cursor.execute("""
        SELECT b.BagisID, p.PaketAdi, b.Tutar, GROUP_CONCAT(k.KuponKodu SEPARATOR ' | ')
        FROM Bagis b 
        JOIN UrunPaketi p ON b.PaketID = p.PaketID 
        JOIN Kupon k ON b.BagisID = k.BagisID 
        WHERE b.KullaniciID = %s 
        GROUP BY b.BagisID, p.PaketAdi, b.Tutar 
        ORDER BY b.BagisID DESC
    """, (session['kullanici_id'],))
    gecmis_bagislar = cursor.fetchall()
    
    # === RÜTBE VE ROZET MATEMATİĞİ ===
    bagis_sayisi = len(gecmis_bagislar)
    
    if bagis_sayisi == 0:
        rutbe, ikon, renk = "Yeni Gönüllü", "bi-star", "secondary"
    elif bagis_sayisi < 5:
        rutbe, ikon, renk = "Yardımsever", "bi-star-half", "info"
    elif bagis_sayisi < 10:
        rutbe, ikon, renk = "Gümüş Kalp", "bi-heart-fill", "secondary"
    elif bagis_sayisi < 20:
        rutbe, ikon, renk = "Altın Yürek", "bi-award-fill", "warning"
    else:
        rutbe, ikon, renk = "İyilik Kahramanı", "bi-trophy-fill", "danger"
    # ===============================================

    cursor.close()
    conn.close()
    return render_template('bagisci.html', talepler=guncel_talepler, gecmis_bagislar=gecmis_bagislar, 
                           bagis_sayisi=bagis_sayisi, rutbe=rutbe, ikon=ikon, renk=renk)

@app.route('/odeme/<int:talep_id>')
def odeme_ekrani(talep_id):
    if 'kullanici_id' not in session or session['rol'] != 'Bagisci': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TalepID, Kategori, Adet, KarsilananAdet FROM Talep WHERE TalepID = %s", (talep_id,))
    talep = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not talep: return redirect(url_for('bagisci_panel'))
    
    birim_fiyat = fiyat_bul(talep[1])
    istenen = talep[2] if talep[2] else 1
    karsilanan = talep[3] if talep[3] else 0
    kalan_limit = istenen - karsilanan
    
    if kalan_limit < 1: kalan_limit = 1
    
    return render_template('odeme.html', talep=talep, birim_fiyat=birim_fiyat, kalan_limit=kalan_limit)

@app.route('/bagis_yap/<int:talep_id>', methods=['POST'])
def bagis_yap(talep_id):
    if 'kullanici_id' not in session or session['rol'] != 'Bagisci': return redirect(url_for('index'))
    bagis_adet = int(request.form.get('bagis_adet', 1))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT Kategori, Adet, KarsilananAdet, KullaniciID FROM Talep WHERE TalepID = %s", (talep_id,))
    talep_verisi = cursor.fetchone()
    if not talep_verisi: return redirect(url_for('bagisci_panel'))

    istenen_toplam = talep_verisi[1] if talep_verisi[1] else 1
    eski_karsilanan = talep_verisi[2] if talep_verisi[2] else 0
    yeni_toplam_karsilanan = eski_karsilanan + bagis_adet
    
    yeni_durum = 'Karşılandı' if yeni_toplam_karsilanan >= istenen_toplam else 'Beklemede'
    
    cursor.execute("UPDATE Talep SET KarsilananAdet = %s, Durum = %s WHERE TalepID = %s", (yeni_toplam_karsilanan, yeni_durum, talep_id))

    birim_fiyat = fiyat_bul(talep_verisi[0])
    toplam_odeme = bagis_adet * birim_fiyat
    
    cursor.execute("SELECT PaketID FROM UrunPaketi WHERE PaketAdi = %s", (talep_verisi[0],))
    paket = cursor.fetchone()
    if not paket:
        cursor.execute("INSERT INTO UrunPaketi (PaketAdi, Fiyat, Adet) VALUES (%s, %s, %s)", (talep_verisi[0], birim_fiyat, 1))
        paket_id = cursor.lastrowid
    else: 
        paket_id = paket[0]

    cursor.execute("INSERT INTO Bagis (KullaniciID, PaketID, Tutar) VALUES (%s, %s, %s)", (session['kullanici_id'], paket_id, toplam_odeme))
    bagis_id = cursor.lastrowid
    
    uretilen_kuponlar = []
    for _ in range(bagis_adet):
        kupon_kodu = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("INSERT INTO Kupon (KuponKodu, KullaniciID, BagisID, PaketID, Durum) VALUES (%s, %s, %s, %s, 'Active')", (kupon_kodu, talep_verisi[3], bagis_id, paket_id))
        uretilen_kuponlar.append(kupon_kodu)
        
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Bağış başarılı! Güvenli Kodlarınız: {" | ".join(uretilen_kuponlar)}', 'success')
    return redirect(url_for('bagisci_panel'))

# ==========================================
# --- ESNAF MODÜLÜ ---
@app.route('/esnaf', methods=['GET', 'POST'])
def esnaf_panel():
    if 'kullanici_id' not in session or session['rol'] != 'Esnaf': return redirect(url_for('index'))
    kupon_detay = None
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        if 'kod_sorgula' in request.form:
            cursor.execute("SELECT k.KuponID, k.KuponKodu, k.Durum, u.AdSoyad, p.PaketAdi FROM Kupon k JOIN Kullanici u ON k.KullaniciID = u.KullaniciID JOIN UrunPaketi p ON k.PaketID = p.PaketID WHERE k.KuponKodu = %s", (request.form['kupon_kodu'],))
            kupon_detay = cursor.fetchone()
            if not kupon_detay: flash('Kupon bulunamadı!', 'danger')
        
        elif 'kod_onayla' in request.form:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            cursor.execute("UPDATE Kupon SET Durum = 'Used', EsnafID = %s, UsedAt = CURRENT_TIMESTAMP WHERE KuponID = %s", (session['kullanici_id'], request.form['kupon_id']))
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
            conn.commit()
            flash('Ürün başarıyla teslim edildi!', 'success')
            return redirect(url_for('esnaf_panel'))

    cursor.execute("SELECT k.KuponKodu, u.AdSoyad, p.PaketAdi, k.UsedAt FROM Kupon k JOIN Kullanici u ON k.KullaniciID = u.KullaniciID JOIN UrunPaketi p ON k.PaketID = p.PaketID WHERE k.EsnafID = %s AND k.Durum = 'Used' ORDER BY k.UsedAt DESC", (session['kullanici_id'],))
    gecmis = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('esnaf.html', kupon_detay=kupon_detay, gecmis_islemler=gecmis)

@app.route('/esnaf/rapor_indir')
def esnaf_rapor_indir():
    if 'kullanici_id' not in session or session['rol'] != 'Esnaf': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT k.KuponKodu, u.AdSoyad, p.PaketAdi, k.UsedAt FROM Kupon k JOIN Kullanici u ON k.KullaniciID = u.KullaniciID JOIN UrunPaketi p ON k.PaketID = p.PaketID WHERE k.EsnafID = %s AND k.Durum = 'Used' ORDER BY k.UsedAt DESC", (session['kullanici_id'],))
    gecmis = cursor.fetchall()
    si = StringIO()
    cw = csv.writer(si, delimiter=';') 
    cw.writerow(['Kupon Kodu', 'Ihtiyac Sahibi', 'Teslim Edilen Urun', 'Islem Tarihi'])
    cw.writerows(gecmis)
    output = make_response(si.getvalue().encode('utf-8-sig'))
    output.headers["Content-Disposition"] = "attachment; filename=Esnaf_Raporu.csv"
    output.headers["Content-type"] = "text/csv"
    cursor.close()
    conn.close()
    return output 

@app.route('/profil/sehir_guncelle', methods=['POST'])
def sehir_guncelle():
    if 'kullanici_id' not in session or session['rol'] != 'Esnaf': return redirect(url_for('index'))
    yeni_sehir = request.form['yeni_sehir']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Kullanici SET Sehir = %s WHERE KullaniciID = %s", (yeni_sehir, session['kullanici_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f'Hizmet bölgeniz {yeni_sehir} olarak güncellendi!', 'success')
    return redirect(url_for('profil'))

# ==========================================
# --- ADMIN MODÜLÜ VE ONAY SİSTEMİ ---
@app.route('/admin')
def admin_panel():
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT KullaniciID, AdSoyad, Email, DATE_FORMAT(CreatedAt, '%d.%m.%Y') FROM Kullanici WHERE Rol = 'BekleyenEsnaf' ORDER BY CreatedAt DESC")
    onay_bekleyen_esnaflar = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM Talep")
    toplam_talep = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Talep WHERE Durum = 'Beklemede'")
    bekleyen = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Talep WHERE Durum = 'Karşılandı'")
    tamamlanan = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Kupon")
    toplam_bagis = cursor.fetchone()[0]
    
    cursor.execute("SELECT t.TalepID, t.Kategori, t.Konum, t.Detay, t.Durum, t.OlusturmaTarihi, k.AdSoyad FROM Talep t JOIN Kullanici k ON t.KullaniciID = k.KullaniciID ORDER BY t.OlusturmaTarihi DESC")
    tum_talepler = cursor.fetchall()
    
    cursor.execute("SELECT l.Islem, l.Tarih, k.AdSoyad, k.Rol FROM SistemLog l JOIN Kullanici k ON l.KullaniciID = k.KullaniciID ORDER BY l.Tarih DESC LIMIT 50")
    loglar = cursor.fetchall()

    cursor.execute("""
        SELECT MONTH(OlusturmaTarihi) AS Ay, COUNT(*) AS Sayi 
        FROM Talep 
        WHERE YEAR(OlusturmaTarihi) = YEAR(CURRENT_DATE())
        GROUP BY MONTH(OlusturmaTarihi)
        ORDER BY MONTH(OlusturmaTarihi)
    """)
    aylik_veriler = cursor.fetchall()
    turkce_aylar = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
    
    grafik_aylar = [turkce_aylar.get(satir[0], str(satir[0])) for satir in aylik_veriler]
    grafik_degerler = [satir[1] for satir in aylik_veriler]
    if not grafik_aylar:
        grafik_aylar, grafik_degerler = ['Ocak', 'Şubat', 'Mart'], [0, 0, 0]

    cursor.close()
    conn.close()
    
    return render_template('admin.html', 
                           toplam_talep=toplam_talep, bekleyen_talep=bekleyen, 
                           tamamlanan_talep=tamamlanan, toplam_bagis=toplam_bagis, 
                           tum_talepler=tum_talepler, loglar=loglar,
                           grafik_aylar=grafik_aylar, grafik_degerler=grafik_degerler,
                           onay_bekleyen_esnaflar=onay_bekleyen_esnaflar)

@app.route('/admin/talep_sil/<int:talep_id>', methods=['POST'])
def talep_sil(talep_id):
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Talep WHERE TalepID = %s", (talep_id,))
    conn.commit()
    log_kaydet(session['kullanici_id'], f"Admin yetkisiyle talep silindi (ID: {talep_id})")
    cursor.close()
    conn.close()
    flash('Talep sistemden başarıyla silindi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/talep_tamamla/<int:talep_id>', methods=['POST'])
def talep_tamamla(talep_id):
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Talep SET Durum = 'Karşılandı' WHERE TalepID = %s", (talep_id,))
    conn.commit()
    log_kaydet(session['kullanici_id'], f"Admin yetkisiyle talep manuel tamamlandı (ID: {talep_id})")
    cursor.close()
    conn.close()
    flash('Talep başarıyla tamamlandı olarak işaretlendi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/rapor_indir')
def admin_rapor_indir():
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT t.TalepID, k.AdSoyad, t.Kategori, t.Konum, t.Durum, t.OlusturmaTarihi FROM Talep t JOIN Kullanici k ON t.KullaniciID = k.KullaniciID")
    talepler = cursor.fetchall()
    si = StringIO()
    cw = csv.writer(si, delimiter=';') 
    cw.writerow(['ID', 'İhtiyaç Sahibi', 'Kategori', 'Konum', 'Sistem Durumu', 'Tarih'])
    cw.writerows(talepler)
    output = make_response(si.getvalue().encode('utf-8-sig'))
    output.headers["Content-Disposition"] = "attachment; filename=Imece_Talepler.csv"
    output.headers["Content-type"] = "text/csv"
    cursor.close()
    conn.close()
    return output

@app.route('/admin/esnaf_onayla/<int:esnaf_id>', methods=['POST'])
def esnaf_onayla(esnaf_id):
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Kullanici SET Rol = 'Esnaf' WHERE KullaniciID = %s", (esnaf_id,))
    conn.commit()
    log_kaydet(session['kullanici_id'], f"Esnaf hesabı onaylandı (ID: {esnaf_id})")
    cursor.close()
    conn.close()
    flash('Esnaf hesabı başarıyla onaylandı ve sisteme erişimi açıldı.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/esnaf_reddet/<int:esnaf_id>', methods=['POST'])
def esnaf_reddet(esnaf_id):
    if 'kullanici_id' not in session or session['rol'] != 'Admin': return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM SistemLog WHERE KullaniciID = %s", (esnaf_id,))
    cursor.execute("DELETE FROM Kullanici WHERE KullaniciID = %s", (esnaf_id,))
    conn.commit()
    log_kaydet(session['kullanici_id'], f"Onay bekleyen esnaf reddedildi/silindi (ID: {esnaf_id})")
    cursor.close()
    conn.close()
    flash('Esnaf başvurusu reddedildi ve sistemden silindi.', 'danger')
    return redirect(url_for('admin_panel'))

# ==========================================
# --- PROFİL MODÜLÜ ---
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'kullanici_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        eski_sifre = request.form['eski_sifre']
        yeni_sifre = request.form['yeni_sifre']
        
        cursor.execute("SELECT SifreHash FROM Kullanici WHERE KullaniciID = %s", (session['kullanici_id'],))
        kullanici = cursor.fetchone()
        if kullanici and check_password_hash(kullanici[0], eski_sifre):
            
            # === PROFİLDE ŞİFRE DEĞİŞTİRİRKEN GÜVENLİK KONTROLÜ ===
            if len(yeni_sifre) < 6 or not re.search(r"[A-Z]", yeni_sifre) or not re.search(r"[0-9]", yeni_sifre) or not re.search(r"[^A-Za-z0-9]", yeni_sifre):
                flash('Yeni şifreniz en az 6 karakter olmalı; en az 1 büyük harf, 1 rakam ve 1 özel karakter (-, ., vb.) içermelidir.', 'danger')
                return redirect(url_for('profil'))
            # ====================================================================
            
            yeni_hash = generate_password_hash(yeni_sifre)
            cursor.execute("UPDATE Kullanici SET SifreHash = %s WHERE KullaniciID = %s", (yeni_hash, session['kullanici_id']))
            conn.commit()
            flash('Şifreniz güncellendi.', 'success')
        else:
            flash('Mevcut şifrenizi hatalı girdiniz.', 'danger')
        return redirect(url_for('profil'))
        
    cursor.execute("SELECT AdSoyad, Email, Rol, DATE_FORMAT(CreatedAt, '%d.%m.%Y'), Sehir FROM Kullanici WHERE KullaniciID = %s", (session['kullanici_id'],))
    kullanici_bilgi = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('profil.html', kullanici=kullanici_bilgi)

# =========== ŞİFRE SIFIRLAMA ROTASI ===========
@app.route('/sifre-sifirla', methods=['GET', 'POST'])
def sifre_sifirla():
    if request.method == 'POST':
        email = request.form.get('email')
        anahtar = request.form.get('anahtar')
        yeni_sifre = request.form.get('yeni_sifre')
        
        # === ŞİFRE SIFIRLARKEN GÜVENLİK KONTROLÜ ===
        if len(yeni_sifre) < 6 or not re.search(r"[A-Z]", yeni_sifre) or not re.search(r"[0-9]", yeni_sifre) or not re.search(r"[^A-Za-z0-9]", yeni_sifre):
            return "<script>alert('Yeni şifreniz en az 6 karakter olmalı; en az 1 büyük harf, 1 rakam ve 1 özel karakter (-, ., vb.) içermelidir!'); window.history.back();</script>"
        # =========================================================

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Kullanici WHERE Email = %s AND KurtarmaAnahtari = %s", (email, anahtar))
        user = cursor.fetchone()
        
        if user:
            from werkzeug.security import generate_password_hash
            yeni_hash = generate_password_hash(yeni_sifre)
            cursor.execute("UPDATE Kullanici SET SifreHash = %s WHERE Email = %s", (yeni_hash, email))
            conn.commit() 
            cursor.close()
            conn.close()
            return "<script>alert('Şifreniz başarıyla sıfırlandı!'); window.location.href='/';</script>"
        else:
            cursor.close()
            conn.close()
            return "<script>alert('E-posta veya Kurtarma Anahtarı hatalı!'); window.history.back();</script>"
            
    return render_template('sifre_sifirla.html')


# --- VERİTABANI OTOMATİK YAMA MOTORU ---
def db_yama_yap():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Rol sınırını kaldırıyoruz
        cursor.execute("ALTER TABLE Kullanici MODIFY COLUMN Rol VARCHAR(50)")
        
        # Kısmi bağış sütunu yoksa ekliyoruz
        try:
            cursor.execute("ALTER TABLE Talep ADD COLUMN KarsilananAdet INT DEFAULT 0")
            cursor.execute("UPDATE Talep SET KarsilananAdet = 0 WHERE KarsilananAdet IS NULL")
        except:
            pass

        # Kurtarma Anahtarı sütunu yoksa ekliyoruz
        try:
            cursor.execute("ALTER TABLE Kullanici ADD COLUMN KurtarmaAnahtari VARCHAR(100) DEFAULT 'imece123'")
        except:
            pass

        # === YENİ EKLENEN YAMALAR ===
        try:
            cursor.execute("ALTER TABLE Kullanici ADD COLUMN Sehir VARCHAR(50) DEFAULT 'Belirtilmedi'")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE Talep ADD COLUMN TeslimatEsnafID INT NULL")
        except:
            pass
        # =============================

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        pass

if __name__ == '__main__':
    db_yama_yap()
    app.run(debug=True)