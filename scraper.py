import feedparser
import re
import os
from supabase import create_client

print("=== INICIANDO SCRAPER (MODO NEWS MINIMALIST RSS) ===")

# Conectar ao Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# O feed RSS oficial do News Minimalist (que já tem as notícias curadas e com score!)
RSS_URL = 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml'

print(f"Lendo feed: {RSS_URL}")
feed = feedparser.parse(RSS_URL)

total_inseridos = 0

# Regex para extrair do HTML: [Score] Título — <a href="URL"><b>Fonte</b></a>
# Exemplo no HTML: <b>[6.3] Juries hold Meta... — </b><a ... href="https://..."><b>apnews.com</b></a>
pattern = re.compile(r'\[(\d+\.\d+)\]\s+(.*?)\s+—\s+.*?href="(https?://[^"]+)".*?<b>([^<]+)</b>', re.IGNORECASE | re.DOTALL)

for entry in feed.entries:
    # O conteúdo HTML está geralmente em 'content' ou 'summary'
    content = entry.get('content', [{}])[0].get('value', '')
    if not content:
        content = entry.get('summary', '')
        
    # Encontrar todas as correspondências no conteúdo HTML
    matches = pattern.findall(content)
    
    for match in matches:
        score_str, title, url, source = match
        
        # Limpar o título e a fonte de espaços extras ou quebras de linha
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
            
        # Só inserir se o score for relevante (ex: >= 5.0)
        if score >= 5.0:
            print(f"Encontrada: [{score}] {title} ({source})")
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'publicado_em': entry.get('published', '')
                }, on_conflict='url').execute()
                total_inseridos += 1
            except Exception as e:
                print(f"Erro ao inserir: {e}")

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
