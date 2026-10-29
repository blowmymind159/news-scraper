import feedparser
import os
import google.generativeai as genai
from supabase import create_client

print("=== INICIANDO SCRAPER ===")

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key: {supabase_key[:20]}...")

supabase = create_client(supabase_url, supabase_key)

feeds = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.theguardian.com/world/rss',
    'https://www.aljazeera.com/xml/rss/all.xml',
    'https://techcrunch.com/feed/',
    'https://feeds.npr.org/1001/rss.xml',
    'https://www.nature.com/nature.rss',
    'https://hnrss.org/frontpage',
    'https://feeds.arstechnica.com/arstechnica/index'
]

print(f"\n=== PROCESSANDO {len(feeds)} FEEDS ===\n")

total_inseridos = 0

for feed_url in feeds:
    print(f"Processando: {feed_url}")
    feed = feedparser.parse(feed_url)
    print(f"  Encontradas {len(feed.entries)} entradas")
    
    for entry in feed.entries[:5]:
        print(f"  Título: {entry.title}")
        
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
                    'score': score,
                    'publicado_em': entry.get('published', '')
                }, on_conflict='url').execute()
                
                print(f"    Resultado: {result}")
                total_inseridos += 1
            else:
                print(f"    Score muito baixo, ignorando")
                
        except Exception as e:
            print(f"    ERRO: {e}")
            import traceback
            traceback.print_exc()

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
