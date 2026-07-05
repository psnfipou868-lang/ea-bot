import os
import time
import json
import urllib.request
import urllib.error

BOT_TOKEN = "8967466749:AAFMNlEI0lORHUG0EibzA92a2f93Hh199B4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

user_sessions = {}

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
    global user_sessions
    
    # ===== جلسة التوليد =====
    if chat_id in user_sessions:
        session = user_sessions[chat_id]
        step = session.get('step')
        
        if step == 'awaiting_first':
            session['first'] = text.strip()
            session['step'] = 'awaiting_second'
            send_message(chat_id, "📝 أرسل الكلمة الثانية (أو /skip):")
            return
        
        elif step == 'awaiting_second':
            if text == '/skip':
                session['second'] = ''
            else:
                session['second'] = text.strip()
            
            first = session['first']
            second = session['second']
            domains = ['@hotmail.com', '@outlook.com', '@live.com', '@msn.com']
            
            results = set()
            separators = ['', '-', '.', '_']
            years = list(range(1970, 2031))
            numbers = list(range(0, 1000))
            extra_words = ['PLAY', 'PLAYSTATION', 'PLAYSTATION3', 'PS3', 'PSN']
            
            words = [first]
            if second:
                words.append(second)
            
            for w in words:
                results.add(w)
                for sep in separators:
                    if sep:
                        results.add(w + sep + w)
                    for num in numbers[:200]:
                        if sep:
                            results.add(w + sep + str(num))
                        else:
                            results.add(w + str(num))
                    for year in years[:20]:
                        if sep:
                            results.add(w + sep + str(year))
                        else:
                            results.add(w + str(year))
            
            if second:
                results.add(first + second)
                results.add(second + first)
                for sep in separators:
                    if sep:
                        results.add(first + sep + second)
                        results.add(second + sep + first)
                        for num in numbers[:200]:
                            results.add(first + sep + second + sep + str(num))
                            results.add(second + sep + first + sep + str(num))
                        for year in years[:20]:
                            results.add(first + sep + second + sep + str(year))
                            results.add(second + sep + first + sep + str(year))
                    else:
                        for num in numbers[:200]:
                            results.add(first + second + str(num))
                            results.add(second + first + str(num))
                        for year in years[:20]:
                            results.add(first + second + str(year))
                            results.add(second + first + str(year))
                
                for extra in extra_words:
                    for sep in separators:
                        if sep:
                            results.add(first + sep + extra)
                            results.add(second + sep + extra)
                            results.add(first + sep + second + sep + extra)
                        else:
                            results.add(first + extra)
                            results.add(second + extra)
                            results.add(first + second + extra)
            
            final = []
            for email in results:
                for domain in domains:
                    final.append(email + domain)
            final = list(set(final))
            write_file(os.path.join(DATA_DIR, 'emails.txt'), final)
            
            send_message(chat_id, f"✅ تم توليد {len(final)} إيميل\n📁 حفظ في emails.txt")
            sample = "\n".join(final[:15])
            send_message(chat_id, f"📋 عينة:\n{sample}")
            
            del user_sessions[chat_id]
            return
    
    # ===== الأوامر الرئيسية =====
    if text == "/start":
        send_message(chat_id, "🤖 بوت EA + Outlook + PSN v3.0\n/generate - توليد إيميلات\n/check_ea - فحص EA\n/check_ms - فحص Microsoft\n/check_psn - فحص PlayStation\n/add_proxy - إضافة بروكسيات\n/stats - إحصائيات\n/export - تصدير\n/help - مساعدة")
    
    elif text == "/help":
        send_message(chat_id, "الأوامر:\n/generate - توليد إيميلات\n/check_ea - فحص EA\n/check_ms - فحص Microsoft\n/check_psn - فحص PlayStation\n/add_proxy - إضافة بروكسيات\n/stats - إحصائيات\n/export - تصدير الملفات")
    
    elif text == "/add_proxy":
        send_message(chat_id, "🌐 أرسل البروكسيات بالشكل:\nhttp://user:pass@ip:port\nsocks5://ip:port\nhttp://ip:port\nواحد لكل سطر")
    
    elif text == "/generate":
        user_sessions[chat_id] = {'step': 'awaiting_first'}
        send_message(chat_id, "📝 أرسل الكلمة الأولى (مثل: king):")
    
    elif text == "/check_ea":
        emails = read_file(os.path.join(DATA_DIR, 'emails.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات! استخدم /generate")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم /add_proxy")
            return
        send_message(chat_id, f"▶️ فحص EA لـ {len(emails)} إيميل...")
        linked, not_linked = [], []
        total = len(emails)
        for i, email in enumerate(emails):
            proxy = proxies[i % len(proxies)]
            if check_ea(email, proxy):
                linked.append(email)
                append_file(os.path.join(DATA_DIR, 'Linked.txt'), email)
            else:
                not_linked.append(email)
                append_file(os.path.join(DATA_DIR, 'NotLinked.txt'), email)
            if (i+1) % 10 == 0 or (i+1) == total:
                send_message(chat_id, f"📊 {i+1}/{total}\n🔗 {len(linked)}\n❌ {len(not_linked)}")
        send_message(chat_id, f"✅ انتهى EA\n🔗 {len(linked)}\n❌ {len(not_linked)}")
        if linked:
            send_file(chat_id, os.path.join(DATA_DIR, 'Linked.txt'), "🔗 المرتبطة بـ EA")
    
    elif text == "/check_ms":
        emails = read_file(os.path.join(DATA_DIR, 'NotLinked.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات غير مرتبطة! استخدم /check_ea")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات!")
            return
        send_message(chat_id, f"▶️ فحص Microsoft لـ {len(emails)} إيميل...")
        available, not_available, errors = [], [], []
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
            if (i+1) % 10 == 0 or (i+1) == total:
                send_message(chat_id, f"📊 MS {i+1}/{total}\n📤 {len(available)}\n📥 {len(not_available)}\n⚠️ {len(errors)}")
        send_message(chat_id, f"✅ انتهى MS\n📤 {len(available)}\n📥 {len(not_available)}\n⚠️ {len(errors)}")
        if available:
            send_file(chat_id, os.path.join(DATA_DIR, 'Available.txt'), "📤 المتاحة")
    
    elif text == "/check_psn":
        emails = read_file(os.path.join(DATA_DIR, 'emails.txt'))
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات!")
            return
        proxies = read_file(os.path.join(DATA_DIR, 'proxies.txt'))
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات!")
            return
        send_message(chat_id, f"▶️ فحص PSN لـ {len(emails)} إيميل...")
        linked, not_linked, errors = [], [], []
        total = len(emails)
        for i, email in enumerate(emails):
            proxy = proxies[i % len(proxies)]
            status, online_id = check_psn(email, proxy)
            if status == 'linked':
                line = f"{email} | ID: {online_id}"
                linked.append(line)
                append_file(os.path.join(DATA_DIR, 'PSN_Linked.txt'), line)
            elif status == 'not_linked':
                not_linked.append(email)
                append_file(os.path.join(DATA_DIR, 'PSN_NotLinked.txt'), email)
            else:
                errors.append(email)
                append_file(os.path.join(DATA_DIR, 'PSN_Errors.txt'), email)
            if (i+1) % 10 == 0 or (i+1) == total:
                send_message(chat_id, f"📊 PSN {i+1}/{total}\n🎮 {len(linked)}\n❌ {len(not_linked)}\n⚠️ {len(errors)}")
        send_message(chat_id, f"✅ انتهى PSN\n🎮 {len(linked)}\n❌ {len(not_linked)}\n⚠️ {len(errors)}")
        if linked:
            send_file(chat_id, os.path.join(DATA_DIR, 'PSN_Linked.txt'), "🎮 المرتبطة بـ PSN (مع الـ ID)")
    
    elif text == "/stats":
        files = {
            'emails.txt': '📧 الإيميلات الكلي',
            'Linked.txt': '🔗 مرتبط بـ EA',
            'NotLinked.txt': '❌ غير مرتبط بـ EA',
            'Available.txt': '📤 متاح (MS)',
            'NotAvailable.txt': '📥 غير متاح (MS)',
            'Errors.txt': '⚠️ أخطاء (MS)',
            'PSN_Linked.txt': '🎮 مرتبط بـ PSN',
            'PSN_NotLinked.txt': '❌ غير مرتبط بـ PSN',
            'PSN_Errors.txt': '⚠️ أخطاء PSN'
        }
        msg = "📊 الإحصائيات:\n"
        for f, label in files.items():
            count = len(read_file(os.path.join(DATA_DIR, f)))
            msg += f"{label}: {count}\n"
        proxies = len(read_file(os.path.join(DATA_DIR, 'proxies.txt')))
        msg += f"🌐 بروكسيات: {proxies}"
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
