import feedparser
import re
import os
from supabase import create_client

print("=== INICIANDO SCRAPER (RSS NEWS MINIMALIST) ===")

# Conectar ao Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
print(f"Supabase URL: {supabase_url}")

supabase = create_client(supabase_url, supabase_key)

# RSS feed oficial do News Minimalist
RSS_URL = 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml'

print(f"\nLendo feed: {RSS_URL}")
feed = feedparser.parse(RSS_URL)
print(f"Encontradas {len(feed.entries)} edições\n")

total_inseridos = 0

# Padrão para extrair notícias do HTML
# Formato: <b>[SCORE] Título — </b><a href="URL"><b>fonte</b></a>
pattern = re.compile(
    r'<b>\[(\d+\.\d+)\]\s+(.*?)\s+—\s+</b><a\s+href="([^"]+)"[^>]*><b>([^<]+)</b></a>',
    re.IGNORECASE | re.DOTALL
)

# Padrão secundário para "Highly covered news"
# Formato: [SCORE] Título — <a href="URL">fonte</a>
pattern_secondary = re.compile(
    r'\[(\d+\.\d+)\]\s+(.*?)\s+—\s+<a\s+href="([^"]+)"[^>]*>([^<]+)</a>',
    re.IGNORECASE | re.DOTALL
)

for entry in feed.entries:
    # Obter o conteúdo HTML
    content = entry.get('content', [{}])[0].get('value', '')
    if not content:
        content = entry.get('summary', '')
    
    # Obter data de publicação
    pub_date = entry.get('published', '')
    
    print(f"Edição: {entry.title}")
    print(f"Publicada: {pub_date}")
    
    # Extrair notícias com o padrão principal
    matches_main = pattern.findall(content)
    for match in matches_main:
        score_str, title, url, source = match
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        # Só inserir notícias com score >= 5.5 (alta significância)
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
                print(f"    ✗ Erro ao inserir: {e}")
    
    # Extrair notícias com o padrão secundário
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
                print(f"    ✗ Erro ao inserir: {e}")
    
    print()  # Linha em branco entre edições

print(f"\n=== RESUMO ===")
print(f"Total inseridas: {total_inseridos}")
print(f"=== FIM ===")
