"""
反馈邮箱检查脚本
每周运行一次，检查未读邮件并保存到桌面
授权码从本地 secret.json 读取（该文件不提交到 git）
"""
import imaplib
import email
from email.header import decode_header
import json
import os
import re
from datetime import datetime

IMAP_SERVER = "imap.qq.com"
EMAIL_ADDR = "2179662832@qq.com"
OUTPUT_DIR = os.path.expanduser(r"E:\桌面\反馈邮件")
MAX_EMAILS = 30


def contains_chinese(text):
    """判断文本是否包含中文字符（CJK统一表意文字）"""
    return bool(re.search(r"[一-鿿]", text))


def contains_japanese_kana(text):
    """判断文本是否包含日文假名（平假名/片假名）"""
    return bool(re.search(r"[぀-ヿ]", text))


def is_chinese_email(subject, body):
    """只保留中文邮件：含中文字符且不含日文假名"""
    text = (subject or "") + (body or "")
    if not contains_chinese(text):
        return False  # 排除纯英文等无中文的邮件
    if contains_japanese_kana(text):
        return False  # 排除日文邮件
    return True

# 授权码从仓库外的本地文件读取
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_FILE = os.path.join(SCRIPT_DIR, "secret.json")


def load_auth_code():
    if not os.path.exists(SECRET_FILE):
        raise FileNotFoundError(f"缺少 {SECRET_FILE}，请创建并填入授权码")
    with open(SECRET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["auth_code"]


def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                result.append(text.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(text.decode("utf-8", errors="replace"))
        else:
            result.append(str(text))
    return "".join(result)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = os.path.join(OUTPUT_DIR, f"反馈_{stamp}.txt")

    try:
        auth_code = load_auth_code()
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDR, auth_code)
        mail.select("INBOX")

        status, data = mail.search(None, "UNSEEN")
        if status != "OK":
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 搜索失败\n")
            mail.logout()
            return

        msg_ids = data[0].split()
        if not msg_ids:
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 无新邮件\n")
            mail.logout()
            return

        emails = []
        filtered_count = 0
        for mid in msg_ids[-MAX_EMAILS:]:
            status, data = mail.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(data[0][1])
            subject = decode_str(msg["Subject"])
            sender = decode_str(msg.get("From", ""))
            date_str = msg.get("Date", "")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        except Exception:
                            body = str(part.get_payload())
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    body = str(msg.get_payload())

            # 语言筛选：只保留中文邮件
            if not is_chinese_email(subject, body):
                filtered_count += 1
                continue
            emails.append({"subject": subject, "sender": sender, "date": date_str, "body": body[:2000]})

        with open(out, "w", encoding="utf-8") as f:
            f.write(f"反馈邮箱检查报告\n时间：{datetime.now()}\n中文邮件：{len(emails)} 封（已过滤非中文邮件 {filtered_count} 封）\n{'=' * 60}\n\n")
            for i, em in enumerate(emails, 1):
                f.write(f"--- 第{i}封 ---\n发件人：{em['sender']}\n时间：{em['date']}\n主题：{em['subject']}\n\n{em['body']}\n\n")
        mail.logout()
    except Exception as e:
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 错误：{e}\n")


if __name__ == "__main__":
    main()
