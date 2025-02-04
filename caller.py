import subprocess
import re
import sys
import logging
import argparse

from check_comments import check_missing_ids

# 设置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="处理URL并检查评论中的缺失ID。")
    parser.add_argument('--check-missing', action='store_true', help="检查给定文件中的缺失ID。")
    parser.add_argument('filename', nargs='?', default=None, help="检查缺失ID的文件名。")

    args = parser.parse_args()
    url_list = []
    try:
        with open("urls.txt", "r") as f:
            for line in f:
                url = line.strip()
                if url:  # 确保URL不为空
                    url_list.append(url)
    except FileNotFoundError:
        logging.error("urls.txt 文件未找到，请确保文件存在并包含URL列表。")
        sys.exit(1)

    if args.check_missing:
        if args.filename is None:
            logging.error("需要指定文件名以检查缺失ID。")
            sys.exit(1)
        check_missing_ids(args.filename)
    else:
        for url in url_list:
            logging.info(f"正在处理URL: {url}")
            match = re.search(r'/thread/(\d+)/', url)
            # 导入 scraper.py
            from scraper import scrape_comments
            
            if match:
                thread_id = match.group(1)
                filename = f"comments_{thread_id}.json"
                # 直接调用 scrape_comments 函数
                comments, new_comments_found = scrape_comments(url, filename)
                if new_comments_found:
                    logging.info("检测到新评论，正在运行 gemini_analyzer.py")
                    check_missing_ids(filename)
                    subprocess.run(["python", "gemini_analyzer.py", filename])
                else:
                    logging.info("没有检测到新评论，跳过 gemini_analyzer.py")
            else:
                logging.error(f"无法从URL {url} 中提取 thread_id")

if __name__ == "__main__":
    main()
