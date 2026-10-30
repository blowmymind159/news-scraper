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

# Padrão para extrair notícias do HTML do RSS
# Formato: <b>[SCORE] Título — </b><a href="URL"><b>fonte</b></a>
pattern_main = re.compile(
    r'<b>\[(\d+\.\d+)\]\s+(.*?)\s+—\s+</b><a\s+href="([^"]+)"[^>]*><b>([^<]+)</b></a>',
    re.IGNORECASE | re.DOTALL
)

# Formato secundário (Highly covered news): [SCORE] Título — <a href="URL">fonte</a>
pattern_secondary = re.compile(
    r'\[(\d+\.\d+)\]\s+(.*?)\s+—\s+<a\s+href="([^"]+)"[^>]*>([^<]+)</a>',
    re.IGNORECASE | re.DOTALL
)

for entry in feed.entries:
    content = entry.get('content', [{}])[0].get('value', '')
    if not content:
        content = entry.get('summary', '')
    
    pub_date = entry.get('published', '')
    
    print(f"Edição: {entry.title}")
    
    # Extrair com padrão principal
    matches_main = pattern_main.findall(content)
    for match in matches_main:
        score_str, title, url, source = match
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        if score >= 5.5:
            print(f"  ✓ [{score}] {title[:60]}... ({source})")
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'publicado_em': pub_date
                }, on_conflict='url').execute()
                total_inseridos += 1
            except Exception as e:
                print(f"    ✗ Erro: {e}")
    
    # Extrair com padrão secundário
    matches_secondary = pattern_secondary.findall(content)
    for match in matches_secondary:
        score_str, title, url, source = match
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        if score >= 5.5:
            print(f"  ✓ [{score}] {title[:60]}... ({source})")
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'publicado_em': pub_date
                }, on_conflict='url').execute()
                total_inseridos += 1
            except Exception as e:
                print(f"    ✗ Erro: {e}")
    
    print()

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
print(f"=== FIM ===")
