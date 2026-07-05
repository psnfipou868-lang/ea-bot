import os
import time
import json
import urllib.request
import urllib.error

BOT_TOKEN = "8967466749:AAFMNlEI0lORHUG0EibzA92a2f93Hh199B4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

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

def process_command(chat_id, text):
    if text == "/start":
        send_message(chat_id, "🤖 بوت EA + Outlook + PSN Checker v3.0\n\n📌 الأوامر المتاحة:\n/generate - توليد إيميلات\n/check_ea - فحص EA\n/check_ms - فحص Microsoft\n/check_psn - فحص PlayStation\n/add_proxy - إضافة بروكسيات\n/stats - عرض الإحصائيات\n/export - تصدير النتائج\n/help - المساعدة")
    elif text == "/help":
        send_message(chat_id, "🤖 الأوامر المتاحة:\n/generate - توليد إيميلات\n/check_ea - فحص EA\n/check_ms - فحص Microsoft\n/check_psn - فحص PlayStation\n/add_proxy - إضافة بروكسيات\n/stats - إحصائيات\n/export - تصدير الملفات\n/help - هذه المساعدة")
    elif text == "/add_proxy":
        send_message(chat_id, "🌐 إضافة بروكسيات\nأرسل البروكسيات بالشكل التالي:\nhttp://user:pass@ip:port\nsocks5://ip:port\nhttp://ip:port\nواحد لكل سطر")
    elif text == "/generate":
        send_message(chat_id, "🚀 مولد الإيميلات\nاستخدم الأمر بهذا الشكل:\n/generate كلمة1 كلمة2\nمثال:\n/generate king night\nسيولد جميع الصيغ على جميع النطاقات")
    elif text == "/check_ea":
        emails = read_file(os.path.join(DATA_DIR, 'emails.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات! استخدم /generate أولاً")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم /add_proxy لإضافتها")
            return
        send_message(chat_id, f"▶️ بدء فحص EA لـ {len(emails)} إيميل...")
        linked = []
        not_linked = []
        total = len(emails)
        for i, email in enumerate(emails):
            proxy = proxies[i % len(proxies)]
            result = check_ea(email, proxy)
            if result:
                linked.append(email)
                append_file(os.path.join(DATA_DIR, 'Linked.txt'), email)
            else:
                not_linked.append(email)
                append_file(os.path.join(DATA_DIR, 'NotLinked.txt'), email)
            if (i + 1) % 10 == 0 or (i + 1) == total:
                send_message(chat_id, f"📊 {i+1}/{total}\n🔗 LINKED: {len(linked)}\n❌ NOT LINKED: {len(not_linked)}")
        send_message(chat_id, f"✅ انتهى فحص EA\n🔗 LINKED: {len(linked)}\n❌ NOT LINKED: {len(not_linked)}")
        if linked:
            send_file(chat_id, os.path.join(DATA_DIR, 'Linked.txt'), "🔗 الإيميلات المرتبطة بـ EA")
    elif text == "/check_ms":
        emails = read_file(os.path.join(DATA_DIR, 'NotLinked.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات غير مرتبطة! استخدم /check_ea أولاً")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم /add_proxy لإضافتها")
            return
        send_message(chat_id, f"▶️ بدء فحص Microsoft لـ {len(emails)} إيميل...")
        available = []
        not_available = []
        errors = []
        total = len(emails)
        for i, email in enumerate(emails):
            proxy = proxies[i % len(proxies)]
            result = check_ms(email, proxy)
            if result == 'available':
                available.append(email)
                append_file(os.path.join(DATA_DIR, 'Available.txt'), email)
            elif result == 'not_available':
                not_available.append(email)
                append_file(os.path.join(DATA_DIR, 'NotAvailable.txt'), email)
            else:
                errors.append(email)
                append_file(os.path.join(DATA_DIR, 'Errors.txt'), email)
            if (i + 1) % 10 == 0 or (i + 1) == total:
                send_message(chat_id, f"📊 Microsoft {i+1}/{total}\n📤 متاح: {len(available)}\n📥 غير متاح: {len(not_available)}\n⚠️ أخطاء: {len(errors)}")
        send_message(chat_id, f"✅ انتهى فحص Microsoft\n📤 متاح: {len(available)}\n📥 غير متاح: {len(not_available)}\n⚠️ أخطاء: {len(errors)}")
        if available:
            send_file(chat_id, os.path.join(DATA_DIR, 'Available.txt'), "📤 الإيميلات المتاحة")
    elif text == "/check_psn":
        emails = read_file(os.path.join(DATA_DIR, 'emails.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات! استخدم /generate أولاً")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم /add_proxy لإضافتها")
            return
        send_message(chat_id, f"▶️ بدء فحص PlayStation لـ {len(emails)} إيميل...")
        linked = []
        not_linked = []
        errors = []
        total = len(emails)
        for i, email in enumerate(emails):
            proxy = proxies[i % len(proxies)]
            status, online_id = check_psn(email, proxy)
            if status == 'linked':
                line = f"{email} | Online ID: {online_id}"
                linked.append(line)
                append_file(os.path.join(DATA_DIR, 'PSN_Linked.txt'), line)
            elif status == 'not_linked':
                not_linked.append(email)
                append_file(os.path.join(DATA_DIR, 'PSN_NotLinked.txt'), email)
            else:
                errors.append(email)
                append_file(os.path.join(DATA_DIR, 'PSN_Errors.txt'), email)
            if (i + 1) % 10 == 0 or (i + 1) == total:
                send_message(chat_id, f"📊 PSN {i+1}/{total}\n🎮 مرتبط: {len(linked)}\n❌ غير مرتبط: {len(not_linked)}\n⚠️ أخطاء: {len(errors)}")
        send_message(chat_id, f"✅ انتهى فحص PlayStation\n🎮 مرتبط (مع الـ ID): {len(linked)}\n❌ غير مرتبط: {len(not_linked)}\n⚠️ أخطاء: {len(errors)}")
        if linked:
            send_file(chat_id, os.path.join(DATA_DIR, 'PSN_Linked.txt'), "🎮 الإيميلات المرتبطة بـ PlayStation (مع الـ Online ID)")
    elif text == "/stats":
        files = {
            'emails.txt': '📧 الإيميلات الكلي',
            'Linked.txt': '🔗 مرتبط بـ EA',
            'NotLinked.txt': '❌ غير مرتبط بـ EA',
            'Available.txt': '📤 متاح (Microsoft)',
            'NotAvailable.txt': '📥 غير متاح (Microsoft)',
            'Errors.txt': '⚠️ أخطاء (Microsoft)',
            'PSN_Linked.txt': '🎮 مرتبط بـ PlayStation',
            'PSN_NotLinked.txt': '❌ غير مرتبط بـ PlayStation',
            'PSN_Errors.txt': '⚠️ أخطاء (PSN)'
        }
        msg = "📊 الإحصائيات:\n\n"
        for f, label in files.items():
            count = len(read_file(os.path.join(DATA_DIR, f)))
            msg += f"{label}: {count}\n"
        proxies = len(read_file(os.path.join(DATA_DIR, 'proxies.txt')))
        msg += f"\n🌐 البروكسيات المحملة: {proxies}"
        send_message(chat_id, msg)
    elif text == "/export":
        files_list = ['emails.txt', 'Linked.txt', 'NotLinked.txt', 'Available.txt', 'NotAvailable.txt', 'Errors.txt', 'PSN_Linked.txt', 'PSN_NotLinked.txt', 'PSN_Errors.txt']
        sent = 0
        for f in files_list:
            path = os.path.join(DATA_DIR, f)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                send_message(chat_id, f"📄 {f}: {len(read_file(path))} سطر")
                sent += 1
        if sent == 0:
            send_message(chat_id, "❌ لا توجد ملفات")
        else:
            send_message(chat_id, f"✅ تم عرض {sent} ملف")
    elif text.startswith('http') or text.startswith('socks'):
        proxies = [p.strip() for p in text.split('\n') if p.strip()]
        existing = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        all_proxies = existing + proxies
        write_file(os.path.join(DATA_DIR, 'proxies.txt'), all_proxies)
        send_message(chat_id, f"🌐 تم إضافة {len(proxies)} بروكسي\n📁 المجموع: {len(all_proxies)}")
    else:
        send_message(chat_id, f"❌ أمر غير معروف: {text}\nاستخدم /help")

def run_bot():
    print("🤖 البوت يعمل...")
    print(f"📁 البيانات: {DATA_DIR}")
    last_id = 0
    while True:
        try:
            updates = get_updates(last_id + 1)
            for u in updates:
                if u['update_id'] > last_id:
                    last_id = u['update_id']
                msg = u.get('message', {})
                chat_id = msg.get('chat', {}).get('id')
                text = msg.get('text', '')
                if chat_id and text:
                    print(f"📩 {text}")
                    process_command(chat_id, text)
            time.sleep(2)
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
