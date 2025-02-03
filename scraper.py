import requests
from bs4 import BeautifulSoup
import json
import sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def load_comments_from_json(path="comments.json"):
    """从 JSON 文件加载评论."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            comments = json.load(f)
        print(f"从 {path} 文件加载了 {len(comments)} 条评论")
        return comments
    except FileNotFoundError:
        print(f"文件 {path} 未找到，请先运行爬虫抓取评论并保存到文件。")
        return None

import re

def scrape_comments(base_url):
    """抓取网页评论并保存到 JSON 文件."""
    extracted_comments = []
    comment_ids = set()

    # 从 base_url 中提取楼盘 ID
    match = re.search(r'/thread/(\d+)/', base_url)
    if match:
        thread_id = match.group(1)
        filename = f"comments_{thread_id}.json" # 使用楼盘 ID 创建文件名
    else:
        filename = "comments.json" # 默认文件名，如果无法提取 ID

    for i in range(1, 10001, 200):
        start = i
        end = i + 199
        page_url = f"{base_url}res/{start}-{end}/"
        print(f"正在抓取页面: {page_url}")
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            comments = soup.find_all('li', class_='normal')
            if not comments:
                print(f"页面 {page_url} 没有评论，停止抓取")
                break
            for comment_div in comments:
                comment_id = comment_div.get('value')
                if comment_id in comment_ids:
                    continue
                comment_ids.add(comment_id)
                comment_text = comment_div.find('div', class_='res-item-detail').find('p', itemprop='commentText').text.strip()
                extracted_comments.append({'id': comment_id, 'text': comment_text})
        except requests.exceptions.HTTPError as e:
            print(f"抓取页面 {page_url} 失败: {e}")
            continue
        except Exception as e:
            print(f"抓取页面 {page_url} 发生错误: {e}")
            continue

    with open(filename, "w", encoding="utf-8") as f: # 使用动态文件名
        json.dump(extracted_comments, f, ensure_ascii=False, indent=4)
    print(f"所有评论已保存到 {filename} 文件中 (JSON 格式)") # 更新打印信息
    print(f"总共抓取到 {len(extracted_comments)} 条评论")
    return extracted_comments

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    base_url = sys.argv[2] if len(sys.argv) > 2 else None # 从命令行参数获取 base_url

    if action == "scrape" and base_url: # 确保 scrape 操作需要 base_url
        scrape_comments(base_url) # 传递 base_url
    elif action == "load":
        comments = load_comments_from_json()
        if comments:
            print("加载到的评论:")
            print(json.dumps(comments, ensure_ascii=False, indent=4))
    else:
        print("请指定操作: python scraper.py scrape <base_url> 或 python scraper.py load") # 更新帮助信息
