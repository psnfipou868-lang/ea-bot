import os
import time
import json
import urllib.request
import urllib.error

# ============================================
# 🔑 توكن البوت (محدث)
# ============================================
BOT_TOKEN = "8967466749:AAFMNlEI0lORHUG0EibzA92a2f93Hh199B4"

# ============================================
# 📁 الإعدادات
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================
# 📂 دوال الملفات
# ============================================
def read_file(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]

def write_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(data))

def append_file(path, data):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(data + '\n')

# ============================================
# 🔍 فاحص EA
# ============================================
def check_ea(email, proxy=None):
    try:
        url = f'https://signin.ea.com/p/{email}'
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except:
        return False

# ============================================
# 🔍 فاحص Microsoft (Outlook/Hotmail/Live/MSN)
# ============================================
def check_ms(email, proxy=None):
    try:
        url = 'https://login.live.com/GetCredentialType.srf'
        data = json.dumps({"Username": email}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode())
            if result.get('IfExistsResult') == 0:
                return 'available'
            elif result.get('IfExistsResult') == 1:
                return 'not_available'
            else:
                return 'error'
    except:
        return 'error'

# ============================================
# 🔍 فاحص PlayStation (PSN)
# ============================================
def check_psn(email, proxy=None):
    try:
        url = 'https://account.sonyentertainmentnetwork.com/api/v1/ssoc/email'
        data = json.dumps({"email": email}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode())
            if result.get('emailExists') == True:
                online_id = result.get('onlineId', 'غير معروف')
                return 'linked', online_id
            else:
                return 'not_linked', None
    except Exception as e:
        if 'account.notfound' in str(e):
            return 'not_linked', None
        return 'error', None

# ============================================
# 🌐 دوال التلغرام
# ============================================
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = f"chat_id={chat_id}&text={text}&parse_mode=Markdown"
        req = urllib.request.Request(url, data=data.encode('utf-8'), method='POST')
        urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

def send_file(chat_id, file_path, caption=""):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(file_path, 'rb') as f:
            file_data = f.read()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="document"; filename="{os.path.basename(file_path)}"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
        ).encode('utf-8') + file_data + f"\r\n--{boundary}--\r\n".encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        urllib.request.urlopen(req, timeout=30)
        return True
    except:
        return False

def get_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        if offset:
            url += f"?offset={offset}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('result', [])
    except:
        return []

# ============================================
# ⚙️ معالج الأوامر
# ============================================
def process_command(chat_id, text):
    
    if text == "/start":
        send_message(chat_id, """
🤖 **بوت EA + Outlook + PSN Checker v3.0**

📌 **الأوامر المتاحة:**

/generate - توليد إيميلات
/check_ea - فحص EA (LINKED / NOT LINKED)
/check_ms - فحص Microsoft (متاح / غير متاح)
/check_psn - فحص PlayStation (مع إظهار الـ Online ID)
/add_proxy - إضافة بروكسيات
/stats - عرض الإحصائيات
/export - تصدير النتائج
/help - المساعدة

📁 **النتائج تحفظ في مجلد data/**
        """)
    
    elif text == "/help":
        send_message(chat_id, """
🤖 **الأوامر المتاحة:**

/generate - توليد إيميلات
/check_ea - فحص EA (LINKED / NOT LINKED)
/check_ms - فحص Microsoft (متاح / غير متاح)
/check_psn - فحص PlayStation (مع إظهار الـ Online ID)
/add_proxy - إضافة بروكسيات
/stats - إحصائيات
/export - تصدير الملفات
/help - هذه المساعدة
        """)
    
    elif text == "/add_proxy":
        send_message(chat_id, """
🌐 **إضافة بروكسيات**

أرسل البروكسيات بالشكل التالي:
