import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import datetime
import time

# --- AYARLAR ---
SPOTIPY_CLIENT_ID = '0c7890ae46254cf1b3c06070d7f982dd'
SPOTIPY_CLIENT_SECRET = '0b79d067a0bf43ba9add6eb44a65d0ba'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'
LASTFM_API_KEY = '955e588c82d7c7e8ddb4959993818969'
SCOPE = "playlist-modify-public"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SCOPE))

def get_recommendations_with_reason(artist, track_name, limit=20): 
    # Limit arttırıldı çünkü aynı sanatçıları eleyeceğimiz için daha çok adaya ihtiyacımız var
    url = "http://ws.audioscrobbler.com/2.0/"
    
    # 1. YÖNTEM: Şarkı Benzerliği
    params_track = {
        'method': 'track.getsimilar',
        'artist': artist,
        'track': track_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit,
        'autocorrect': 1
    }
    
    try:
        response = requests.get(url, params=params_track)
        data = response.json()
        
        recommendations = []
        if 'similartracks' in data and data['similartracks']['track']:
            for item in data['similartracks']['track']:
                rec_song = item['name']
                rec_artist = item['artist']['name']
                recommendations.append(f"{rec_artist} - {rec_song}")
            return recommendations, "Şarkı Benzerliği"

        # 2. YÖNTEM: Sanatçı Benzerliği
        params_artist = {
            'method': 'artist.getsimilar',
            'artist': artist,
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': limit,
            'autocorrect': 1
        }
        
        resp_artist = requests.get(url, params=params_artist)
        data_artist = resp_artist.json()
        
        if 'similarartists' in data_artist and data_artist['similarartists']['artist']:
            for item in data_artist['similarartists']['artist']:
                rec_artist_name = item['name']
                recommendations.append(rec_artist_name) 
            return recommendations, "Sanatçı Vibe'ı"
            
    except Exception as e:
        pass
        
    return [], "Veri Yok"

def find_spotify_details(search_query):
    """
    Şarkıyı arar ve (URI, Şarkı Adı, Sanatçı Adı, Sanatçı ID) döndürür.
    Bu sayede sanatçı kontrolü yapabiliriz.
    """
    try:
        results = sp.search(q=search_query, limit=1, type='track')
        items = results['tracks']['items']
        if items:
            track = items[0]
            track_uri = track['uri']
            track_name = track['name']
            
            # Sanatçı bilgilerini al
            main_artist = track['artists'][0]
            artist_name = main_artist['name']
            artist_id = main_artist['id']
            
            return track_uri, f"{artist_name} - {track_name}", artist_name, artist_id
    except:
        pass
    return None, None, None, None

def create_report_file(log_lines, playlist_name):
    filename = "vibe_raporu.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"RAPOR: {playlist_name}\n")
        f.write(f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("-" * 50 + "\n")
        for line in log_lines:
            f.write(line + "\n")
    print(f"\n📄 Rapor '{filename}' dosyasına kaydedildi.")

def main():
    print("\n--- 🎵 VibeMaster v4.0 (Çeşitlilik Modu: %100) 🎵 ---")
    print("Her sanatçıdan SADECE 1 şarkı alınacaktır.\n")
    
    seed_inputs = []
    for i in range(3):
        while True:
            entry = input(f">> {i+1}. Şarkı (Sanatçı - Şarkı): ")
            if "-" in entry:
                parts = entry.split("-", 1)
                seed_inputs.append((parts[0].strip(), parts[1].strip()))
                break
            else:
                print("Lütfen tire (-) kullanın.")

    all_recommendations = []
    log_buffer = [] 
    
    print("\n[1/3] Geniş kapsamlı aday havuzu oluşturuluyor...")
    
    for artist, song in seed_inputs:
        # Limit=30 yaptık ki elimizde elenecek bol bol malzeme olsun
        recs, method = get_recommendations_with_reason(artist, song, limit=30)
        log_buffer.append(f"\nKAYNAK: {artist} - {song} ({method})")
        
        for r in recs:
            all_recommendations.append(r)

    print("\n[2/3] Spotify Taraması ve Çeşitlilik Filtresi...")
    final_uris = []
    
    # KULLANILAN SANATÇILARI BURADA TUTACAĞIZ
    used_artist_ids = set() 
    
    log_buffer.append("\n" + "-"*30)
    log_buffer.append("FİLTRELEME İŞLEMİ")
    log_buffer.append("-" * 30)
    
    # Rapor ekranı başlıkları
    print(f"{'DURUM':<10} | {'ŞARKI ADI':<40}")
    print("-" * 60)

    count = 0
    target = 20
    
    # Liste karışık gelirse daha iyi olur (Hep aynı kaynaktan gitmemek için)
    import random
    random.shuffle(all_recommendations)

    for query in all_recommendations:
        if count >= target: break
        
        uri, full_name, artist_name, artist_id = find_spotify_details(query)
        
        if uri:
            # --- ÇEŞİTLİLİK KONTROLÜ ---
            if artist_id in used_artist_ids:
                # Bu sanatçı zaten listede var!
                print(f"[-] ATLANDI | {artist_name} (Zaten listede var)")
                log_buffer.append(f"[FİLTRE] '{full_name}' atlandı çünkü {artist_name} zaten listede.")
            else:
                # Yeni bir sanatçı!
                final_uris.append(uri)
                used_artist_ids.add(artist_id) # Sanatçıyı kilitle
                
                print(f"[+] EKLENDİ | {full_name}")
                log_buffer.append(f"[ONAY] '{full_name}' listeye eklendi.")
                count += 1
                time.sleep(0.1)
        else:
            # Şarkı bulunamadı
            pass

    if not final_uris:
        print("Playlist oluşturulamadı.")
        return

    # 3. Playlist Oluşturma
    user_id = sp.current_user()['id']
    playlist_name = f"Vibe Mix (Unique Artists) {datetime.datetime.now().strftime('%d/%m')}"
    
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True, description="Her şarkı farklı bir sanatçıdan seçildi.")
    sp.playlist_add_items(playlist_id=playlist['id'], items=final_uris)
    
    print(f"\n✅ Playlist Hazır: {playlist_name}")
    print(f"Toplam {count} farklı sanatçıdan şarkı eklendi.")
    create_report_file(log_buffer, playlist_name)

if __name__ == "__main__":
    main()