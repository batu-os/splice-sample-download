# Splice Sample Downloader

Splice preview sample'larını doğrudan indirip descramble eden araç.

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
python fetch_sample.py <splice_sample_url>
```

Örnek:
```bash
python fetch_sample.py "https://splice.com/sounds/sample/b65d88bb0221a5f31652be6614baa830ebe377f68b1e63148c140be0036835ff"
```

Dosyalar `downloads/` klasörüne orijinal adlarıyla kaydedilir.

## Nasıl Çalışır

1. Splice sample sayfasını parse eder
2. S3'teki scrambled MP3 URL'sini çeker
3. MP3'ü indirir ve XOR-based descramble uygular
4. Temiz MP3 olarak kaydeder

## Not

Preview kalitesi: MP3 128kbps, 44.1kHz stereo.
