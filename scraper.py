import feedparser
import os
import time
import google.generativeai as genai
from supabase import create_client

print("=== INICIANDO SCRAPER ===")

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3.8-flash')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f"Supabase URL: {supabase_url}")

supabase = create_client(supabase_url, supabase_key)

# APENAS 2 FEEDS para ficar dentro do limite de 20 requests/dia
feeds = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://techcrunch.com/feed/'
]

print(f"\n=== PROCESSANDO {len(feeds)} FEEDS (max 5 entradas cada) ===\n")

total_inseridos = 0
total_processados = 0

for feed_url in feeds:
    print(f"Processando: {feed_url}")
    feed = feedparser.parse(feed_url)
    print(f"  Encontradas {len(feed.entries)} entradas")
    
    for entry in feed.entries[:5]:
        total_processados += 1
        print(f"  [{total_processados}] Título: {entry.title}")
        
        prompt = f'Avalie de 1.0 a 10.0 a significância global desta notícia. Retorne APENAS o número. Eventos triviais = <3.0. Geopolítica, ciência, macroeconomia = >5.0. Título: {entry.title}'
        
        try:
            response = model.generate_content(prompt)
            score_text = response.text.strip().replace('`', '').replace('json', '')
            print(f"    Resposta Gemini: {score_text}")
            
            score = float(score_text)
            print(f"    Score: {score}")
            
            if score >= 2.0:
                print(f"    Inserindo no Supabase...")
                result = supabase.table('noticias').upsert({
                    'titulo': entry.title,
                    'fonte': feed.feed.get('title', 'Unknown'),
                    'url': entry.link,
                    'score': score
                }, on_conflict='url').execute()
                
                print(f"    Resultado: OK")
                total_inseridos += 1
            else:
                print(f"    Score muito baixo, ignorando")
                
        except Exception as e:
            print(f"    ERRO: {e}")
        
        # Pausa de 3 segundos entre requests para evitar rate limit
        time.sleep(3)

print(f"\n=== TOTAL PROCESSADOS: {total_processados} ===")
print(f"=== TOTAL INSERIDOS: {total_inseridos} ===")
