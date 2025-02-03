import subprocess
import re
import sys

# 从 check_comments.py 导入 check_missing_ids 函数
from check_comments import check_missing_ids

# 硬编码的URL列表
url_list = [
    "https://www.e-mansion.co.jp/bbs/thread/683455/",
]

# 遍历处理每个URL
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check_missing":
        filename = sys.argv[2]
        check_missing_ids(filename) # 直接调用导入的函数
    else:
        for url in url_list:
            print(f"正在处理URL: {url}")
            # 从 url 中提取 thread_id
            match = re.search(r'/thread/(\d+)/', url)
            if match:
                thread_id = match.group(1)
                filename = f"comments_{thread_id}.json"
                subprocess.run(["python", "scraper.py", "scrape", url, filename]) # 将文件名传递给 scraper.py
                check_missing_ids(filename) # 在 scraper 完成后检查缺失的 ID
            else:
                print(f"无法从URL {url} 中提取 thread_id")
