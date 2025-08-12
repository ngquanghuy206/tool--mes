import json
import time
import hashlib
import random
import string
import requests
import paho.mqtt.client as mqtt
import ssl
import re
from urllib.parse import urlparse
from collections import defaultdict
import threading

ng_quang_huy_cookie_attempts = defaultdict(lambda: {'count': 0, 'last_reset': time.time(), 'banned_until': 0, 'permanent_ban': False})
ng_quang_huy_active_threads = {}

def ng_quang_huy_handle_failed_connection(cookie_hash):
    global ng_quang_huy_cookie_attempts
    current_time = time.time()
    if current_time - ng_quang_huy_cookie_attempts[cookie_hash]['last_reset'] > 43200:
        ng_quang_huy_cookie_attempts[cookie_hash]['count'] = 0
        ng_quang_huy_cookie_attempts[cookie_hash]['last_reset'] = current_time
        ng_quang_huy_cookie_attempts[cookie_hash]['banned_until'] = 0
    if ng_quang_huy_cookie_attempts[cookie_hash]['banned_until'] > 0:
        ban_count = getattr(ng_quang_huy_cookie_attempts[cookie_hash], 'ban_count', 0) + 1
        ng_quang_huy_cookie_attempts[cookie_hash]['ban_count'] = ban_count
        if ban_count >= 5:
            ng_quang_huy_cookie_attempts[cookie_hash]['permanent_ban'] = True
            print(f"Cookie {cookie_hash[:10]} bị cấm vĩnh viễn")
            for key in list(ng_quang_huy_active_threads.keys()):
                if key.startswith(cookie_hash):
                    ng_quang_huy_active_threads[key].ng_quang_huy_stop()
                    del ng_quang_huy_active_threads[key]

def ng_quang_huy_generate_offline_threading_id():
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))

def ng_quang_huy_json_minimal(data):
    return json.dumps(data, separators=(",", ":"))

class ng_quang_huy_TreoMQTTSender:
    def __init__(self, dataFB):
        self.dataFB = dataFB
        self.mqtt = None
        self.ws_req_number = 0
        self.syncToken = None
        self.lastSeqID = dataFB.get("lastSeqID", "0")
        self.req_callbacks = {}
        self.cookie_hash = hashlib.md5(dataFB['cookieFacebook'].encode()).hexdigest()
        self.last_cleanup = time.time()
        self.success_count = 0

    def ng_quang_huy_cleanup_memory(self):
        current_time = time.time()
        if current_time - self.last_cleanup > 3600:
            self.req_callbacks.clear()
            self.last_cleanup = current_time

    def ng_quang_huy_on_disconnect(self, client, userdata, rc):
        global ng_quang_huy_cookie_attempts
        ng_quang_huy_cookie_attempts[self.cookie_hash]['count'] += 1
        current_time = time.time()
        if current_time - ng_quang_huy_cookie_attempts[self.cookie_hash]['last_reset'] > 43200:
            ng_quang_huy_cookie_attempts[self.cookie_hash]['count'] = 1
            ng_quang_huy_cookie_attempts[self.cookie_hash]['last_reset'] = current_time
        if ng_quang_huy_cookie_attempts[self.cookie_hash]['count'] >= 20:
            ng_quang_huy_cookie_attempts[self.cookie_hash]['banned_until'] = current_time + 43200
            return
        if rc != 0:
            try:
                time.sleep(min(ng_quang_huy_cookie_attempts[self.cookie_hash]['count'] * 2, 30))
                client.reconnect()
            except:
                pass

    def ng_quang_huy_messenger_queue_publish(self, client, userdata, flags, rc):
        if rc != 0:
            return
        topics = [("/t_ms", 0)]
        client.subscribe(topics)
        queue = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self.dataFB['FacebookID']
        }
        if self.syncToken is None:
            topic = "/messenger_sync_create_queue"
            queue["initial_titan_sequence_id"] = self.lastSeqID
            queue["device_params"] = None
        else:
            topic = "/messenger_sync_get_diffs"
            queue["last_seq_id"] = self.lastSeqID
            queue["sync_token"] = self.syncToken
        client.publish(
            topic,
            ng_quang_huy_json_minimal(queue),
            qos=1,
            retain=False,
        )

    def ng_quang_huy_mqtt_connect(self):
        global ng_quang_huy_cookie_attempts
        if ng_quang_huy_cookie_attempts[self.cookie_hash]['permanent_ban']:
            return False
        current_time = time.time()
        if current_time < ng_quang_huy_cookie_attempts[self.cookie_hash]['banned_until']:
            return False
        session_id = random.randint(1, 2 ** 53)
        user = {
            "u": self.dataFB["FacebookID"],
            "s": session_id,
            "chat_on": ng_quang_huy_json_minimal(True),
            "fg": False,
            "d": ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '-' +
                 ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' +
                 ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' +
                 ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' +
                 ''.join(random.choices(string.ascii_lowercase + string.digits, k=12)),
            "ct": "websocket",
            "aid": 219994525426954,
            "mqtt_sid": "",
            "cp": 3,
            "ecp": 10,
            "st": ["/t_ms", "/messenger_sync_get_diffs", "/messenger_sync_create_queue"],
            "pm": [],
            "dc": "",
            "no_auto_fg": True,
            "gas": None,
            "pack": [],
        }
        host = f"wss://edge-chat.messenger.com/chat?region=eag&sid={session_id}"
        options = {
            "client_id": "mqttwsclient",
            "username": ng_quang_huy_json_minimal(user),
            "clean": True,
            "ws_options": {
                "headers": {
                    "Cookie": self.dataFB['cookieFacebook'],
                    "Origin": "https://www.messenger.com",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
                    "Referer": "https://www.messenger.com/",
                    "Host": "edge-chat.messenger.com",
                },
            },
            "keepalive": 10,
        }
        self.mqtt = mqtt.Client(
            client_id="mqttwsclient",
            clean_session=True,
            protocol=mqtt.MQTTv31,
            transport="websockets",
        )
        self.mqtt.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.mqtt.on_connect = self.ng_quang_huy_messenger_queue_publish
        self.mqtt.on_disconnect = self.ng_quang_huy_on_disconnect
        self.mqtt.username_pw_set(username=options["username"])
        parsed_host = urlparse(host)
        self.mqtt.ws_set_options(
            path=f"{parsed_host.path}?{parsed_host.query}",
            headers=options["ws_options"]["headers"],
        )
        try:
            self.mqtt.connect(
                host=options["ws_options"]["headers"]["Host"],
                port=443,
                keepalive=options["keepalive"],
            )
            self.mqtt.loop_start()
            return True
        except Exception as e:
            ng_quang_huy_cookie_attempts[self.cookie_hash]['count'] += 1
            return False

    def ng_quang_huy_stop(self):
        if self.mqtt:
            try:
                self.mqtt.disconnect()
                self.mqtt.loop_stop()
            except:
                pass
        self.ng_quang_huy_cleanup_memory()

    def ng_quang_huy_mqtt_send_message(self, message, thread_id):
        if self.mqtt is None:
            return False
        if not all([message, thread_id]):
            return False
        self.ng_quang_huy_cleanup_memory()
        self.ws_req_number += 1
        task_payload = {
            "thread_id": thread_id,
            "otid": ng_quang_huy_generate_offline_threading_id(),
            "source": 0,
            "send_type": 1,
            "text": message,
            "initiating_source": 1
        }
        content = {
            "app_id": "2220391788200892",
            "payload": {
                "tasks": [{
                    "label": 46,
                    "payload": json.dumps(task_payload, separators=(",", ":")),
                    "queue_name": "send_message",
                    "task_id": self.ws_req_number,
                    "failure_count": None,
                }],
                "epoch_id": ng_quang_huy_generate_offline_threading_id(),
                "version_id": "7214102258676893",
            },
            "request_id": self.ws_req_number,
            "type": 3
        }
        content["payload"] = json.dumps(content["payload"], separators=(",", ":"))
        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            self.success_count += 1
            return True
        except Exception as e:
            return False

class ng_quang_huy_TreoFacebookAuth:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.ng_quang_huy_id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.ng_quang_huy_init_params()

    def ng_quang_huy_id_user(self):
        try:
            match = re.search(r"c_user=(\d+)", self.cookie)
            if not match:
                raise Exception("Cookie không hợp lệ")
            return match.group(1)
        except Exception as e:
            raise Exception(f"Lỗi khi lấy user_id: {str(e)}")

    def ng_quang_huy_init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        urls = [
            'https://www.facebook.com',
            'https://mbasic.facebook.com',
            'https://m.facebook.com'
        ]
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                fb_dtsg_patterns = [
                    r'"token":"(.*?)"',
                    r'name="fb_dtsg" value="(.*?)"',
                    r'"fb_dtsg":"(.*?)"',
                    r'fb_dtsg=([^&"]+)'
                ]
                jazoest_pattern = r'name="jazoest" value="(\d+)"'
                rev_pattern = r'"__rev":"(\d+)"'
                fb_dtsg = None
                for pattern in fb_dtsg_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        fb_dtsg = match.group(1)
                        break
                jazoest_match = re.search(jazoest_pattern, response.text)
                rev_match = re.search(rev_pattern, response.text)
                if fb_dtsg:
                    self.fb_dtsg = fb_dtsg
                    self.jazoest = jazoest_match.group(1) if jazoest_match else "22036"
                    self.rev = rev_match.group(1) if rev_match else "1015919737"
                    return
            except Exception as e:
                time.sleep(2)
        raise Exception("Không thể lấy fb_dtsg từ bất kỳ URL nào")

def ng_quang_huy_send_messages_with_cookie(cookie, thread_ids, contents, delay):
    global ng_quang_huy_cookie_attempts, ng_quang_huy_active_threads
    cookie_hash = hashlib.md5(cookie.encode()).hexdigest()
    if ng_quang_huy_cookie_attempts[cookie_hash]['permanent_ban']:
        print(f"Cookie {cookie_hash[:10]} bị cấm vĩnh viễn")
        return False
    current_time = time.time()
    if current_time < ng_quang_huy_cookie_attempts[cookie_hash]['banned_until']:
        print(f"Cookie {cookie_hash[:10]} bị cấm tạm thời")
        return False
    try:
        fb = ng_quang_huy_TreoFacebookAuth(cookie)
        sender = ng_quang_huy_TreoMQTTSender({
            "FacebookID": fb.user_id,
            "fb_dtsg": fb.fb_dtsg,
            "clientRevision": fb.rev,
            "jazoest": fb.jazoest,
            "cookieFacebook": cookie,
            "lastSeqID": "0"
        })
        if not sender.ng_quang_huy_mqtt_connect():
            ng_quang_huy_handle_failed_connection(cookie_hash)
            print(f"Kết nối thất bại với cookie {cookie_hash[:10]}")
            return False
        for thread_id in thread_ids:
            ng_quang_huy_active_threads[f"{cookie_hash}_{thread_id}"] = sender
        try:
            while True:
                for thread_id in thread_ids:
                    for content in contents:
                        if sender.ng_quang_huy_mqtt_send_message(content, thread_id):
                            print(f"[DZIXNANH] ĐÃ TREO NGÔN TỚI NHÓM {thread_id} THÀNH CÔNG")
                        else:
                            print(f"TREO NGÔN THẤT BẠI TỚI NHÓM {thread_id} VỚI COOKIE {cookie_hash[:10]}")
                        time.sleep(delay)
        except KeyboardInterrupt:
            print("Dừng tool")
        finally:
            sender.ng_quang_huy_stop()
            for thread_id in thread_ids:
                if f"{cookie_hash}_{thread_id}" in ng_quang_huy_active_threads:
                    del ng_quang_huy_active_threads[f"{cookie_hash}_{thread_id}"]
        return True
    except Exception as e:
        ng_quang_huy_handle_failed_connection(cookie_hash)
        print(f"Lỗi với cookie {cookie_hash[:10]}: {str(e)}")
        return False

def ng_quang_huy_read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {str(e)}")
        return []

def ng_quang_huy_main():
    cookie_file = input("Nhập đường dẫn file cookie (.txt): ")
    cookies = ng_quang_huy_read_file(cookie_file)
    if not cookies:
        print("Không tìm thấy cookie hợp lệ")
        return
    thread_ids = input("Nhập danh sách ID box (cách nhau bởi dấu phẩy): ").split(',')
    thread_ids = [tid.strip() for tid in thread_ids if tid.strip()]
    if not thread_ids:
        print("Không có ID box hợp lệ")
        return
    content_file = input("Nhập đường dẫn file nội dung (.txt): ")
    contents = ng_quang_huy_read_file(content_file)
    if not contents:
        print("Không tìm thấy nội dung hợp lệ")
        return
    try:
        delay = float(input("Nhập thời gian delay giữa các tin nhắn (giây): "))
    except ValueError:
        print("Delay không hợp lệ, sử dụng mặc định 5 giây")
        delay = 5
    threads = []
    cookie_index = 0
    while True:
        try:
            for i in range(len(cookies)):
                cookie = cookies[cookie_index]
                t = threading.Thread(target=ng_quang_huy_send_messages_with_cookie, args=(cookie, thread_ids, contents, delay))
                t.start()
                threads.append(t)
                cookie_index = (cookie_index + 1) % len(cookies)
                time.sleep(1)
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            print("Dừng tool treo")
            break

if __name__ == "__main__":
    ng_quang_huy_main()
    