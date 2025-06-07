import smtplib
from email.message import EmailMessage
import requests
import time
import os

# === CONFIGURATION ===
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")        # Set in Railway or env vars
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")      # Set in Railway or env vars

CHAIN = "eth"                                      # Can be 'eth', 'base', 'solana', etc.
VOLUME_THRESHOLD = 2.0                             # 2.0 = 200% volume spike
CHECK_INTERVAL = 300                               # Seconds between checks (5 mins)

sent_tokens = set()  # Prevent duplicate alerts per session


def get_trending_tokens():
    url = f"https://api.geckoterminal.com/api/v2/networks/{CHAIN}/trending_pools"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def send_email_alert(token_name, volume_change, price_change, url):
    msg = EmailMessage()
    msg["Subject"] = f"🚀 [MEME ALERT] {token_name} pumping: +{volume_change:.0f}% volume"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    msg.set_content(f"""
Token: {token_name}
Volume Spike: {volume_change:.0f}%
Price Change: {price_change:.2f}%
Chart: {url}

Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent for {token_name}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def scan_tokens():
    tokens = get_trending_tokens()
    for token in tokens:
        try:
            attrs = token["attributes"]
            token_name = attrs["name"]
            token_url = f"https://www.geckoterminal.com/{CHAIN}/pools/{token['id'].split('/')[-1]}"

            vol_change = float(attrs["volume_usd_change_percentage"].replace("%", ""))
            price_change = float(attrs["price_change_percentage"].replace("%", ""))

            if vol_change >= VOLUME_THRESHOLD * 100 and token_name not in sent_tokens:
                send_email_alert(token_name, vol_change, price_change, token_url)
                sent_tokens.add(token_name)

        except Exception as e:
            print(f"Error processing token: {e}")


if __name__ == "__main__":
    print("🚨 Memecoin pump alert system started...")
    while True:
        scan_tokens()
        time.sleep(CHECK_INTERVAL)
