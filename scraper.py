import feedparser
import re
import os
from supabase import create_client

print("=== INICIANDO SCRAPER (RSS NEWS MINIMALIST) ===")

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

RSS_URL = 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml'

print(f"Lendo feed: {RSS_URL}")
feed = feedparser.parse(RSS_URL)
print(f"Encontradas {len(feed.entries)} edições\n")

total_inseridos = 0

# Padrão para extrair notícias do HTML
pattern = re.compile(
    r'\[(\d+\.\d+)\]\s+(.*?)\s+—\s+<a\s+href="([^"]+)"[^>]*><b>([^<]+)</b></a>',
    re.IGNORECASE | re.DOTALL
)

for entry in feed.entries:
    content = entry.get('content', [{}])[0].get('value', '')
    if not content:
        content = entry.get('summary', '')
    
    matches = pattern.findall(content)
    
    for match in matches:
        score_str, title, url, source = match
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        # Inserir todas as notícias com score >= 5.0
        if score >= 5.0:
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'publicado_em': entry.get('published', '')
                }, on_conflict='url').execute()
                total_inseridos += 1
                print(f"✓ [{score}] {title[:60]}...")
            except Exception as e:
                print(f"✗ Erro ao inserir: {e}")

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
