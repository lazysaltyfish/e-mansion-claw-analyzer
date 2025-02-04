import json
from bs4 import BeautifulSoup

def extract_comments(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    comments = []
    for li in soup.find_all('li', attrs={'itemscope': True, 'itemtype': "http://schema.org/UserComments"}):
        comment_id = li.get('value')
        comment_text_elem = li.find('p', attrs={'itemprop': 'commentText'})
        if comment_text_elem:
            comment_text = comment_text_elem.get_text(strip=True)
            comments.append({'id': comment_id, 'text': comment_text})
    return comments

if __name__ == "__main__":
    with open('test_html.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    comments = extract_comments(html_content)
    print(json.dumps(comments, ensure_ascii=False, indent=4))