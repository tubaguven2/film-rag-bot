#  FilmRAGBot – Akıllı Film Öneri Chatbotu

##  Proje Amacı
Bu proje, kullanıcının doğal dilde yazdığı film isteklerine göre **The Movie Database (TMDB)** API’sinden veri çekerek **kişiselleştirilmiş film önerileri** sunan bir yapay zeka destekli chatbot geliştirmeyi amaçlamaktadır.  
Sistem, **RAG (Retrieval-Augmented Generation)** yaklaşımına dayalı olarak film türü, puan, özet ve dil bilgilerini birleştirir.

---

##  Veri Seti Hakkında Bilgi
Proje, harici bir veri seti kullanmak yerine **TMDB API** aracılığıyla gerçek zamanlı olarak film verilerini çekmektedir.  
API sayesinde aşağıdaki bilgiler dinamik olarak elde edilir:
- Film Adı  
- Yayın Yılı  
- Tür  
- IMDb Puanı  
- Film Özeti (Türkçe dil desteğiyle)  
- Poster Görseli  

Kullanıcıdan gelen sorgular (örneğin *"korku filmi öner 7 üstü"*, *"romantik komedi öner"*) TMDB veritabanındaki uygun filmlerle eşleştirilir.

---

##  Kullanılan Yöntemler ve Teknolojiler
- **Python** – Ana geliştirme dili  
- **Gradio** – Web arayüzü ve chatbot etkileşimi  
- **TMDB API** – Film verilerinin alınması  
- **Regex & Akıllı Filtreleme** – Tür, puan, kelime eşleştirme  
- **Hugging Face Spaces** – Model deploy ortamı  

---

##  Çözüm Mimarisi
1. Kullanıcıdan doğal dilde film isteği alınır.  
2. Sistem, istek içeriğini analiz ederek tür ve minimum IMDb puanını algılar.  
3. TMDB API’ye sorgu gönderilir (`language=tr-TR` parametresiyle Türkçe içerik desteği).  
4. Dönen JSON verisi filtrelenir ve Gradio arayüzünde kullanıcıya özet, afiş ve puan bilgisiyle gösterilir.  
5. “Farklı film öner” gibi ifadelerde sistem, önceki önerilerden farklı yeni filmleri getirir.  

---

##  Web Arayüzü
Proje **Gradio** ile oluşturulmuş ve **Hugging Face Spaces** üzerinde yayımlanmıştır.  
Canlı demo bağlantısı:  
 [https://huggingface.co/spaces/tubaguven/film-rag-bot](https://huggingface.co/spaces/tubaguven/film-rag-bot)

Arayüz, kullanıcıların “Filmini sor” kutucuğuna Türkçe ifadelerle film isteği girmesine olanak tanır.  
Bot yanıtlarında film posteri, puan ve kısa özet görüntülenir.

---

##  Çalıştırma Kılavuzu
1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install gradio requests

2.TMDB API anahtarınızı ekleyin:
 export TMDB_API_KEY="YOUR_API_KEY"

3.Uygulamayı başlatın:
 python app.py

 4.Tarayıcıdan http://localhost:7860 adresine giderek botu test edin.

 ---

 requirements.txt
 
 gradio
 
 requests

---

SONUÇ
Bu proje, Türkçe film öneri sistemlerinde RAG tabanlı doğal dil anlayışının pratik bir örneğini sunmaktadır. Gerçek zamanlı veri çekme, akıllı filtreleme ve kullanıcı dostu arayüzüyle, eğlenceli bir etkileşim sunmayı hedeflemektedir.
