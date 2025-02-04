import json
import logging
from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO, format='%(message)s')
def check_missing_ids(filename):
    """检查评论文件中缺失的 ID。"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            comments = json.load(f)
    except FileNotFoundError:
        logging.error(f"错误:文件 {filename} 未找到")
        return

    existing_ids = [int(comment['id']) for comment in comments]
    if not existing_ids:
        logging.info("文件中没有评论数据")
        return

    min_id = min(existing_ids)
    max_id = max(existing_ids)
    expected_ids = list(range(min_id, max_id + 1))
    missing_ids = [id for id in expected_ids if id not in existing_ids]

    if missing_ids:
        logging.info(f"发现以下缺失的 ID: {missing_ids}")
    else:
        logging.info(f"未发现缺失的 ID")


if __name__ == "__main__":
    parser = ArgumentParser(description="检查评论文件中的缺失ID。")
    parser.add_argument('filename', help="包含评论数据的文件名。")

    args = parser.parse_args()
    check_missing_ids(args.filename)
