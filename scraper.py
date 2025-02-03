import requests
from bs4 import BeautifulSoup
import json
import sys
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def scrape_comments(base_url, filename="comments.json"):
    """增量抓取网页评论并保存到 JSON 文件."""

    # 从 base_url 中提取楼盘 ID
    match = re.search(r'/thread/(\d+)/', base_url)
    if match:
        thread_id = match.group(1)
        filename = f"comments_{thread_id}.json" # 使用楼盘 ID 创建文件名
    else:
        filename = "comments.json" # 默认文件名，如果无法提取 ID

    # 尝试加载已有的评论
    try:
        with open(filename, "r", encoding="utf-8") as f:
            extracted_comments = json.load(f)
            print(f"从 {filename} 文件加载了 {len(extracted_comments)} 条评论")
    except FileNotFoundError:
        print(f"文件 {filename} 未找到，将创建新文件")
        extracted_comments = []

    comment_ids = set(comment['id'] for comment in extracted_comments)

    for i in range(1, 10001, 200):
        start = i
        end = i + 199

        # 检查这一页最后一条评论是否已存在
        if str(end) in comment_ids:
            print(f"页面 {start}-{end} 的最后一条评论已存在，跳过")
            continue  # 跳过此页的抓取

        page_url = f"{base_url}res/{start}-{end}/"
        print(f"正在抓取页面: {page_url}")
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            comments = soup.find_all('li', class_=['normal', 'sage', 'admin']) # 修改选择器，同时匹配 'normal', 'sage' 和 'admin'
            if not comments:
                print(f"页面 {page_url} 没有评论，停止抓取")
                break

            for comment_div in comments:
                comment_id = comment_div.get('value')
                if comment_id in comment_ids:
                    continue  # 跳过已存在的评论

                comment_ids.add(comment_id)
                comment_text = comment_div.find('div', class_='res-item-detail').find('p', itemprop='commentText').text.strip()
                extracted_comments.append({'id': comment_id, 'text': comment_text})

        except requests.exceptions.HTTPError as e:
            print(f"抓取页面 {page_url} 失败: {e}")
            continue
        except Exception as e:
            print(f"抓取页面 {page_url} 发生错误: {e}")
            continue


    with open(filename, "w", encoding="utf-8") as f:
        json.dump(extracted_comments, f, ensure_ascii=False, indent=4)
    print(f"所有评论已保存到 {filename} 文件中 (JSON 格式)")
    print(f"总共抓取到 {len(extracted_comments)} 条评论")
    return extracted_comments

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    base_url = sys.argv[2] if len(sys.argv) > 2 else None # 从命令行参数获取 base_url

    if action == "scrape" and base_url: # 确保 scrape 操作需要 base_url
        filename = sys.argv[3] if len(sys.argv) > 3 else "comments.json" # 获取文件名参数，默认为 comments.json
        scrape_comments(base_url, filename) # 传递 base_url 和 filename
    else:
        print("请指定操作: python scraper.py scrape <base_url> <filename>") # 更新帮助信息
