import feedparser
from bs4 import BeautifulSoup



def parse_description_and_image(description: str) -> tuple[str]:
    '''Parse the description and image URL from the given HTML'''
    soup = BeautifulSoup(description, 'html.parser')

    # Extract the image URL
    image = soup.find('img')['src']

    # Extract the description
    description = soup.find_all('p')[1].text

    return image, description


def fetch_cointelegraph_news() -> list[dict]:
    '''Fetch the latest 4 articles from Cointelegraph RSS feed'''

    rss_url = "https://cointelegraph.com/rss"
    
    feed = feedparser.parse(rss_url)
    
    # Extract articles
    articles = []
    for entry in feed.entries[:4]:
        image, description = parse_description_and_image(entry.summary)
        author = entry.get('author', None)
        author = author.replace('Cointelegraph by ', '') if author else None

        articles.append({
            'title': entry.title,
            'description': description,
            'creator_name': author,
            'image_url': image,
            'link': entry.link
        })
    
    return articles

