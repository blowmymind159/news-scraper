import feedparser
import os
import google.generativeai as genai
from supabase import create_client

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

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

for feed_url in feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:
        prompt = f'Avalie de 1.0 a 10.0 a significância global desta notícia. Retorne APENAS o número. Eventos triviais = <3.0. Geopolítica, ciência, macroeconomia = >5.0. Título: {entry.title}'
        try:
            response = model.generate_content(prompt)
            score = float(response.text.strip().replace('`', '').replace('json', ''))
            if score >= 2.0:
                supabase.table('noticias').upsert({
                    'titulo': entry.title,
                    'fonte': feed.feed.get('title', 'Unknown'),
                    'url': entry.link,
                    'score': score,
                    'publicado_em': entry.get('published', '')
                }, on_conflict='url').execute()
        except Exception:
            pass
