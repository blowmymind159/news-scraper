import feedparser
import os
import time
from datetime import datetime
import google.generativeai as genai
from supabase import create_client

print("=== INICIANDO SCRAPER ===")

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3.8-flash')

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

feeds = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.theguardian.com/world/rss',
    'https://techcrunch.com/feed/',
    'https://hnrss.org/frontpage'
]

print(f"\n=== PROCESSANDO {len(feeds)} FEEDS ===\n")

total_inseridos = 0
gemini_requests = 0

for feed_url in feeds:
    print(f"Processando: {feed_url}")
    feed = feedparser.parse(feed_url)
    
    for entry in feed.entries[:5]:
        title = entry.title
        source = feed.feed.get('title', 'Unknown')
        url = entry.link
        
        print(f"  Título: {title}")
        print(f"  Fonte: {source}")
        
        # Usar Gemini para score
        if gemini_requests < 20:
            try:
                prompt = f'Avalie de 1.0 a 10.0 a significância global desta notícia. Retorne APENAS o número. Título: {title}'
                response = model.generate_content(prompt)
                score = float(response.text.strip().replace('`', '').replace('json', ''))
                gemini_requests += 1
                print(f"    Score Gemini: {score}")
            except Exception as e:
                print(f"    Erro Gemini: {e}")
                score = 3.0
        else:
            score = 3.0
            print(f"    Quota Gemini esgotada, usando score padrão")
        
        # Inserir no Supabase (sem publicado_em)
        if score >= 2.0:
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score
                }, on_conflict='url').execute()
                total_inseridos += 1
                print(f"    ✓ Inserido")
            except Exception as e:
                print(f"    ✗ Erro ao inserir: {e}")
        
        time.sleep(2)

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
print(f"=== REQUESTS GEMINI: {gemini_requests}/20 ===")
