import feedparser
import os
import time
from datetime import datetime
from collections import Counter

# Só importa a Gemini se necessário
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

from supabase import create_client

print("=== INICIANDO SCRAPER ===")

# Configurar Gemini apenas se tiver chave
if HAS_GEMINI:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    print("Gemini não configurado, usando apenas heurística")

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

feeds = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.theguardian.com/world/rss',
    'https://www.aljazeera.com/xml/rss/all.xml',
    'https://techcrunch.com/feed/',
    'https://www.nature.com/nature.rss',
    'https://hnrss.org/frontpage'
]

# Palavras-chave de ALTA significância (score automático 5.0+)
HIGH_SIGNIFICANCE_KEYWORDS = [
    'war', 'election', 'climate change', 'breakthrough', 'discovery',
    'economic crisis', 'pandemic', 'earthquake', 'terror', 'sanctions',
    'treaty', 'summit', 'UN', 'NATO', 'nuclear', 'AI', 'artificial intelligence'
]

# Fontes de alta credibilidade
HIGH_CREDIBILITY_SOURCES = ['BBC', 'Reuters', 'Guardian', 'Nature', 'Al Jazeera']

print(f"\n=== PROCESSANDO {len(feeds)} FEEDS ===\n")

total_inseridos = 0
gemini_requests = 0

for feed_url in feeds:
    print(f"Processando: {feed_url}")
    feed = feedparser.parse(feed_url)
    
    for entry in feed.entries[:10]:  # 10 notícias por feed
        # === FILTRAGEM POR HEURÍSTICA ===
        title_lower = entry.title.lower()
        source_name = feed.feed.get('title', 'Unknown')
        
        # Score base
        score = 3.0
        
        # +1.0 se tiver palavras-chave de alta significância
        if any(keyword in title_lower for keyword in HIGH_SIGNIFICANCE_KEYWORDS):
            score += 1.5
        
        # +0.5 se for fonte de alta credibilidade
        if any(hc in source_name for hc in HIGH_CREDIBILITY_SOURCES):
            score += 0.5
        
        # +0.5 se o título for longo (mais detalhado)
        if len(entry.title) > 80:
            score += 0.3
        
        # === DECISÃO: Usa Gemini ou não? ===
        use_gemini = False
        
        # Se score heurístico >= 4.0, usa Gemini para confirmar
        if score >= 4.0 and HAS_GEMINI and gemini_requests < 15:
            use_gemini = True
            gemini_requests += 1
        
        # Se já usámos 15 requests Gemini, só usa heurística
        if use_gemini:
            print(f"  [{gemini_requests}/20] {entry.title}")
            print(f"    Score heurístico: {score}")
            
            try:
                prompt = f'Avalie de 1.0 a 10.0 a significância GLOBAL desta notícia. Retorne APENAS o número. Título: {entry.title}'
                response = model.generate_content(prompt)
                gemini_score = float(response.text.strip().replace('`', '').replace('json', ''))
                print(f"    Score Gemini: {gemini_score}")
                final_score = gemini_score
            except Exception as e:
                print(f"    ERRO Gemini: {e}")
                final_score = score  # Fallback para heurística
        else:
            print(f"  [Heurística] {entry.title}")
            print(f"    Score: {score}")
            final_score = score
        
        # Inserir se score >= 2.5
        if final_score >= 2.5:
            try:
                supabase.table('noticias').upsert({
                    'titulo': entry.title,
                    'fonte': source_name,
                    'url': entry.link,
                    'score': final_score,
                    'created_at': datetime.utcnow().isoformat()
                }, on_conflict='url').execute()
                total_inseridos += 1
                print(f"    ✓ Inserido")
            except Exception as e:
                print(f"    ✗ Erro ao inserir: {e}")
        
        # Pausa de 2 segundos
        time.sleep(2)

print(f"\n=== RESUMO ===")
print(f"Total inseridos: {total_inseridos}")
print(f"Requests Gemini usados: {gemini_requests}/20")
