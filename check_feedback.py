"""
反馈邮箱检查脚本
每周运行一次，检查未读邮件并保存到桌面
"""
import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime

IMAP_SERVER = "imap.qq.com"
EMAIL_ADDR = "2179662832@qq.com"
AUTH_CODE = "REDACTED_请重新生成"
OUTPUT_DIR = os.path.expanduser(r"E:\桌面\反馈邮件")
MAX_EMAILS = 30

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
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDR, AUTH_CODE)
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
            emails.append({"subject": subject, "sender": sender, "date": date_str, "body": body[:2000]})

        with open(out, "w", encoding="utf-8") as f:
            f.write(f"反馈邮箱检查报告\n时间：{datetime.now()}\n未读：{len(emails)} 封\n{'=' * 60}\n\n")
            for i, em in enumerate(emails, 1):
                f.write(f"--- 第{i}封 ---\n发件人：{em['sender']}\n时间：{em['date']}\n主题：{em['subject']}\n\n{em['body']}\n\n")
        mail.logout()
    except Exception as e:
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 错误：{e}\n")

if __name__ == "__main__":
    main()
