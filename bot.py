import time
import json
import urllib.request
import urllib.error
import threading
import logging
from pathlib import Path

# ============================================
# 📋 إعدادات التسجيل
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# 🔑 توكن البوت
# ============================================
BOT_TOKEN = "8761475257:AAFWe7VRfRSaKtPC-bRAkcZy_oh9VUzJIEk"

# ============================================
# 📁 الإعدادات
# ============================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

user_sessions = {}
running_tasks = {}

# ============================================
# 📂 دوال الملفات (محسّنة)
# ============================================
def read_file(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        logger.warning("File not found: %s", file_path)
        return []
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    except OSError as exc:
        logger.exception("Failed to read file: %s", exc)
        return []

def write_file(path: str, data: list[str]) -> None:
    file_path = Path(path)
    try:
        with file_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(data))
        logger.info("Written %d lines to %s", len(data), file_path)
    except OSError as exc:
        logger.exception("Failed to write file: %s", exc)

def append_file(path: str, line: str) -> None:
    file_path = Path(path)
    try:
        with file_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as exc:
        logger.exception("Failed to append to file: %s", exc)

def clear_file(path: str) -> None:
    file_path = Path(path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info("Cleared file: %s", file_path)
        except OSError as exc:
            logger.exception("Failed to clear file: %s", exc)

# ============================================
# 🔍 دوال الفحص (مع معالجة الأخطاء)
# ============================================
def check_ea(email, proxy=None):
    try:
        url = f'https://signin.ea.com/p/ajax/user/checkEmailAvailability?email={email}'
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get('available') == True:
                return 'not-linked'
            return 'linked'
    except Exception as exc:
        logger.exception("EA check error for %s: %s", email, exc)
        return 'error'

def check_ms(email, proxy=None):
    try:
        url = 'https://login.microsoftonline.com/common/GetCredentialType'
        data = json.dumps({"username": email, "isOtherIdpSupported": True}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode())
            if result.get('IfExistsResult') == 1:
                return 'available'
            elif result.get('IfExistsResult') in [0, 4, 5, 6]:
                return 'not-available'
            else:
                return 'error'
    except Exception as exc:
        logger.exception("MS check error for %s: %s", email, exc)
        return 'error'

def check_psn(email, proxy=None):
    try:
        url = 'https://ca.account.sony.com/api/v1/ssocookie'
        data = json.dumps({
            "authentication_type": "password",
            "username": email,
            "password": "Probe__X9$!!"
        }).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode())
            error_code = result.get('error_code', '')
            if error_code in ['4165', '4145', '4100', '4155']:
                return 'linked'
            elif error_code in ['4168', '4150', '4160']:
                return 'not-linked'
            else:
                return 'error'
    except Exception as exc:
        logger.exception("PSN check error for %s: %s", email, exc)
        if 'account.notfound' in str(exc):
            return 'not-linked'
        return 'error'

# ============================================
# 🚀 مولد الإيميلات (جميع الصيغ)
# ============================================
def generate_emails(first, second=''):
    domains = ['@hotmail.com', '@outlook.com', '@live.com', '@msn.com']
    results = set()
    separators = ['', '-', '.', '_']
    years = list(range(1970, 2031))
    numbers = list(range(0, 1000))
    extra_words = ['PLAY', 'PLAYSTATION', 'PS3', 'PSN', 'GAMER', 'PRO', 'KING']
    
    words = [first]
    if second:
        words.append(second)
    
    for w in words:
        results.add(w)
        for sep in separators:
            if sep:
                results.add(w + sep + w)
            for num in numbers:
                if sep:
                    results.add(w + sep + str(num))
                else:
                    results.add(w + str(num))
            for year in years:
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
                for num in numbers:
                    results.add(first + sep + second + sep + str(num))
                    results.add(second + sep + first + sep + str(num))
                for year in years:
                    results.add(first + sep + second + sep + str(year))
                    results.add(second + sep + first + sep + str(year))
            else:
                for num in numbers:
                    results.add(first + second + str(num))
                    results.add(second + first + str(num))
                for year in years:
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
        
        for sep1 in ['-', '.', '_']:
            for sep2 in ['-', '.', '_']:
                results.add(first + sep1 + second + sep2 + '0')
                results.add(first + sep1 + second + sep2 + '100')
                results.add(first + sep1 + second + sep2 + '123')
                results.add(first + sep1 + second + sep2 + '2026')
                for num in numbers[:100]:
                    results.add(first + sep1 + second + sep2 + str(num))
    
    final = []
    for email in results:
        for domain in domains:
            final.append(email + domain)
    return list(set(final))

# ============================================
# 🌐 دوال التلغرام (مع تحسين getUpdates)
# ============================================
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = f"chat_id={chat_id}&text={text}&parse_mode=Markdown"
        req = urllib.request.Request(url, data=data.encode('utf-8'), method='POST')
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as exc:
        logger.exception("Failed to send message: %s", exc)
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
            f'Content-Disposition: form-data; name="document"; filename="{Path(file_path).name}"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
        ).encode('utf-8') + file_data + f"\r\n--{boundary}--\r\n".encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        urllib.request.urlopen(req, timeout=30)
        return True
    except Exception as exc:
        logger.exception("Failed to send file: %s", exc)
        return False

def get_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode())
            return data.get('result', [])
    except Exception as exc:
        logger.exception("Failed to get updates: %s", exc)
        return []

# ============================================
# ⚙️ تشغيل الفحوصات (خيوط)
# ============================================
def run_ea_check(chat_id, emails, proxies):
    clear_file(DATA_DIR / 'Linked.txt')
    clear_file(DATA_DIR / 'NotLinked.txt')
    
    send_message(chat_id, f"▶️ **بدء فحص EA** لـ {len(emails)} إيميل...")
    linked, not_linked = [], []
    total = len(emails)
    for i, email in enumerate(emails):
        if not running_tasks.get(chat_id, True):
            send_message(chat_id, "⏹️ تم إيقاف الفحص")
            break
        proxy = proxies[i % len(proxies)] if proxies else None
        result = check_ea(email, proxy)
        if result == 'linked':
            linked.append(email)
            append_file(DATA_DIR / 'Linked.txt', email)
        elif result == 'not-linked':
            not_linked.append(email)
            append_file(DATA_DIR / 'NotLinked.txt', email)
        if (i+1) % 10 == 0 or (i+1) == total:
            send_message(chat_id, f"📊 **{i+1}/{total}**\n🔗 مرتبط: {len(linked)}\n❌ غير مرتبط: {len(not_linked)}")
    send_message(chat_id, f"✅ **انتهى فحص EA**\n🔗 مرتبط: {len(linked)}\n❌ غير مرتبط: {len(not_linked)}")
    if linked:
        send_file(chat_id, DATA_DIR / 'Linked.txt', "🔗 الإيميلات المرتبطة بـ EA")
    if not_linked:
        run_ms_check(chat_id, not_linked, proxies)
    else:
        running_tasks[chat_id] = False

def run_ms_check(chat_id, emails, proxies):
    clear_file(DATA_DIR / 'Available.txt')
    clear_file(DATA_DIR / 'NotAvailable.txt')
    clear_file(DATA_DIR / 'Errors.txt')
    
    send_message(chat_id, f"▶️ **بدء فحص Microsoft** لـ {len(emails)} إيميل...")
    available, not_available, errors = [], [], []
    total = len(emails)
    for i, email in enumerate(emails):
        if not running_tasks.get(chat_id, True):
            send_message(chat_id, "⏹️ تم إيقاف الفحص")
            break
        proxy = proxies[i % len(proxies)] if proxies else None
        result = check_ms(email, proxy)
        if result == 'available':
            available.append(email)
            append_file(DATA_DIR / 'Available.txt', email)
        elif result == 'not-available':
            not_available.append(email)
            append_file(DATA_DIR / 'NotAvailable.txt', email)
        else:
            errors.append(email)
            append_file(DATA_DIR / 'Errors.txt', email)
        if (i+1) % 10 == 0 or (i+1) == total:
            send_message(chat_id, f"📊 **MS {i+1}/{total}**\n📤 متاح: {len(available)}\n📥 غير متاح: {len(not_available)}\n⚠️ أخطاء: {len(errors)}")
    send_message(chat_id, f"✅ **انتهى فحص Microsoft**\n📤 متاح: {len(available)}\n📥 غير متاح: {len(not_available)}\n⚠️ أخطاء: {len(errors)}")
    if available:
        send_file(chat_id, DATA_DIR / 'Available.txt', "📤 الإيميلات المتاحة")
    running_tasks[chat_id] = False

def run_psn_check(chat_id, emails, proxies):
    clear_file(DATA_DIR / 'PSN_Linked.txt')
    clear_file(DATA_DIR / 'PSN_NotLinked.txt')
    clear_file(DATA_DIR / 'PSN_Errors.txt')
    
    send_message(chat_id, f"▶️ **بدء فحص PlayStation** لـ {len(emails)} إيميل...")
    linked, not_linked, errors = [], [], []
    total = len(emails)
    for i, email in enumerate(emails):
        if not running_tasks.get(chat_id, True):
            send_message(chat_id, "⏹️ تم إيقاف الفحص")
            break
        proxy = proxies[i % len(proxies)] if proxies else None
        result = check_psn(email, proxy)
        if result == 'linked':
            linked.append(email)
            append_file(DATA_DIR / 'PSN_Linked.txt', email)
        elif result == 'not-linked':
            not_linked.append(email)
            append_file(DATA_DIR / 'PSN_NotLinked.txt', email)
        else:
            errors.append(email)
            append_file(DATA_DIR / 'PSN_Errors.txt', email)
        if (i+1) % 10 == 0 or (i+1) == total:
            send_message(chat_id, f"📊 **PSN {i+1}/{total}**\n🎮 مرتبط: {len(linked)}\n❌ غير مرتبط: {len(not_linked)}\n⚠️ أخطاء: {len(errors)}")
    send_message(chat_id, f"✅ **انتهى فحص PlayStation**\n🎮 مرتبط: {len(linked)}\n❌ غير مرتبط: {len(not_linked)}\n⚠️ أخطاء: {len(errors)}")
    if linked:
        send_file(chat_id, DATA_DIR / 'PSN_Linked.txt', "🎮 الإيميلات المرتبطة بـ PSN")
    running_tasks[chat_id] = False

# ============================================
# ⚙️ معالج الأوامر (محسّن)
# ============================================
def process_command(chat_id, text):
    global user_sessions
    
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
            emails = generate_emails(first, second)
            write_file(DATA_DIR / 'emails.txt', emails)
            send_message(chat_id, f"✅ **تم توليد {len(emails)} إيميل**\n📁 حفظ في `emails.txt`")
            sample = "\n".join(emails[:15])
            send_message(chat_id, f"📋 **عينة من الإيميلات:**\n```\n{sample}\n```")
            del user_sessions[chat_id]
            return
    
    # ===== قائمة الأوامر الرئيسية =====
    menu = """
🤖 **EA + Outlook + PSN Checker v4.0** 🌟

📌 **الأوامر المتاحة:**

/generate  🚀 توليد إيميلات (تفاعلي)
/check_ea   🔍 فحص EA (تلقائي يشمل MS)
/check_psn  🎮 فحص PlayStation
/add_proxy  🌐 إضافة بروكسيات (رفع ملف أو كتابة)
/check      📧 فحص إيميل واحد
/stop       ⏹️ إيقاف الفحص
/stats      📊 إحصائيات
/export     📁 تصدير النتائج
/menu       📋 عرض هذه القائمة
/help       ❓ المساعدة
"""
    
    if text == "/start" or text == "/menu":
        send_message(chat_id, menu)
    
    elif text == "/help":
        send_message(chat_id, menu)
    
    elif text == "/add_proxy":
        send_message(chat_id, "📤 **أرسل البروكسيات** (نصاً أو ملفاً)\nكل بروكسي في سطر:\n`http://user:pass@ip:port`\n`socks5://ip:port`\n`http://ip:port`")
    
    elif text == "/generate":
        user_sessions[chat_id] = {'step': 'awaiting_first'}
        send_message(chat_id, "📝 أرسل الكلمة الأولى (مثل: `king`):")
    
    elif text == "/stop":
        running_tasks[chat_id] = False
        send_message(chat_id, "⏹️ جاري إيقاف الفحص...")
    
    elif text == "/check_ea":
        emails = read_file(DATA_DIR / 'emails.txt')
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات! استخدم `/generate` أولاً")
            return
        proxies = read_file(DATA_DIR / 'proxies.txt')
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم `/add_proxy`")
            return
        running_tasks[chat_id] = True
        threading.Thread(target=run_ea_check, args=(chat_id, emails, proxies), daemon=True).start()
    
    elif text == "/check_psn":
        emails = read_file(DATA_DIR / 'emails.txt')
        if not emails:
            send_message(chat_id, "❌ لا توجد إيميلات! استخدم `/generate`")
            return
        proxies = read_file(DATA_DIR / 'proxies.txt')
        if not proxies:
            send_message(chat_id, "⚠️ لا توجد بروكسيات! استخدم `/add_proxy`")
            return
        running_tasks[chat_id] = True
        threading.Thread(target=run_psn_check, args=(chat_id, emails, proxies), daemon=True).start()
    
    elif text == "/check":
        # تنسيق /check email@example.com
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "❌ استخدم: `/check email@example.com`")
            return
        email = parts[1]
        if '@' not in email:
            send_message(chat_id, "❌ الإيميل غير صالح")
            return
        # فحص فوري
        send_message(chat_id, f"📧 جاري فحص: `{email}`")
        proxy = read_file(DATA_DIR / 'proxies.txt')
        p = proxy[0] if proxy else None
        ea = check_ea(email, p)
        ms = check_ms(email, p)
        psn = check_psn(email, p)
        send_message(chat_id, f"📧 **{email}**\n🔗 EA: {ea}\n📤 MS: {ms}\n🎮 PSN: {psn}")
    
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
        msg = "📊 **الإحصائيات:**\n"
        for f, label in files.items():
            count = len(read_file(DATA_DIR / f))
            msg += f"{label}: {count}\n"
        proxies = len(read_file(DATA_DIR / 'proxies.txt'))
        msg += f"🌐 بروكسيات محملة: {proxies}"
        send_message(chat_id, msg)
    
    elif text == "/export":
        files_list = ['Linked.txt', 'NotLinked.txt', 'Available.txt', 'NotAvailable.txt', 'Errors.txt', 'PSN_Linked.txt', 'PSN_NotLinked.txt', 'PSN_Errors.txt']
        sent = 0
        for f in files_list:
            path = DATA_DIR / f
            if path.exists() and path.stat().st_size > 0:
                send_file(chat_id, path, f"📄 {f}")
                sent += 1
        if sent == 0:
            send_message(chat_id, "❌ لا توجد نتائج للتصدير")
        else:
            send_message(chat_id, f"✅ تم إرسال {sent} ملف")
    
    else:
        # أي أمر غير معروف – لا نرد (يسكت)
        pass

# ============================================
# 🏃 تشغيل البوت
# ============================================
def run_bot():
    logger.info("🤖 EA + Outlook + PSN Checker v4.0")
    logger.info("📁 البيانات: %s", DATA_DIR)
    last_id = 0
    
    while True:
        try:
            updates = get_updates(last_id + 1)
            for u in updates:
                if u['update_id'] > last_id:
                    last_id = u['update_id']
                
                msg = u.get('message', {})
                chat_id = msg.get('chat', {}).get('id')
                
                if 'document' in msg:
                    file_id = msg['document']['file_id']
                    try:
                        get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
                        req = urllib.request.Request(get_file_url, method='GET')
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            file_info = json.loads(resp.read().decode())
                            file_path = file_info['result']['file_path']
                            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                            req2 = urllib.request.Request(download_url, method='GET')
                            with urllib.request.urlopen(req2, timeout=30) as resp2:
                                content = resp2.read().decode('utf-8', errors='ignore')
                                proxies = [p.strip() for p in content.split('\n') if p.strip()]
                                write_file(DATA_DIR / 'proxies.txt', proxies)
                                send_message(chat_id, f"🌐 تم استلام {len(proxies)} بروكسي وحفظها بنجاح\n📁 المجموع: {len(proxies)}")
                    except Exception as exc:
                        logger.exception("Failed to process uploaded file: %s", exc)
                        send_message(chat_id, f"❌ فشل في قراءة الملف: {str(exc)}")
                    continue
                
                text = msg.get('text', '')
                if chat_id and text:
                    if text.startswith('/'):
                        logger.info("📩 أمر: %s", text)
                        process_command(chat_id, text)
                    elif text.startswith('http') or text.startswith('socks'):
                        proxies = [p.strip() for p in text.split('\n') if p.strip()]
                        existing = read_file(DATA_DIR / 'proxies.txt')
                        all_proxies = existing + proxies
                        write_file(DATA_DIR / 'proxies.txt', all_proxies)
                        send_message(chat_id, f"🌐 تم إضافة {len(proxies)} بروكسي\n📁 المجموع: {len(all_proxies)}")
                    elif '@' in text and len(text.split()) == 1:
                        email = text.strip()
                        send_message(chat_id, f"📧 جاري فحص: `{email}`")
                        proxy = read_file(DATA_DIR / 'proxies.txt')
                        p = proxy[0] if proxy else None
                        ea = check_ea(email, p)
                        ms = check_ms(email, p)
                        psn = check_psn(email, p)
                        send_message(chat_id, f"📧 **{email}**\n🔗 EA: {ea}\n📤 MS: {ms}\n🎮 PSN: {psn}")
            
            time.sleep(2)
        except Exception as exc:
            logger.exception("Unexpected error in main loop: %s", exc)
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
