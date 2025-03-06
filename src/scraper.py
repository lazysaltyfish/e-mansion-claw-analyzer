import os
import requests

import requests_cache
requests_cache.install_cache('property_claw_http', backend='sqlite', expire_after=3600)
from bs4 import BeautifulSoup
import json
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

def scrape_comments(base_url, filename="comments.json", test_mode=False, test_html="", output_dir="output/intermediate_results"):
    """增量抓取网页评论并保存到 JSON 文件."""

    # 从 base_url 中提取楼盘 ID
    match = re.search(r'/thread/(\d+)/', base_url)
    if match:
        thread_id = match.group(1)
        filename = os.path.join(output_dir, f"comments_{thread_id}.json") # 使用楼盘 ID 创建文件名
    else:
        filename = os.path.join(output_dir, "comments.json") # 默认文件名,如果无法提取 ID

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
            if test_mode:
                soup = BeautifulSoup(test_html, 'html.parser')
            else:
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
                comment_detail = comment_div.find('div', class_='res-item-detail')
                comment_text = comment_detail.find('p', itemprop='commentText').text.strip()

                # 提取发布时间
                time_script = comment_detail.find('script')
                if time_script:
                    match = re.search(r"timeToSimple\('(.*?)'\)", time_script.string)
                    if match:
                        timestamp = match.group(1)
                    else:
                        timestamp = ""  # 如果找不到时间，则设置为空字符串
                else:
                    timestamp = ""

                # 提取回复目标的ID
                reply_to = []
                for a_tag in comment_detail.find_all('a', href=True):
                    match = re.search(r'/bbs/thread/\d+/res/(\d+)', a_tag['href'])
                    if match:
                        reply_to.append(match.group(1))

                # 提取图片链接
                images = []
                for img_tag in comment_detail.find_all('img'):
                    images.append(img_tag.get('src'))

                extracted_comments.append({
                    'id': comment_id,
                    'text': comment_text,
                    'timestamp': timestamp,
                    'replies': reply_to,
                    'images': images
                })
                new_comments_found = True  # 标记为找到新评论

        except requests.exceptions.HTTPError as e:
            logging.error(f"抓取页面 {page_url} 失败: {e}")
            extracted_comments = [] # 清空评论列表
            new_comments_found = False
            continue
        except Exception as e:
            logging.error(f"抓取页面 {page_url} 发生错误: {e}")
            extracted_comments = [] # 清空评论列表
            new_comments_found = False
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
    parser.add_argument("--test_mode", action="store_true", help="使用测试模式") # 添加 test_mode 参数
    parser.add_argument("--test_html", type=str, default="", help="测试模式下使用的 HTML 文件路径") # 添加 test_html 参数

    args = parser.parse_args()

    if args.action == "scrape" and args.base_url:
        if args.test_mode:
            # 测试模式下，读取 test_html 文件的内容
            try:
                with open(args.test_html, 'r', encoding='utf-8') as f:
                    test_html_content = f.read()
                scrape_comments(args.base_url, args.filename, test_mode=True, test_html=test_html_content)
            except FileNotFoundError:
                logging.error(f"测试文件 {args.test_html} 未找到。")
        else:
            scrape_comments(args.base_url, args.filename)
    else:
        logging.error("请指定操作和基础 URL: python scraper.py scrape <base_url> --filename <filename>")
