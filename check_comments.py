import json
import sys

def check_missing_ids(filename):
    """检查评论文件中缺失的 ID。"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            comments = json.load(f)
    except FileNotFoundError:
        print(f"错误：文件 {filename} 未找到")
        return

    existing_ids = [int(comment['id']) for comment in comments]
    if not existing_ids:
        print("文件中没有评论数据")
        return

    min_id = min(existing_ids)
    max_id = max(existing_ids)
    expected_ids = list(range(min_id, max_id + 1))
    missing_ids = [id for id in expected_ids if id not in existing_ids]

    if missing_ids:
        print(f"在 {filename} 文件中发现以下缺失的 ID:")
        print(missing_ids)
    else:
        print(f"在 {filename} 文件中未发现缺失的 ID")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        check_missing_ids(filename)
    else:
        print("用法: python check_comments.py <comments_filename>")
