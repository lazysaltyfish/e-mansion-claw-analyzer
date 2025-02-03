import subprocess

# 硬编码的URL列表
url_list = [
    "https://www.e-mansion.co.jp/bbs/thread/683455/",
    "https://www.e-mansion.co.jp/bbs/thread/123456/",
    "https://www.e-mansion.co.jp/bbs/thread/789012/"
]

# 遍历处理每个URL
for url in url_list:
    print(f"正在处理URL: {url}")
    subprocess.run(["python", "scraper.py", "scrape", url])
