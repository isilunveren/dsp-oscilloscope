app/                       
├── main.py                 Uygulama giriş noktası
│
├── device/                 Donanımla haberleşme
│   ├── protocol.py           Binary paket formatı, CRC16
│   └── reader.py              Seri port okuma, resync, paket parse
│
├── core/                    Sinyal işleme mantığı
│   ├── channel_manager.py     Kanal/port yönetimi, SerialReader orkestrasyon
│   ├── signal_buffer.py       Sliding window örnek buffer'ı
│   ├── signal_filter.py       IIR filtre (Butterworth/Chebyshev/Elliptic)
│   ├── signal_denoiser.py     AI tabanlı gürültü giderme (DeepFilterNet3)
│   ├── trigger_detector.py    Osiloskop trigger mekanizması
│   ├── peak_detector.py       Wavelet tabanlı pik tespiti
│   └── event_detector.py      Piklerin olaylara gruplanması
│
├── wav_recorder.py          WAV dosyasına kayıt
│
├── llm/                     Doğal dil ile cihaz kontrolü
│   ├── tools.py                Tool tanımları, sistem promptu
│   ├── worker.py                LLM API çağrısı (QThread)
│   └── handlers.py              Tool çağrılarını UI state'ine uygulama
│
└── ui/                       Arayüz
    ├── main_window.py          Ana pencere: state + olay yöneticileri
    ├── panels.py                Kontrol panelleri (CHANNEL, FILTER, EVENTS...)
    ├── plots.py                  Waveform/FFT/Waterfall grafik kurulumu
    ├── interaction.py            Fare etkileşimi (measure/pan/zoom)
    ├── sections.py                Ortak panel kutusu bileşeni
    └── styles.py                  QSS stil tanımları
    

Katman Mantığı

    device/ yalnızca ham byte akışını paket nesnesine çevirir, sinyal işleme bilmez.
    core/ tüm DSP mantığını (filtre, trigger, FFT, peak/event) barındırır; UI'dan bağımsızdır.
    ui/ yalnızca görüntüleme ve kullanıcı etkileşimini yönetir, DSP hesaplaması yapmaz,  core/ sınıflarını çağırır.
    llm/ UI state'ini değiştiren ayrı bir kontrol katmanıdır; main_window.py'nin widget'larına LLMSettingsController üzerinden erişir.

Çalıştırma

    pip install -r requirements.txt
    python app/main.py