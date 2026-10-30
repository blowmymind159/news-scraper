import feedparser
import re
import os
from datetime import datetime
from supabase import create_client

print("=== INICIANDO SCRAPER ===")

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# RSS feed principal do News Minimalist (já tem scores)
RSS_URL = 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml'

print(f"Lendo feed principal: {RSS_URL}")
feed = feedparser.parse(RSS_URL)
print(f"Encontradas {len(feed.entries)} edições\n")

total_inseridos = 0

# Padrão para extrair notícias
pattern = re.compile(
    r'<b>\[(\d+\.\d+)\]\s+(.*?)\s+—\s+</b><a\s+href="([^"]+)"[^>]*><b>([^<]+)</b></a>',
    re.IGNORECASE | re.DOTALL
)

pattern_secondary = re.compile(
    r'\[(\d+\.\d+)\]\s+(.*?)\s+—\s+<a\s+href="([^"]+)"[^>]*>([^<]+)</a>',
    re.IGNORECASE | re.DOTALL
)

# Função para categorizar notícias por palavras-chave
def categorize_news(title, source):
    title_lower = title.lower()
    source_lower = source.lower()
    
    categories = []
    
    if any(word in title_lower for word in ['politic', 'election', 'government', 'president', 'congress', 'senate', 'law', 'legislation']):
        categories.append('Politics')
    
    if any(word in title_lower for word in ['tech', 'ai', 'artificial', 'computer', 'software', 'app', 'digital', 'internet', 'cyber']):
        categories.append('Technology')
    
    if any(word in title_lower for word in ['science', 'research', 'study', 'scientist', 'discovery', 'space', 'nasa', 'astronomy']):
        categories.append('Science')
    
    if any(word in title_lower for word in ['climate', 'environment', 'green', 'renewable', 'solar', 'wind', 'pollution', 'carbon']):
        categories.append('Environment')
    
    if any(word in title_lower for word in ['health', 'medical', 'disease', 'vaccine', 'hospital', 'doctor', 'cancer', 'drug']):
        categories.append('Health')
    
    if any(word in title_lower for word in ['business', 'economy', 'market', 'stock', 'trade', 'company', 'bank', 'financial']):
        categories.append('Business')
    
    if any(word in title_lower for word in ['war', 'military', 'army', 'conflict', 'attack', 'bomb', 'nato', 'defense']):
        categories.append('Society')
    
    if any(word in title_lower for word in ['culture', 'art', 'music', 'film', 'movie', 'book', 'literature']):
        categories.append('Culture')
    
    if any(word in title_lower for word in ['sport', 'football', 'soccer', 'basketball', 'olympic', 'game']):
        categories.append('Sports')
    
    if not categories:
        categories.append('Society')
    
    return categories

for entry in feed.entries:
    content = entry.get('content', [{}])[0].get('value', '')
    if not content:
        content = entry.get('summary', '')
    
    pub_date = entry.get('published', '')
    
    print(f"Edição: {entry.title}")
    
    # Extrair com padrão principal
    matches_main = pattern.findall(content)
    for match in matches_main:
        score_str, title, url, source = match
        title = title.strip()
        source = source.strip()
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        if score >= 5.0:
            categories = categorize_news(title, source)
            category_str = ','.join(categories)
            
            print(f"  ✓ [{score}] {title[:60]}... ({source}) - {category_str}")
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'categoria': category_str,
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
        
        if score >= 5.0:
            categories = categorize_news(title, source)
            category_str = ','.join(categories)
            
            print(f"  ✓ [{score}] {title[:60]}... ({source}) - {category_str}")
            try:
                supabase.table('noticias').upsert({
                    'titulo': title,
                    'fonte': source,
                    'url': url,
                    'score': score,
                    'categoria': category_str,
                    'publicado_em': pub_date
                }, on_conflict='url').execute()
                total_inseridos += 1
            except Exception as e:
                print(f"    ✗ Erro: {e}")
    
    print()

print(f"\n=== TOTAL INSERIDOS: {total_inseridos} ===")
print(f"=== FIM ===")
