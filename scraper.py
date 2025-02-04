import requests
from bs4 import BeautifulSoup
import json
import sys
import re
import argparse
import logging

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def scrape_comments(base_url, filename="comments.json"):
    """增量抓取网页评论并保存到 JSON 文件."""

    # 从 base_url 中提取楼盘 ID
    match = re.search(r'/thread/(\d+)/', base_url)
    if match:
        thread_id = match.group(1)
        filename = f"comments_{thread_id}.json" # 使用楼盘 ID 创建文件名
    else:
        filename = "comments.json" # 默认文件名,如果无法提取 ID

    # 尝试加载已有的评论
    try:
        with open(filename, "r", encoding="utf-8") as f:
            extracted_comments = json.load(f)
            logging.info(f"从 {filename} 文件加载了 {len(extracted_comments)} 条评论")
    except FileNotFoundError:
        logging.info(f"文件 {filename} 未找到,将创建新文件")
        extracted_comments = []

    comment_ids = set(comment['id'] for comment in extracted_comments)
    new_comments_found = False  # 标志是否有新评论

    for i in range(1, 10001, 200):
        start = i
        end = i + 199

        # 检查这一页最后一条评论是否已存在
        if str(end) in comment_ids:
            logging.debug(f"页面 {start}-{end} 的最后一条评论已存在,跳过")
            continue  # 跳过此页的抓取

        page_url = f"{base_url}res/{start}-{end}/"
        logging.info(f"正在抓取页面: {page_url}")
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            comments = soup.find_all('li', class_=['normal', 'sage', 'admin']) # 修改选择器,同时匹配 'normal', 'sage' 和 'admin'
            if not comments:
                logging.info(f"页面 {page_url} 没有评论,停止抓取")
                break

            for comment_div in comments:
                comment_id = comment_div.get('value')
                if comment_id in comment_ids:
                    continue  # 跳过已存在的评论

                comment_ids.add(comment_id)
                comment_text = comment_div.find('div', class_='res-item-detail').find('p', itemprop='commentText').text.strip()
                extracted_comments.append({'id': comment_id, 'text': comment_text})
                new_comments_found = True  # 标记为找到新评论

        except requests.exceptions.HTTPError as e:
            logging.error(f"抓取页面 {page_url} 失败: {e}")
            continue
        except Exception as e:
            logging.error(f"抓取页面 {page_url} 发生错误: {e}")
            continue


    extracted_comments.sort(key=lambda x: int(x['id'])) # 根据 id 从小到大排序
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(extracted_comments, f, ensure_ascii=False, indent=4)
    logging.info(f"所有评论已保存到 {filename} 文件中 (JSON 格式, id 已排序)")
    logging.info(f"总共抓取到 {len(extracted_comments)} 条评论")
    return extracted_comments, new_comments_found

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="增量抓取网页评论并保存到 JSON 文件.")
    parser.add_argument("action", choices=["scrape"], help="指定操作为 'scrape'")
    parser.add_argument("base_url", type=str, help="指定基础 URL")
    parser.add_argument("--filename", type=str, default="comments.json", help="指定输出文件名 (默认: comments.json)")

    args = parser.parse_args()

    if args.action == "scrape" and args.base_url:
        scrape_comments(args.base_url, args.filename)
    else:
        logging.error("请指定操作和基础 URL: python scraper.py scrape <base_url> --filename <filename>")
