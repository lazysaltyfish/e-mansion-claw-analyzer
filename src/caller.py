import re
import sys
import logging
import argparse
import os
import asyncio
from tqdm import tqdm  # 导入 tqdm

# 将项目的根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.check_comments import check_missing_ids
from src.gemini_analyzer import analyze_comments_async
from src.scraper import scrape_comments

# 设置日志记录器,只输出 WARNING 和 ERROR 级别的信息
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

async def main(urls_file="urls.txt"):

    parser = argparse.ArgumentParser(description="处理URL并检查评论中的缺失ID。")
    parser.add_argument('--check-missing', action='store_true', help="检查给定文件中的缺失ID。")
    parser.add_argument('filename', nargs='?', default=None, help="检查缺失ID的文件名。")

    args = parser.parse_args()
    url_list = []
    try:
        with open(urls_file, "r") as f:
            for line in f:
                url = line.strip()
                if url:  # 确保URL不为空
                    url_list.append(url)
    except FileNotFoundError:
        logging.error(f"{urls_file} 文件未找到,请确保文件存在并包含URL列表。")
        sys.exit(1)

    if args.check_missing:
        if args.filename is None:
            logging.error("需要指定文件名以检查缺失ID。")
            sys.exit(1)
        check_missing_ids(args.filename)
    else:
        with tqdm(total=len(url_list), desc="处理进度") as pbar:
            for url in url_list:
                logging.debug(f"正在处理URL: {url}")
                match = re.search(r'/thread/(\d+)/', url)

                if match:
                    thread_id = match.group(1)
                    output_dir = "output/intermediate_results"  # 默认为中间结果输出目录
                    analysis_filename = os.path.join("output", "analysis_results", f"analysis_comments_{thread_id}_merged.json") # 正确的赋值位置
                    filename = f"comments_{thread_id}.json"
                    # 直接调用 scrape_comments 函数
                    comments, new_comments_found = scrape_comments(url, filename=filename, output_dir=output_dir)
                    if new_comments_found:
                        logging.debug("检测到新评论,正在检查缺失的ID...")
                        check_missing_ids(os.path.join("output", "intermediate_results", filename))

                    if new_comments_found or (analysis_filename is not None and not os.path.exists(analysis_filename)):
                        # 使用异步函数analyze_comments_async
                        logging.debug(f"正在为 URL: {url} 分析 {len(comments)} 条评论")
                        try:
                            result = await analyze_comments_async(comments)
                            # 保存分析结果
                            with open(analysis_filename, 'w', encoding='utf-8') as f:
                                f.write(result)
                        except asyncio.CancelledError:
                            logging.warning(f"分析任务 (URL: {url}) 被取消")
                        except Exception as e:
                            logging.error(f"分析 URL: {url} 时发生错误: {e}")
                    else:
                        logging.debug("没有检测到新评论,跳过分析")
                    pbar.update(1)  # 更新进度条
                else:
                    logging.error(f"无法从URL {url} 中提取 thread_id")

if __name__ == "__main__":
    asyncio.run(main())
