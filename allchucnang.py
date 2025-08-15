"use strict";

import os
import sys
import time
import ssl
import json
import random
import string
import hashlib
import threading
import re
from collections import defaultdict
from urllib.parse import urlparse, urlencode
from datetime import datetime
import requests
import psutil
import gc
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt

cookie_attempts = defaultdict(lambda: {'count': 0, 'last_reset': time.time(), 'banned_until': 0, 'permanent_ban': False})
cookie_delays = {}
active_threads = {}
cleanup_lock = threading.Lock()

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def handle_failed_connection(cookie_hash):
    global cookie_attempts
    
    current_time = time.time()
    
    if current_time - cookie_attempts[cookie_hash]['last_reset'] > 43200:
        cookie_attempts[cookie_hash]['count'] = 0
        cookie_attempts[cookie_hash]['last_reset'] = current_time
        cookie_attempts[cookie_hash]['banned_until'] = 0
    
    if cookie_attempts[cookie_hash]['banned_until'] > 0:
        ban_count = getattr(cookie_attempts[cookie_hash], 'ban_count', 0) + 1
        cookie_attempts[cookie_hash]['ban_count'] = ban_count
        
        if ban_count >= 5:
            cookie_attempts[cookie_hash]['permanent_ban'] = True
            print(f"Cookie {cookie_hash[:10]} Đã Bị Ngưng Hoạt Động Vĩnh Viễn Để Tránh Đầy Memory, Lí Do: Acc Die, CheckPoint v.v")
            
            for key in list(active_threads.keys()):
                if key.startswith(cookie_hash):
                    active_threads[key].stop()
                    del active_threads[key]

def cleanup_global_memory():
    global active_threads, cookie_attempts
    
    with cleanup_lock:
        current_time = time.time()
        
        expired_cookies = []
        for cookie_hash, data in cookie_attempts.items():
            if data['permanent_ban'] or (current_time - data['last_reset'] > 86400):
                expired_cookies.append(cookie_hash)
        
        for cookie_hash in expired_cookies:
            del cookie_attempts[cookie_hash]
            for key in list(active_threads.keys()):
                if key.startswith(cookie_hash):
                    active_threads[key].stop()
                    del active_threads[key]
        
        gc.collect()
        
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"Memory Usage: {memory_info.rss / (1024**3):.2f} GB")

def parse_cookie_string(cookie_string):
    cookie_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        if "=" in cookie:
            key, value = cookie.strip().split("=", 1)
            cookie_dict[key] = value
    return cookie_dict

def generate_offline_threading_id() -> str:
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))

def get_headers(url: str, options: dict = {}, ctx: dict = {}, customHeader: dict = {}) -> dict:
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.facebook.com/",
        "Host": urlparse(url).netloc,
        "Origin": "https://www.facebook.com",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
        "Connection": "keep-alive",
    }

    if "user_agent" in options:
        headers["User-Agent"] = options["user_agent"]

    for key in customHeader:
        headers[key] = customHeader[key]

    if "region" in ctx:
        headers["X-MSGR-Region"] = ctx["region"]

    return headers

def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))

class Counter:
    def __init__(self, initial_value=0):
        self.value = initial_value
        
    def increment(self):
        self.value += 1
        return self.value
        
    @property
    def counter(self):
        return self.value

def formAll(dataFB, FBApiReqFriendlyName=None, docID=None, requireGraphql=None):
    global _req_counter
    if '_req_counter' not in globals():
        _req_counter = Counter(0)
    
    __reg = _req_counter.increment()
    dataForm = {}
    
    if requireGraphql is None:
        dataForm["fb_dtsg"] = dataFB["fb_dtsg"]
        dataForm["jazoest"] = dataFB["jazoest"]
        dataForm["__a"] = 1
        dataForm["__user"] = str(dataFB["FacebookID"])
        dataForm["__req"] = str_base(__reg, 36) 
        dataForm["__rev"] = dataFB["clientRevision"]
        dataForm["av"] = dataFB["FacebookID"]
        dataForm["fb_api_caller_class"] = "RelayModern"
        dataForm["fb_api_req_friendly_name"] = FBApiReqFriendlyName
        dataForm["server_timestamps"] = "true"
        dataForm["doc_id"] = str(docID)
    else:
        dataForm["fb_dtsg"] = dataFB["fb_dtsg"]
        dataForm["jazoest"] = dataFB["jazoest"]
        dataForm["__a"] = 1
        dataForm["__user"] = str(dataFB["FacebookID"])
        dataForm["__req"] = str_base(__reg, 36) 
        dataForm["__rev"] = dataFB["clientRevision"]
        dataForm["av"] = dataFB["FacebookID"]

    return dataForm

def mainRequests(url, data, cookies):
    return {
        "url": url,
        "data": data,
        "headers": {
            "authority": "www.facebook.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,vi;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": "https://www.facebook.com/",
            "sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "x-fb-friendly-name": "FriendingCometFriendRequestsRootQueryRelayPreloader",
            "x-fb-lsd": "YCb7tYCGWDI6JLU5Aexa1-"
        },
        "cookies": parse_cookie_string(cookies),
        "verify": True
    }

def digitToChar(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number, base):
    if number < 0:
        return "-" + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digitToChar(m)
    return digitToChar(m)

def generate_session_id():
    return random.randint(1, 2 ** 53)

def generate_client_id():
    def gen(length):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return gen(8) + '-' + gen(4) + '-' + gen(4) + '-' + gen(4) + '-' + gen(12)

# Hàm mới: Lấy danh sách bạn bè
def get_friends_list(dataFB):
    """Lấy danh sách bạn bè của tài khoản bằng endpoint chat/user_info_all."""
    try:
        form = {
            "viewer": str(dataFB["FacebookID"]),
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }

        headers = get_headers("https://www.facebook.com/chat/user_info_all", customHeader={
            "Content-Type": "application/x-www-form-urlencoded"
        })

        response = requests.post(
            "https://www.facebook.com/chat/user_info_all",
            data=form,
            headers=headers,
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")

        content = response.text.replace('for (;;);', '')
        data = json.loads(content)

        if not data or "payload" not in data:
            raise Exception("getFriendsList returned empty object or missing payload.")

        if "error" in data:
            raise Exception(f"API Error: {data.get('errorDescription', 'Unknown error')}")

        # Format the friend list
        friends = data["payload"]
        friend_ids = [str(user_id) for user_id in friends.keys()]
        return True, friend_ids, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Lấy được {len(friend_ids)} bạn bè."
    except Exception as e:
        return False, [], f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi khi lấy danh sách bạn bè: {str(e)}"

# Hàm mới: Đổi tên nhóm và thêm bạn bè
def change_group_name_and_add_friends(dataFB, thread_id, group_name):
    try:
        # Đổi tên nhóm
        success, log = tenbox(group_name, thread_id, dataFB)
        if not success:
            return False, log

        # Lấy danh sách bạn bè
        success, friend_ids, log = get_friends_list(dataFB)
        if not success:
            return False, log
        print(log)

        # Thêm bạn bè vào nhóm (giới hạn mỗi lần 10 bạn, delay 5 giây)
        batch_size = 50  # Reduced batch size
        for i in range(0, len(friend_ids), batch_size):
            batch = friend_ids[i:i + batch_size]
            success, log = add_user_to_group(dataFB, batch, thread_id)
            if not success:
                return False, log
            print(log)
            time.sleep(5)  # Increased delay
        return True, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã đổi tên nhóm thành {group_name} và thêm {len(friend_ids)} bạn bè vào nhóm {thread_id}"
    except Exception as e:
        return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi: {str(e)}"

# Hàm hiện có: Đổi tên nhóm
def tenbox(newTitle, threadID, dataFB):
    try:
        message_id = generate_offline_threading_id()
        timestamp = int(time.time() * 1000)
        form_data = {
            "client": "mercury",
            "action_type": "ma-type:log-message",
            "author": f"fbid:{dataFB['FacebookID']}",
            "thread_id": str(threadID),
            "timestamp": timestamp,
            "timestamp_relative": str(int(time.time())),
            "source": "source:chat:web",
            "source_tags[0]": "source:chat",
            "offline_threading_id": message_id,
            "message_id": message_id,
            "threading_id": generate_offline_threading_id(),
            "thread_fbid": str(threadID),
            "thread_name": str(newTitle),
            "log_message_type": "log:thread-name",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }

        response = requests.post(
            "https://www.facebook.com/messaging/set_thread_name/",
            data=form_data,
            headers=get_headers("https://www.facebook.com", customHeader={"Content-Length": str(len(form_data))}),
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )

        if response.status_code == 200:
            return True, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã đổi tên thành: {newTitle}"
        else:
            return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi HTTP {response.status_code} khi đổi tên."
    except Exception as e:
        return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}"

def change_nickname(nickname, thread_id, participant_id, dataFB):
    try:
        form = {
            "nickname": nickname,
            "participant_id": str(participant_id),
            "thread_or_other_fbid": str(thread_id),
            "source": "thread_settings",
            "dpr": "1",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": str_base(Counter().increment(), 36),
            "__rev": dataFB.get("clientRevision", "1015919737")
        }

        headers = get_headers("https://www.facebook.com/messaging/save_thread_nickname/", customHeader={
            "Content-Type": "application/x-www-form-urlencoded"
        })

        response = requests.post(
            "https://www.facebook.com/messaging/save_thread_nickname/",
            data=form,
            headers=headers,
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")

        content = response.text.replace('for (;;);', '')
        data = json.loads(content)

        if "error" in data:
            error_code = data.get("error")
            if error_code == 1545014:
                raise Exception("Trying to change nickname of user who isn't in thread")
            if error_code == 1357031:
                raise Exception("Thread doesn't exist or has no messages")
            raise Exception(f"API Error: {data.get('errorDescription', 'Unknown error')}")

        return True, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã đổi biệt danh cho user {participant_id} thành {nickname} trong box {thread_id}"
    except Exception as e:
        return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi khi đổi biệt danh cho user {participant_id}: {str(e)}"
        
def get_thread_info_graphql(thread_id, dataFB):
    try:
        form = {
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3449967031715030",
                    "query_params": {
                        "id": str(thread_id),
                        "message_limit": 0,
                        "load_messages": False,
                        "load_read_receipts": False,
                        "before": None
                    }
                }
            }, separators=(",", ":")),
            "batch_name": "MessengerGraphQLThreadFetcher",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": str_base(Counter().increment(), 36),
            "__rev": dataFB.get("clientRevision", "1015919737")
        }

        headers = get_headers("https://www.facebook.com/api/graphqlbatch/", customHeader={
            "Content-Type": "application/x-www-form-urlencoded"
        })

        response = requests.post(
            "https://www.facebook.com/api/graphqlbatch/",
            data=form,
            headers=headers,
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")

        content = response.text.replace('for (;;);', '')
        response_parts = content.split("\n")
        if not response_parts or not response_parts[0].strip():
            raise Exception("Empty response from API")

        data = json.loads(response_parts[0])

        if "error" in data:
            raise Exception(f"API Error: {data.get('errorDescription', 'Unknown error')}")

        if data.get("error_results", 0) != 0:
            raise Exception("Error results in response")

        message_thread = data["o0"]["data"]["message_thread"]
        thread_id = (message_thread["thread_key"]["thread_fbid"] 
                     if message_thread["thread_key"].get("thread_fbid") 
                     else message_thread["thread_key"]["other_user_id"])

        participant_ids = [edge["node"]["messaging_actor"]["id"] 
                          for edge in message_thread["all_participants"]["edges"]]

        return True, participant_ids, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Lấy được {len(participant_ids)} thành viên trong box {thread_id}"
    except Exception as e:
        return False, [], f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi khi lấy thông tin box {thread_id}: {str(e)}"

# Hàm hiện có: Tạo nhóm mới
def create_new_group(dataFB, participant_ids, group_title):
    """Create a new Facebook group with the given participants and title."""
    try:
        if not isinstance(participant_ids, list):
            raise ValueError("participant_ids should be an array.")
        
        if len(participant_ids) < 2:
            raise ValueError("participant_ids should have at least 2 IDs.")

        pids = [{"fbid": str(pid)} for pid in participant_ids]
        pids.append({"fbid": str(dataFB["FacebookID"])})

        form = {
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "MessengerGroupCreateMutation",
            "av": str(dataFB["FacebookID"]),
            "doc_id": "577041672419534",
            "variables": json.dumps({
                "input": {
                    "entry_point": "jewel_new_group",
                    "actor_id": str(dataFB["FacebookID"]),
                    "participants": pids,
                    "client_mutation_id": str(random.randint(1, 1024)),
                    "thread_settings": {
                        "name": group_title,
                        "joinable_mode": "PRIVATE",
                        "thread_image_fbid": None
                    }
                }
            }, separators=(",", ":")),
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }

        headers = get_headers("https://www.facebook.com/api/graphql/", customHeader={
            "Content-Type": "application/x-www-form-urlencoded"
        })

        response = requests.post(
            "https://www.facebook.com/api/graphql/",
            data=form,
            headers=headers,
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")

        content = response.text.replace('for (;;);', '')
        data = json.loads(content)

        if "errors" in data:
            raise Exception(f"API Error: {data['errors'][0]['message']}")

        thread_id = data["data"]["messenger_group_thread_create"]["thread"]["thread_key"]["thread_fbid"]
        return True, thread_id, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã tạo nhóm: {group_title} (ID: {thread_id})"
    except Exception as e:
        return False, None, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi khi tạo nhóm {group_title}: {str(e)}"

# Hàm hiện có: Thêm người dùng vào nhóm
def add_user_to_group(dataFB, user_ids, thread_id, max_retries=3):
    """Add users to an existing Facebook group with retry logic."""
    for attempt in range(max_retries):
        try:
            if not isinstance(user_ids, list):
                user_ids = [user_ids]

            # Validate user IDs and thread ID
            for user_id in user_ids:
                if not isinstance(user_id, (str, int)) or not str(user_id).isdigit():
                    raise ValueError(f"Invalid user_id: {user_id}. Must be a number or string of digits.")
            if not isinstance(thread_id, (str, int)) or not str(thread_id).isdigit():
                raise ValueError(f"Invalid thread_id: {thread_id}. Must be a number or string of digits.")

            message_and_otid = generate_offline_threading_id()
            form = {
                "client": "mercury",
                "action_type": "ma-type:log-message",
                "author": f"fbid:{dataFB['FacebookID']}",
                "thread_id": "",
                "timestamp": str(int(time.time() * 1000)),
                "timestamp_absolute": "Today",
                "timestamp_relative": generateTimestampRelative(),
                "timestamp_time_passed": "0",
                "is_unread": "false",
                "is_cleared": "false",
                "is_forward": "false",
                "is_filtered_content": "false",
                "is_filtered_content_bh": "false",
                "is_filtered_content_account": "false",
                "is_spoof_warning": "false",
                "source": "source:chat:web",
                "source_tags[0]": "source:chat",
                "log_message_type": "log:subscribe",
                "status": "0",
                "offline_threading_id": message_and_otid,
                "message_id": message_and_otid,
                "threading_id": f"<{int(time.time() * 1000)}:{message_and_otid}>",
                "manual_retry_cnt": "0",
                "thread_fbid": str(thread_id),
                "fb_dtsg": dataFB["fb_dtsg"],
                "jazoest": dataFB["jazoest"],
                "__user": str(dataFB["FacebookID"]),
                "__a": "1",
                "__req": str_base(Counter().increment(), 36),
                "__rev": dataFB.get("clientRevision", "1015919737")
            }

            for i, user_id in enumerate(user_ids):
                form[f"log_message_data[added_participants][{i}]"] = f"fbid:{user_id}"

            headers = get_headers("https://www.facebook.com/messaging/send/", customHeader={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-FB-LSD": dataFB.get("lsd", "YCb7tYCGWDI6JLU5Aexa1-"),
                "Content-Length": str(len(urlencode(form)))
            })

            print(f"[DEBUG] Attempt {attempt + 1}/{max_retries}: Adding {len(user_ids)} users to thread {thread_id}")

            response = requests.post(
                "https://www.facebook.com/messaging/send/",
                data=form,
                headers=headers,
                cookies=parse_cookie_string(dataFB["cookieFacebook"]),
                timeout=15
            )

            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text[:100]}")

            content = response.text.replace('for (;;);', '')
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise Exception(f"JSON Decode Error: {e}. Response: {content[:100]}")

            if "error" in data:
                error_msg = data.get('errorDescription', 'Unknown error')
                error_code = data.get('error', 'No error code')
                if error_code == 1545052 and attempt < max_retries - 1:
                    print(f"[WARNING] API Error 1545052 on attempt {attempt + 1}. Retrying after 10 seconds...")
                    time.sleep(10)
                    continue
                raise Exception(f"API Error {error_code}: {error_msg}")

            return True, f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã thêm {len(user_ids)} người vào nhóm {thread_id}"

        except Exception as e:
            error_msg = f"❌ [{datetime.now().strftime('%H:%M:%S')}] Lỗi khi thêm người vào nhóm {thread_id}: {str(e)}"
            print(error_msg)
            if 'response' in locals():
                with open('error_response.json', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("[DEBUG] Saved error response to error_response.json")
            if attempt == max_retries - 1:
                return False, error_msg
            time.sleep(10)  # Wait before retrying
    return False, f"❌ [{datetime.now().strftime('%H:%M:%S')}] Failed after {max_retries} attempts"

# Hàm hiện có: Đọc cookie từ file
def read_cookies_from_file(file_path):
    """Read cookies from a file, one cookie per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies = [line.strip() for line in f if line.strip()]
        if not cookies:
            raise ValueError("File cookie rỗng hoặc không có cookie hợp lệ.")
        return cookies
    except FileNotFoundError:
        raise FileNotFoundError(f"File không tồn tại: {file_path}")
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file cookie: {str(e)}")

# Hàm hiện có: Tạo timestamp tương đối
def generateTimestampRelative():
    current_time = datetime.now()
    hours_ago = (datetime.now() - datetime.now()).seconds // 3600
    if hours_ago == 0:
        return "Just now"
    elif hours_ago == 1:
        return "1 hour ago"
    else:
        return f"{hours_ago} hours ago"

# Lớp fbTools (giả định đã có từ mã gốc)
class fbTools:
    def __init__(self, dataFB, threadID="0"):
        self.threadID = threadID
        self.dataGet = None
        self.dataFB = dataFB
        self.ProcessingTime = None
        self.last_seq_id = None
    
    def getAllThreadList(self):
        randomNumber = str(int(format(int(time.time() * 1000), "b") + ("0000000000000000000000" + format(int(random.random() * 4294967295), "b"))[-22:], 2))
        dataForm = formAll(self.dataFB, requireGraphql=0)

        dataForm["queries"] = json.dumps({
            "o0": {
                "doc_id": "3336396659757871",
                "query_params": {
                    "limit": 20,
                    "before": None,
                    "tags": ["INBOX"],
                    "includeDeliveryReceipts": False,
                    "includeSeqID": True,
                }
            }
        })
        
        sendRequests = requests.post(**mainRequests("https://www.facebook.com/api/graphqlbatch/", dataForm, self.dataFB["cookieFacebook"]))
        response_text = sendRequests.text
        self.ProcessingTime = sendRequests.elapsed.total_seconds()
        
        if response_text.startswith("for(;;);"):
            response_text = response_text[9:]
        
        if not response_text.strip():
            print("Error: Empty response from Facebook API")
            return False
            
        try:
            response_parts = response_text.split("\n")
            first_part = response_parts[0]
            
            if first_part.strip():
                response_data = json.loads(first_part)
                self.dataGet = first_part
                
                if "o0" in response_data and "data" in response_data["o0"] and "viewer" in response_data["o0"]["data"] and "message_threads" in response_data["o0"]["data"]["viewer"]:
                    self.last_seq_id = response_data["o0"]["data"]["viewer"]["message_threads"]["sync_sequence_id"]
                    return True
                else:
                    print("Error: Expected fields not found in response")
                    return False
            else:
                print("Error: Empty first part of response")
                return False
                
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Response first part: {response_parts[0][:100]}")
            return False
        except KeyError as e:
            print(f"Key Error: {e}")
            print("The expected data structure wasn't found in the response")
            return False

# Lớp MessageSender (giả định đã có từ mã gốc)
class MessageSender:
    def __init__(self, fbt, dataFB, fb_instance):
        self.fbt = fbt
        self.dataFB = dataFB
        self.fb_instance = fb_instance
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.syncToken = None
        self.lastSeqID = None
        self.req_callbacks = {}
        self.cookie_hash = hashlib.md5(dataFB['cookieFacebook'].encode()).hexdigest()
        self.connect_attempts = 0
        self.last_cleanup = time.time()

        # Danh sách theme (tương tự như trong JavaScript)
    THEMES = [
        {"id": "3650637715209675", "name": "Besties"},
        {"id": "769656934577391", "name": "Women's History Month"},
        {"id": "702099018755409", "name": "Dune: Part Two"},
        {"id": "1480404512543552", "name": "Avatar: The Last Airbender"},
        {"id": "952656233130616", "name": "J.Lo"},
        {"id": "741311439775765", "name": "Love"},
        {"id": "215565958307259", "name": "Bob Marley: One Love"},
        {"id": "194982117007866", "name": "Football"},
        {"id": "1743641112805218", "name": "Soccer"},
        {"id": "730357905262632", "name": "Mean Girls"},
        {"id": "1270466356981452", "name": "Wonka"},
        {"id": "704702021720552", "name": "Pizza"},
        {"id": "1013083536414851", "name": "Wish"},
        {"id": "359537246600743", "name": "Trolls"},
        {"id": "173976782455615", "name": "The Marvels"},
        {"id": "2317258455139234", "name": "One Piece"},
        {"id": "6685081604943977", "name": "1989"},
        {"id": "1508524016651271", "name": "Avocado"},
        {"id": "265997946276694", "name": "Loki Season 2"},
        {"id": "6584393768293861", "name": "olivia rodrigo"},
        {"id": "845097890371902", "name": "Baseball"},
        {"id": "292955489929680", "name": "Lollipop"},
        {"id": "976389323536938", "name": "Loops"},
        {"id": "810978360551741", "name": "Parenthood"},
        {"id": "195296273246380", "name": "Bubble Tea"},
        {"id": "6026716157422736", "name": "Basketball"},
        {"id": "693996545771691", "name": "Elephants & Flowers"},
        {"id": "390127158985345", "name": "Chill"},
        {"id": "365557122117011", "name": "Support"},
        {"id": "339021464972092", "name": "Music"},
        {"id": "1060619084701625", "name": "Lo-Fi"},
        {"id": "3190514984517598", "name": "Sky"},
        {"id": "627144732056021", "name": "Celebration"},
        {"id": "275041734441112", "name": "Care"},
        {"id": "3082966625307060", "name": "Astrology"},
        {"id": "539927563794799", "name": "Cottagecore"},
        {"id": "527564631955494", "name": "Ocean"},
        {"id": "230032715012014", "name": "Tie-Dye"},
        {"id": "788274591712841", "name": "Monochrome"},
        {"id": "3259963564026002", "name": "Default"},
        {"id": "724096885023603", "name": "Berry"},
        {"id": "624266884847972", "name": "Candy"},
        {"id": "273728810607574", "name": "Unicorn"},
        {"id": "262191918210707", "name": "Tropical"},
        {"id": "2533652183614000", "name": "Maple"},
        {"id": "909695489504566", "name": "Sushi"},
        {"id": "582065306070020", "name": "Rocket"},
        {"id": "557344741607350", "name": "Citrus"},
        {"id": "280333826736184", "name": "Lollipop"},
        {"id": "271607034185782", "name": "Shadow"},
        {"id": "1257453361255152", "name": "Rose"},
        {"id": "571193503540759", "name": "Lavender"},
        {"id": "2873642949430623", "name": "Tulip"},
        {"id": "3273938616164733", "name": "Classic"},
        {"id": "403422283881973", "name": "Apple"},
        {"id": "3022526817824329", "name": "Peach"},
        {"id": "672058580051520", "name": "Honey"},
        {"id": "3151463484918004", "name": "Kiwi"},
        {"id": "736591620215564", "name": "Ocean"},
        {"id": "193497045377796", "name": "Grape"},
    ]

    def set_theme(self, theme_id, thread_id, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        self.ws_task_number += 1

        # Nếu không cung cấp theme_id, chọn ngẫu nhiên một theme
        if not theme_id:
            selected_theme = random.choice(self.THEMES)
            theme_id = selected_theme["id"]
            theme_name = selected_theme["name"]
        else:
            # Kiểm tra theme_id hợp lệ
            selected_theme = next((theme for theme in self.THEMES if theme["id"] == theme_id), None)
            if not selected_theme:
                print(f"Error: Theme ID {theme_id} not found in available themes")
                return False
            theme_name = selected_theme["name"]

        task_payload = {
            "thread_key": thread_id,
            "theme_fbid": theme_id,
            "source": None,
            "sync_group": 1,
            "payload": None,
        }

        task = {
            "failure_count": None,
            "label": "43",
            "payload": json.dumps(task_payload, separators=(",", ":")),
            "queue_name": "thread_theme",
            "task_id": self.ws_task_number,
        }

        content = {
            "app_id": "2220391788200892",
            "payload": json.dumps({
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [task],
                "version_id": "25095469420099952",
            }, separators=(",", ":")),
            "request_id": self.ws_req_number,
            "type": 3,
        }

        if callback is not None and callable(callback):
            self.req_callbacks[self.ws_req_number] = callback

        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            print(f"[✓] Đã thay đổi theme thành: {theme_name} (ID: {theme_id}) cho box {thread_id}")
            return True
        except Exception as e:
            print(f"Error Publishing Theme Change: {e}")
            return False
        
    def cleanup_memory(self):
        current_time = time.time()
        if current_time - self.last_cleanup > 3600:
            self.req_callbacks.clear()
            gc.collect()
            self.last_cleanup = current_time

    def get_last_seq_id(self):
        success = self.fbt.getAllThreadList()
        if success:
            self.lastSeqID = self.fbt.last_seq_id
        else:
            print("Failed To Get Last Sequence ID. Check Facebook Authentication.")
            return

    def on_disconnect(self, client, userdata, rc):
        global cookie_attempts
        print(f"Disconnected With Code {rc}")
        
        cookie_attempts[self.cookie_hash]['count'] += 1
        current_time = time.time()
        
        if current_time - cookie_attempts[self.cookie_hash]['last_reset'] > 43200:
            cookie_attempts[self.cookie_hash]['count'] = 1
            cookie_attempts[self.cookie_hash]['last_reset'] = current_time
        
        if cookie_attempts[self.cookie_hash]['count'] >= 20:
            print(f"Cookie {self.cookie_hash[:10]} Bị Tạm Ngưng Connect Trong 12 Giờ Vì Disconnect, Nghi Vấn: Die Cookies, Check Point")
            cookie_attempts[self.cookie_hash]['banned_until'] = current_time + 43200
            return
        
        if rc != 0:
            print("Attempting To Reconnect...")
            try:
                time.sleep(min(cookie_attempts[self.cookie_hash]['count'] * 2, 30))
                client.reconnect()
            except:
                print("Reconnect Failed")

    def _messenger_queue_publish(self, client, userdata, flags, rc):
        print(f"Connected To MQTT With Code: {rc}")
        if rc != 0:
            print(f"Connection Failed With Code {rc}")
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

        print(f"Publishing To {topic}")
        client.publish(
            topic,
            json_minimal(queue),
            qos=1,
            retain=False,
        )

    def connect_mqtt(self):
        global cookie_attempts
        
        if cookie_attempts[self.cookie_hash]['permanent_ban']:
            print(f"Cookie {self.cookie_hash[:10]} Đã Bị Ngưng Connect Vĩnh Viễn, Lí Do: Die Cookies, Check Point v.v")
            return False
            
        current_time = time.time()
        if current_time < cookie_attempts[self.cookie_hash]['banned_until']:
            remaining = cookie_attempts[self.cookie_hash]['banned_until'] - current_time
            print(f"Cookie {self.cookie_hash[:10]} Bị Tạm Khóa, Còn {remaining/3600:.1f} Giờ")
            return False

        if not self.lastSeqID:
            print("Error: No last_seq_id Available. Cannot Connect To MQTT.")
            return False

        chat_on = json_minimal(True)
        session_id = generate_session_id()
        user = {
            "u": self.dataFB["FacebookID"],
            "s": session_id,
            "chat_on": chat_on,
            "fg": False,
            "d": generate_client_id(),
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
            "username": json_minimal(user),
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
        self.mqtt.on_connect = self._messenger_queue_publish
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.username_pw_set(username=options["username"])

        parsed_host = urlparse(host)
        self.mqtt.ws_set_options(
            path=f"{parsed_host.path}?{parsed_host.query}",
            headers=options["ws_options"]["headers"],
        )

        print(f"Connecting To {options['ws_options']['headers']['Host']}...")
        try:
            self.mqtt.connect(
                host=options["ws_options"]["headers"]["Host"],
                port=443,
                keepalive=options["keepalive"],
            )

            print("MQTT Connection Established")
            self.mqtt.loop_start()
            return True
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
            cookie_attempts[self.cookie_hash]['count'] += 1
            return False

    def stop(self):
        if self.mqtt:
            print("Stopping MQTT Client...")
            try:
                self.mqtt.disconnect()
                self.mqtt.loop_stop()
            except:
                pass
        self.cleanup_memory()

    def sendTypingIndicatorMqtt(self, isTyping, thread_id, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        label = '3'
        is_group_thread = 1
        attribution = 0

        task_payload = {
            "thread_key": thread_id,
            "is_group_thread": is_group_thread,
            "is_typing": 1 if isTyping else 0,
            "attribution": attribution,
        }

        content = {
            "app_id": "2220391788200892",
            "payload": json.dumps({
                "label": label,
                "payload": json.dumps(task_payload, separators=(",", ":")),
                "version": "25393437286970779",
            }, separators=(",", ":")),
            "request_id": self.ws_req_number,
            "type": 4,
        }

        if callback is not None and callable(callback):
            self.req_callbacks[self.ws_req_number] = callback

        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            return True
        except Exception as e:
            print(f"Error Publishing Typing Indicator: {e}")
            return False

    def createPollMqtt(self, title, options, thread_id, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        self.ws_task_number += 1

        task_payload = {
            "question_text": title,
            "thread_key": thread_id,
            "options": options,
            "sync_group": 1,
        }

        task = {
            "failure_count": None,
            "label": "163",
            "payload": json.dumps(task_payload, separators=(",", ":")),
            "queue_name": "poll_creation",
            "task_id": self.ws_task_number,
        }

        content = {
            "app_id": "2220391788200892",
            "payload": json.dumps({
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [task],
                "version_id": "7158486590867448",
            }, separators=(",", ":")),
            "request_id": self.ws_req_number,
            "type": 3,
        }

        if callback is not None and callable(callback):
            self.req_callbacks[self.ws_req_number] = callback

        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            return True
        except Exception as e:
            print(f"Error Publishing Poll Creation: {e}")
            return False

    def send_message(self, text=None, thread_id=None, attachment=None, mention=None, message_id=None, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        if thread_id is None:
            print("Error: Thread ID Is Required")
            return False

        if text is None and attachment is None:
            print("Error: Text Or Attachment Is Required")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        content = {
            "app_id": "2220391788200892",
            "payload": {
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [],
                "version_id": "7545284305482586",
            },
            "request_id": self.ws_req_number,
            "type": 3,
        }

        text = str(text) if text is not None else ""
        if len(text) > 0:
            self.ws_task_number += 1
            task_payload = {
                "initiating_source": 0,
                "multitab_env": 0,
                "otid": generate_offline_threading_id(),
                "send_type": 1,
                "skip_url_preview_gen": 0,
                "source": 0,
                "sync_group": 1,
                "text": text,
                "text_has_links": 0,
                "thread_id": int(thread_id),
            }

            if message_id is not None:
                if not isinstance(message_id, str):
                    raise ValueError("message_id must be a string")
                task_payload["reply_metadata"] = {
                    "reply_source_id": message_id,
                    "reply_source_type": 1,
                    "reply_type": 0,
                }

            task = {
                "failure_count": None,
                "label": "46",
                "payload": json.dumps(task_payload, separators=(",", ":")),
                "queue_name": str(thread_id),
                "task_id": self.ws_task_number,
            }

            content["payload"]["tasks"].append(task)

        self.ws_task_number += 1
        task_mark_payload = {
            "last_read_watermark_ts": int(time.time() * 1000),
            "sync_group": 1,
            "thread_id": int(thread_id),
        }

        task_mark = {
            "failure_count": None,
            "label": "21",
            "payload": json.dumps(task_mark_payload, separators=(",", ":")),
            "queue_name": str(thread_id),
            "task_id": self.ws_task_number,
        }

        content["payload"]["tasks"].append(task_mark)

        content["payload"] = json.dumps(content["payload"], separators=(",", ":"))

        if callback is not None and callable(callback):
            self.req_callbacks[self.ws_req_number] = callback

        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            return True
        except Exception as e:
            print(f"Error Publishing Message: {e}")
            return False

    def send_message_with_attachment(self, text, thread_id, file_path_or_url, message_id=None, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        if thread_id is None:
            print("Error: Thread ID Is Required")
            return False

        try:
            if file_path_or_url.startswith(('http://', 'https://')):
                file_info = self.download_and_upload_file(file_path_or_url)
            else:
                file_info = self.upload_file(file_path_or_url)
                
            if not file_info:
                print("Failed To Upload File")
                return False

            self.cleanup_memory()

            self.ws_req_number += 1
            content = {
                "app_id": "2220391788200892",
                "payload": {
                    "data_trace_id": None,
                    "epoch_id": int(generate_offline_threading_id()),
                    "tasks": [],
                    "version_id": "7545284305482586",
                },
                "request_id": self.ws_req_number,
                "type": 3,
            }

            self.ws_task_number += 1
            task_payload = {
                "attachment_fbids": [file_info["id"]],
                "initiating_source": 0,
                "multitab_env": 0,
                "otid": generate_offline_threading_id(),
                "send_type": 3,
                "skip_url_preview_gen": 0,
                "source": 0,
                "sync_group": 1,
                "text": text,
                "text_has_links": 0,
                "thread_id": int(thread_id),
            }

            if message_id is not None:
                if not isinstance(message_id, str):
                    raise ValueError("message_id must be a string")
                task_payload["reply_metadata"] = {
                    "reply_source_id": message_id,
                    "reply_source_type": 1,
                    "reply_type": 0,
                }

            task = {
                "failure_count": None,
                "label": "46",
                "payload": json.dumps(task_payload, separators=(",", ":")),
                "queue_name": str(thread_id),
                "task_id": self.ws_task_number,
            }

            content["payload"]["tasks"].append(task)

            self.ws_task_number += 1
            task_mark_payload = {
                "last_read_watermark_ts": int(time.time() * 1000),
                "sync_group": 1,
                "thread_id": int(thread_id),
            }

            task_mark = {
                "failure_count": None,
                "label": "21",
                "payload": json.dumps(task_mark_payload, separators=(",", ":")),
                "queue_name": str(thread_id),
                "task_id": self.ws_task_number,
            }

            content["payload"]["tasks"].append(task_mark)

            content["payload"] = json.dumps(content["payload"], separators=(",", ":"))

            if callback is not None and callable(callback):
                self.req_callbacks[self.ws_req_number] = callback

            try:
                self.mqtt.publish(
                    topic="/ls_req",
                    payload=json.dumps(content, separators=(",", ":")),
                    qos=1,
                    retain=False,
                )
                return True
            except Exception as e:
                print(f"Error Publishing Message: {e}")
                return False

        except Exception as e:
            print(f"Error Sending Message With Attachment: {e}")
            return False

    def share_contact(self, text=None, sender_id=None, thread_id=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        if sender_id is None:
            print("Error: Sender ID Is Required")
            return False

        if thread_id is None:
            print("Error: Thread ID Is Required")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        self.ws_task_number += 1

        content = {
            "app_id": "2220391788200892",
            "payload": {
                "tasks": [{
                    "label": 359,
                    "payload": json.dumps({
                        "contact_id": sender_id,
                        "sync_group": 1,
                        "text": text or "",
                        "thread_id": thread_id
                    }, separators=(",", ":")),
                    "queue_name": "xma_open_contact_share",
                    "task_id": self.ws_task_number,
                    "failure_count": None,
                }],
                "epoch_id": generate_offline_threading_id(),
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
            return True
        except Exception as e:
            print(f"Error Publishing Contact Share: {e}")
            return False

    def share_link(self, text=None, url=None, thread_id=None, callback=None):
        if self.mqtt is None:
            print("Error: Not Connected To MQTT")
            return False

        if thread_id is None:
            print("Error: Thread ID Is Required")
            return False

        self.cleanup_memory()

        self.ws_req_number += 1
        self.ws_task_number += 1

        content = {
            "app_id": "2220391788200892",
            "payload": {
                "tasks": [{
                    "label": 46,
                    "payload": json.dumps({
                        "otid": generate_offline_threading_id(),
                        "source": 524289,
                        "sync_group": 1,
                        "send_type": 6,
                        "mark_thread_read": 0,
                        "url": url or "https://www.facebook.com",
                        "text": text or "",
                        "thread_id": thread_id,
                        "initiating_source": 0
                    }, separators=(",", ":")),
                    "queue_name": str(thread_id),
                    "task_id": self.ws_task_number,
                    "failure_count": None,
                }],
                "epoch_id": generate_offline_threading_id(),
                "version_id": "7191105584331330",
            },
            "request_id": self.ws_req_number,
            "type": 3
        }

        content["payload"] = json.dumps(content["payload"], separators=(",", ":"))

        if callback is not None and callable(callback):
            self.req_callbacks[self.ws_req_number] = callback

        try:
            self.mqtt.publish(
                topic="/ls_req",
                payload=json.dumps(content, separators=(",", ":")),
                qos=1,
                retain=False,
            )
            return True
        except Exception as e:
            print(f"Error Publishing Link Share: {e}")
            return False

    def upload_file(self, file_path):
        user_id = self.fb_instance.user_id
        url = "https://www.facebook.com/ajax/mercury/upload.php"
        headers = {
            'Cookie': self.dataFB['cookieFacebook'],
            'User-Agent': 'python-http/0.27.0',
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/'
        }

        params = {
            'ads_manager_write_regions': 'true',
            '__aaid': '0',
            '__user': user_id,
            '__a': '1',
            '__hs': '20207.HYP:comet_pkg.2.1...0',
            'dpr': '3',
            '__ccg': 'GOOD',
            '__rev': '1022311521',
            'fb_dtsg': self.dataFB['fb_dtsg'],
            'jazoest': self.dataFB['jazoest'],
            '__crn': 'comet.fbweb.CometHomeRoute'
        }

        mime_type = 'image/jpeg'
        if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            mime_type = 'video/mp4'

        with open(file_path, 'rb') as file:
            files = {'farr': (file_path.split('/')[-1], file, mime_type)}
            response = requests.post(url, headers=headers, params=params, files=files)

        if response.status_code == 200:
            content = response.text.replace('for (;;);', '')
            try:
                data = json.loads(content)
                if 'payload' in data and 'metadata' in data['payload'] and '0' in data['payload']['metadata']:
                    metadata = data['payload']['metadata']['0']
                    if mime_type.startswith('video'):
                        file_id = metadata.get('video_id')
                        return {'id': file_id, 'type': 'video'}
                    else:
                        file_id = metadata.get('fbid') or metadata.get('image_id')
                        return {'id': file_id, 'type': 'image'}
                else:
                    with open('response_debug.json', 'w', encoding='utf-8') as f:
                        f.write(content)
                    raise Exception(f"JSON Structure Not As Expected. Response Saved To response_debug.json")
            except json.JSONDecodeError:
                raise Exception(f"Cannot Parse JSON From Response: {response.text}")
        else:
            raise Exception(f"Error Uploading File: {response.status_code}")

    def download_and_upload_file(self, file_url):
        user_id = self.fb_instance.user_id
        url = "https://www.facebook.com/ajax/mercury/upload.php"
        headers = {
            'Cookie': self.dataFB['cookieFacebook'],
            'User-Agent': 'python-http/0.27.0',
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/'
        }

        params = {
            'ads_manager_write_regions': 'true',
            '__aaid': '0',
            '__user': user_id,
            '__a': '1',
            '__hs': '20207.HYP:comet_pkg.2.1...0',
            'dpr': '3',
            '__ccg': 'GOOD',
            '__rev': '1022311521',
            'fb_dtsg': self.dataFB['fb_dtsg'],
            'jazoest': self.dataFB['jazoest'],
            '__crn': 'comet.fbweb.CometHomeRoute'
        }

        mime_type = 'image/jpeg'
        if file_url.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            mime_type = 'video/mp4'
        elif file_url.lower().endswith(('.png', '.gif')):
            mime_type = f'image/{file_url.split(".")[-1].lower()}'

        try:
            response = requests.get(file_url, stream=True, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Không thể tải file từ URL: {response.status_code}")

            file_name = file_url.split('/')[-1] or f"temp_{int(time.time())}.{mime_type.split('/')[-1]}"
            
            files = {'farr': (file_name, response.content, mime_type)}
            upload_response = requests.post(url, headers=headers, params=params, files=files)

            if upload_response.status_code == 200:
                content = upload_response.text.replace('for (;;);', '')
                try:
                    data = json.loads(content)
                    if 'payload' in data and 'metadata' in data['payload'] and '0' in data['payload']['metadata']:
                        metadata = data['payload']['metadata']['0']
                        if mime_type.startswith('video'):
                            file_id = metadata.get('video_id')
                            return {'id': file_id, 'type': 'video'}
                        else:
                            file_id = metadata.get('fbid') or metadata.get('image_id')
                            return {'id': file_id, 'type': 'image'}
                    else:
                        with open('response_debug.json', 'w', encoding='utf-8') as f:
                            f.write(content)
                        raise Exception(f"Cấu trúc JSON không như mong đợi. Phản hồi đã lưu vào response_debug.json")
                except json.JSONDecodeError:
                    raise Exception(f"Không thể phân tích JSON từ phản hồi: {upload_response.text}")
            else:
                raise Exception(f"Lỗi khi tải file lên: {upload_response.status_code}")

        except Exception as e:
            print(f"Lỗi khi tải hoặc gửi file từ URL {file_url}: {e}")
            return None

# Lớp minhloi (giả định đã có từ mã gốc)
class minhloi:
    def __init__(self, cookie, mqtt_broker="broker.hivemq.com", mqtt_port=1883):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.init_params()

        self.mqtt_client = mqtt.Client(
            client_id=f"messenger_{self.user_id}_{int(time.time())}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic_base = "messenger/spam"

    def id_user(self):
        try:
            match = re.search(r"c_user=(\d+)", self.cookie)
            if not match:
                raise Exception("Cookie không hợp lệ")
            return match.group(1)
        except Exception as e:
            raise Exception(f"Lỗi khi lấy user_id: {str(e)}")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
                print(f"[*] Thử lấy fb_dtsg từ {url}")
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"[❌] Yêu cầu tới {url} thất bại, mã trạng thái: {response.status_code}")
                    continue

                with open('response_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"[*] Đã lưu phản hồi HTML vào response_debug.html để kiểm tra")

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
                    print(f"[✓] Lấy được fb_dtsg: {self.fb_dtsg}, jazoest: {self.jazoest}, rev: {self.rev}")
                    return
                else:
                    print(f"[⚠] Không tìm thấy fb_dtsg trong {url}")

            except Exception as e:
                print(f"[❌] Lỗi khi truy cập {url}: {str(e)}")
                time.sleep(2)

        raise Exception("Không thể lấy được fb_dtsg từ bất kỳ URL nào")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[✓] Kết nối MQTT broker: {self.mqtt_broker}")
            client.subscribe(f"{self.mqtt_topic_base}/#", qos=1)
            print(f"[✓] Subscribe topic: {self.mqtt_topic_base}/#")
        else:
            print(f"[❌] Kết nối MQTT thất bại, mã lỗi: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"[📩] Nhận từ {topic}: {payload}")

            recipient_id = topic.split('/')[-1]
            message = json.loads(payload).get('message', '')
            if not message:
                print("[!] Nội dung rỗng, bỏ qua.")
                return

            result = self.gui_tn(recipient_id, message)
            if result.get('success'):
                print(f"[✓] Gửi thành công tới {recipient_id}")
            else:
                print(f"[×] Gửi thất bại tới {recipient_id}")

        except Exception as e:
            print(f"[!] Lỗi xử lý MQTT: {str(e)}")

    def gui_tn(self, recipient_id, message):
        if not self.fb_dtsg or not self.jazoest or not self.rev:
            self.init_params()
        timestamp = int(time.time() * 1000)
        data = {
            'thread_fbid': recipient_id,
            'action_type': 'ma-type:user-generated-message',
            'body': message,
            'client': 'mercury',
            'author': f'fbid:{self.user_id}',
            'timestamp': timestamp,
            'source': 'source:chat:web',
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'ephemeral_ttl_mode': '',
            '__user': self.user_id,
            '__a': '1',
            '__req': '1b',
            '__rev': self.rev,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Referer': f'https://www.facebook.com/messages/t/{recipient_id}',
            'Cookie': self.cookie
        }

        try:
            response = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[❌] Gửi thất bại. Status: {response.status_code}")
                return {'success': False}

            if 'for (;;);' in response.text:
                json_data = json.loads(response.text.replace('for (;;);', ''))
                if 'error' in json_data:
                    print(f"[❌] Lỗi từ Facebook: {json_data.get('errorDescription', 'Unknown error')}")
                    return {'success': False}

            print("[✅] Gửi tin nhắn thành công.")
            return {'success': True}
        except Exception as e:
            print(f"[❌] Lỗi khi gửi: {str(e)}")
            return {'success': False}

# Hàm chính: send_messages_with_cookie
def send_messages_with_cookie(cookies, thread_ids, message_files, delay, option=0, file_path=None, contact_uid=None, name_file=None, nickname=None):
    global cookie_attempts, active_threads
    
    for cookie in cookies:
        cookie_hash = hashlib.md5(cookie.encode()).hexdigest()
        
        if cookie_attempts[cookie_hash]['permanent_ban']:
            print(f"Cookie {cookie_hash[:10]} Đã Bị Ngưng Hoạt Động Vĩnh Viễn\nLí Do: Cookies Die, CheckPoint V.V")
            continue
            
        current_time = time.time()
        if current_time < cookie_attempts[cookie_hash]['banned_until']:
            remaining = cookie_attempts[cookie_hash]['banned_until'] - current_time
            print(f"Cookie {cookie_hash[:10]} Bị Tạm Khóa, Còn {remaining/3600:.1f} Giờ\nLí Do: Checkpoint, Mõm, Cookies Die")
            continue

        try:
            fb = minhloi(cookie)
            sender = MessageSender(fbTools({
                "FacebookID": fb.user_id,
                "fb_dtsg": fb.fb_dtsg,
                "clientRevision": fb.rev,
                "jazoest": fb.jazoest,
                "cookieFacebook": cookie
            }), {
                "FacebookID": fb.user_id,
                "fb_dtsg": fb.fb_dtsg,
                "clientRevision": fb.rev,
                "jazoest": fb.jazoest,
                "cookieFacebook": cookie
            }, fb)

            if option not in [4, 10]:  # Không kết nối MQTT cho chế độ 4 và 10
                sender.get_last_seq_id()
                if not sender.connect_mqtt():
                    handle_failed_connection(cookie_hash)
                    continue

            for thread_id in thread_ids:
                print(f"Bắt Đầu Xử Lý Cho Box: {thread_id} với Cookie: {cookie_hash[:10]}")
                
                active_threads[f"{cookie_hash}_{thread_id}"] = sender

                try:
                    if option == 4:  # Change group name from file
                        if not name_file:
                            print("[!] Chưa cung cấp file chứa tên nhóm (nhay.txt)")
                            break
                        with open(name_file, 'r', encoding='utf-8') as f:
                            group_names = [line.strip() for line in f if line.strip()]
                        if not group_names:
                            print("[!] File nhay.txt không có nội dung!")
                            break
                        while True:
                            for group_name in group_names:
                                success, log = tenbox(group_name, thread_id, {
                                    "FacebookID": fb.user_id,
                                    "fb_dtsg": fb.fb_dtsg,
                                    "clientRevision": fb.rev,
                                    "jazoest": fb.jazoest,
                                    "cookieFacebook": cookie
                                })
                                print(log)
                                time.sleep(delay)
                                if current_time - sender.last_cleanup > 600:
                                    gc.collect()
                    elif option == 7:  # Create poll
                        if not name_file:
                            print("[!] Chưa cung cấp file chứa tiêu đề poll (nhay.txt)")
                            break
                        with open(name_file, 'r', encoding='utf-8') as f:
                            poll_titles = [line.strip() for line in f if line.strip()]
                        if not poll_titles:
                            print("[!] File nhay.txt không có nội dung!")
                            break
                        while True:
                            for title in poll_titles:
                                titles = title.split(',') if ',' in title else [title]
                                for single_title in titles:
                                    single_title = single_title.strip()
                                    if not single_title:
                                        continue
                                    options = ["Bá war", "Bá sàn"]
                                    print(f"[*] Tạo poll với tiêu đề: {single_title} trong box {thread_id}")
                                    success = sender.createPollMqtt(single_title, options, thread_id)
                                    if success:
                                        print(f"[✓] Đã tạo poll với tiêu đề: {single_title} trong box {thread_id}")
                                    else:
                                        print(f"[❌] Tạo poll thất bại với tiêu đề: {single_title} trong box {thread_id}")
                                    time.sleep(delay)
                                if current_time - sender.last_cleanup > 600:
                                    gc.collect()
                    elif option == 8:  # Fake typing with messages from nhay.txt
                        if not name_file:
                            print("[!] Chưa cung cấp file chứa nội dung tin nhắn (nhay.txt)")
                            break
                        with open(name_file, 'r', encoding='utf-8') as f:
                            messages = [line.strip() for line in f if line.strip()]
                        if not messages:
                            print("[!] File nhay.txt không có nội dung!")
                            break
                        while True:
                            for message in messages:
                                if not message:
                                    continue
                                print(f"[*] Gửi chỉ báo đang gõ cho box {thread_id}")
                                success = sender.sendTypingIndicatorMqtt(True, thread_id)
                                if success:
                                    print(f"[✓] Đã gửi chỉ báo đang gõ cho box {thread_id}")
                                else:
                                    print(f"[❌] Gửi chỉ báo đang gõ thất bại cho box {thread_id}")
                                    continue
                                
                                typing_duration = random.uniform(1, 3)
                                time.sleep(typing_duration)
                                
                                print(f"[*] Gửi tin nhắn: {message} tới box {thread_id}")
                                success = sender.send_message(message, thread_id)
                                if success:
                                    print(f"[✓] Đã gửi tin nhắn tới box {thread_id}")
                                else:
                                    print(f"[❌] Gửi tin nhắn thất bại tới box {thread_id}")
                                
                                success = sender.sendTypingIndicatorMqtt(False, thread_id)
                                if success:
                                    print(f"[✓] Đã tắt chỉ báo đang gõ cho box {thread_id}")
                                else:
                                    print(f"[❌] Tắt chỉ báo đang gõ thất bại cho box {thread_id}")
                                
                                time.sleep(delay)
                                if current_time - sender.last_cleanup > 600:
                                    gc.collect()
                    elif option == 9:  # Change theme
                        themes = sender.THEMES
                        if not themes:
                            print("[!] Danh sách theme rỗng!")
                            break
                        theme_index = 0
                        while True:
                            theme = themes[theme_index % len(themes)]
                            theme_id = theme["id"]
                            theme_name = theme["name"]
                            print(f"[*] Thay đổi theme với ID: {theme_id} ({theme_name}) cho box {thread_id}")
                            success = sender.set_theme(theme_id, thread_id)
                            if success:
                                print(f"[✓] Đã thay đổi theme thành: {theme_name} (ID: {theme_id}) cho box {thread_id}")
                            else:
                                print(f"[❌] Thay đổi theme thất bại cho box {thread_id}")
                            theme_index += 1
                            time.sleep(delay)
                            if current_time - sender.last_cleanup > 600:
                                gc.collect()
                    elif option == 10:  # Change nicknames for all members
                        while True:
                            # Print a "frame" to indicate a new nickname change cycle
                            print("\n" + "="*50)
                            print(f"[*] Chu kỳ đổi biệt danh mới cho box {thread_id}")
                            print("="*50)
                            nickname = input("[+] Nhập biệt danh muốn đặt cho tất cả thành viên (nhấn Enter để dừng):\n> ").strip()
                            if not nickname:
                                print("[*] Không nhập biệt danh, dừng chế độ đổi biệt danh cho box này.")
                                break
                            
                            # Get participant IDs
                            success, participant_ids, log = get_thread_info_graphql(thread_id, {
                                "FacebookID": fb.user_id,
                                "fb_dtsg": fb.fb_dtsg,
                                "clientRevision": fb.rev,
                                "jazoest": fb.jazoest,
                                "cookieFacebook": cookie
                            })
                            print(log)
                            if not success:
                                break

                            # Change nickname for each participant
                            for participant_id in participant_ids:
                                success, log = change_nickname(nickname, thread_id, participant_id, {
                                    "FacebookID": fb.user_id,
                                    "fb_dtsg": fb.fb_dtsg,
                                    "clientRevision": fb.rev,
                                    "jazoest": fb.jazoest,
                                    "cookieFacebook": cookie
                                })
                                print(log)
                                time.sleep(delay)
                            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã hoàn tất đổi biệt danh cho tất cả thành viên trong box {thread_id}")
                    else:  # Options 1, 2, 3, 5
                        while True:
                            content = ""
                            if message_files:
                                if len(message_files) > 1:
                                    selected = random.choice(message_files)
                                else:
                                    selected = message_files[0]
                                with open(selected, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()

                            if option == 2:
                                uid_to_share = contact_uid or fb.user_id
                                sender.share_contact(content, uid_to_share, thread_id)
                            elif option == 3:
                                uid_to_share = contact_uid or fb.user_id
                                share_url = f"https://www.facebook.com/{uid_to_share}"
                                sender.share_link(content, share_url, thread_id)
                            elif option == 5:
                                if not file_path:
                                    print("[!] Chưa cung cấp URL ảnh/video")
                                    break
                                print(f"[*] Gửi ảnh/video từ URL: {file_path} tới box {thread_id}")
                                success = sender.send_message_with_attachment(content, thread_id, file_path)
                                if success:
                                    print(f"[✓] Đã gửi ảnh/video tới box {thread_id}")
                                else:
                                    print(f"[❌] Gửi ảnh/video thất bại tới box {thread_id}")
                            else:  # Option 1
                                sender.send_message(content, thread_id)

                            time.sleep(delay)
                            
                            if current_time - sender.last_cleanup > 600:
                                gc.collect()

                except KeyboardInterrupt:
                    print(f"\nDừng Xử Lý Cho Box: {thread_id}")
                    break
                finally:
                    if option not in [4, 10]:
                        sender.stop()
                    if f"{cookie_hash}_{thread_id}" in active_threads:
                        del active_threads[f"{cookie_hash}_{thread_id}"]

        except Exception as e:
            print(f"Lỗi Trong Luồng Xử Lý Với Cookie {cookie_hash[:10]}: {e}")
            handle_failed_connection(cookie_hash)
            continue

    return True
    
def generateTimestampRelative():
    current_time = datetime.now()
    hours_ago = (datetime.now() - datetime.now()).seconds // 3600
    if hours_ago == 0:
        return "Just now"
    elif hours_ago == 1:
        return "1 hour ago"
    else:
        return f"{hours_ago} hours ago"

class minhloi:
    def __init__(self, cookie, mqtt_broker="broker.hivemq.com", mqtt_port=1883):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.init_params()

        self.mqtt_client = mqtt.Client(
            client_id=f"messenger_{self.user_id}_{int(time.time())}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic_base = "messenger/spam"

    def id_user(self):
        try:
            match = re.search(r"c_user=(\d+)", self.cookie)
            if not match:
                raise Exception("Cookie không hợp lệ")
            return match.group(1)
        except Exception as e:
            raise Exception(f"Lỗi khi lấy user_id: {str(e)}")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
                print(f"[*] Thử lấy fb_dtsg từ {url}")
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"[❌] Yêu cầu tới {url} thất bại, mã trạng thái: {response.status_code}")
                    continue

                with open('response_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"[*] Đã lưu phản hồi HTML vào response_debug.html để kiểm tra")

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
                    print(f"[✓] Lấy được fb_dtsg: {self.fb_dtsg}, jazoest: {self.jazoest}, rev: {self.rev}")
                    return
                else:
                    print(f"[⚠] Không tìm thấy fb_dtsg trong {url}")

            except Exception as e:
                print(f"[❌] Lỗi khi truy cập {url}: {str(e)}")
                time.sleep(2)

        raise Exception("Không thể lấy được fb_dtsg từ bất kỳ URL nào")

    def gui_tn(self, recipient_id, message):
        if not self.fb_dtsg or not self.jazoest or not self.rev:
            self.init_params()
        timestamp = int(time.time() * 1000)
        data = {
            'thread_fbid': recipient_id,
            'action_type': 'ma-type:user-generated-message',
            'body': message,
            'client': 'mercury',
            'author': f'fbid:{self.user_id}',
            'timestamp': timestamp,
            'source': 'source:chat:web',
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'ephemeral_ttl_mode': '',
            '__user': self.user_id,
            '__a': '1',
            '__req': '1b',
            '__rev': self.rev,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Referer': f'https://www.facebook.com/messages/t/{recipient_id}',
            'Cookie': self.cookie
        }

        try:
            response = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[❌] Gửi thất bại. Status: {response.status_code}")
                return {'success': False}

            if 'for (;;);' in response.text:
                json_data = json.loads(response.text.replace('for (;;);', ''))
                if 'error' in json_data:
                    print(f"[❌] Lỗi từ Facebook: {json_data.get('errorDescription', 'Unknown error')}")
                    return {'success': False}

            print("[✅] Gửi tin nhắn thành công.")
            return {'success': True}
        except Exception as e:
            print(f"[❌] Lỗi khi gửi: {str(e)}")
            return {'success': False}

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[✓] Kết nối MQTT broker: {self.mqtt_broker}")
            client.subscribe(f"{self.mqtt_topic_base}/#", qos=1)
            print(f"[✓] Subscribe topic: {self.mqtt_topic_base}/#")
        else:
            print(f"[❌] Kết nối MQTT thất bại, mã lỗi: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"[📩] Nhận từ {topic}: {payload}")

            recipient_id = topic.split('/')[-1]
            message = json.loads(payload).get('message', '')
            if not message:
                print("[!] Nội dung rỗng, bỏ qua.")
                return

            result = self.gui_tn(recipient_id, message)
            if result.get('success'):
                print(f"[✓] Gửi thành công tới {recipient_id}")
            else:
                print(f"[×] Gửi thất bại tới {recipient_id}")

        except Exception as e:
            print(f"[!] Lỗi xử lý MQTT: {str(e)}")

    def start_mqtt(self):
        print(f"[*] Kết nối MQTT {self.mqtt_broker}:{self.mqtt_port}...")
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"[❌] Lỗi kết nối MQTT: {str(e)}")

    def stop_mqtt(self):
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print("[*] Ngắt kết nối MQTT.")
        except Exception as e:
            print(f"[❌] Lỗi ngắt kết nối MQTT: {str(e)}")

def publish_messages(broker, port, topic_base, recipient_id, file_txt, delay):
    client = mqtt.Client(
        client_id=f"publisher_{int(time.time())}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    try:
        client.connect(broker, port, keepalive=60)
        topic = f"{topic_base}/{recipient_id}"

        print(f"[*] Publish tới {topic}...")
        while True:
            try:
                with open(file_txt, 'r', encoding='utf-8') as f:
                    message = f.read().strip()

                if not message:
                    print("[!] Nội dung rỗng, dừng.")
                    break

                payload = json.dumps({'message': message})
                client.publish(topic, payload, qos=1)
                print(f"[✓] Đã publish: {message}")

                sys.stdout.write("[*] Đang chờ ")
                for _ in range(int(delay)):
                    sys.stdout.write("⌛")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\n")

            except Exception as e:
                print(f"[!] Lỗi publish: {str(e)}")
                time.sleep(delay)

    except Exception as e:
        print(f"[❌] Lỗi kết nối publisher: {str(e)}")
    finally:
        client.disconnect()
        print("[*] Ngắt kết nối publisher.")
        
if __name__ == "__main__":
    try:
        print("=== Chế độ xử lý tin nhắn ===")
        print("1. Treo Bình Thường")
        print("2. Treo danh bạ (share contact)")
        print("3. Treo share link (URL từ UID)")
        print("4. Nhay Tên Nhóm")
        print("5. Treo ảnh hoặc video từ URL")
        print("6. Reg Box Messenger")
        print("7. Treo poll với tiêu đề từ nhay.txt")
        print("8. Fake typing với tin nhắn từ nhay.txt")
        print("9. Thay đổi theme nhóm chat")
        print("10. Đổi biệt danh tất cả thành viên trong nhóm")

        option = int(input("[+] Chọn chế độ (1-10):\n> ").strip())
        if option not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            print("[!] Chế độ không hợp lệ")
            exit()

        cookie_file = input("[+] Nhập đường dẫn file chứa cookie (mỗi cookie 1 dòng):\n> ").strip()

        if option == 6:
            print("[*] Chế độ tạo nhóm chat mới")
            num_groups = int(input("[+] Nhập số lượng nhóm muốn tạo:\n> ").strip())
            base_group_name = input("[+] Nhập tên cơ bản cho nhóm (ví dụ: 'kaka' sẽ tạo 'kaka 1', 'kaka 2', ...):\n> ").strip()
            user_ids_input = input("[+] Nhập danh sách ID người cần thêm vào nhóm (cách nhau bởi dấu phẩy):\n> ").strip()
            user_ids = [uid.strip() for uid in user_ids_input.split(",") if uid.strip()]
            if len(user_ids) < 2:
                print("[!] Cần ít nhất 2 ID để tạo nhóm.")
                exit()
            thread_ids = []
            message_files = []
            delay = 0
            file_url = None
            name_file = None
            uid_share = None
            nickname = None
        elif option in [7, 8]:
            print(f"[*] Chế độ {'tạo poll' if option == 7 else 'fake typing'} với nội dung từ nhay.txt")
            name_file = input("[+] Nhập đường dẫn file nhay.txt chứa danh sách nội dung:\n> ").strip()
            if not os.path.isfile(name_file):
                print(f"[!] File không tồn tại: {name_file}")
                exit()
            num_threads = int(input("[+] Nhập số lượng ID box:\n> ").strip())
            thread_ids = []
            for i in range(num_threads):
                thread_id = input(f"[+] Nhập ID box thứ {i+1}:\n> ").strip()
                if thread_id:
                    thread_ids.append(thread_id)
            delay = float(input("[+] Nhập delay (s):\n> ").strip())
            message_files = []
            file_url = None
            uid_share = None
            nickname = None
        elif option == 9:
            print("[*] Chế độ thay đổi theme nhóm chat")
            num_threads = int(input("[+] Nhập số lượng ID box:\n> ").strip())
            thread_ids = []
            for i in range(num_threads):
                thread_id = input(f"[+] Nhập ID box thứ {i+1}:\n> ").strip()
                if thread_id:
                    thread_ids.append(thread_id)
            delay = float(input("[+] Nhập delay (s):\n> ").strip())
            message_files = []
            file_url = None
            uid_share = None
            nickname = None
        elif option == 10:
            print("[*] Chế độ đổi biệt danh tất cả thành viên trong nhóm")
            num_threads = int(input("[+] Nhập số lượng ID box:\n> ").strip())
            thread_ids = []
            for i in range(num_threads):
                thread_id = input(f"[+] Nhập ID box thứ {i+1}:\n> ").strip()
                if thread_id:
                    thread_ids.append(thread_id)
            delay = float(input("[+] Nhập delay (s):\n> ").strip())
            message_files = []
            file_url = None
            uid_share = None
            name_file = None
            nickname = None  # Nickname will be prompted inside send_messages_with_cookie
        else:
            num_threads = int(input("[+] Nhập số lượng ID box:\n> ").strip())
            thread_ids = []
            for i in range(num_threads):
                thread_id = input(f"[+] Nhập ID box thứ {i+1}:\n> ").strip()
                if thread_id:
                    thread_ids.append(thread_id)
            
            delay = float(input("[+] Nhập delay (s):\n> ").strip())

            if option == 1:
                print("[*] Chế độ gửi tin nhắn văn bản")
                file_txt = input("[+] Nhập đường dẫn file .txt chứa nội dung tin nhắn:\n> ").strip()
                if not os.path.isfile(file_txt):
                    print(f"[!] File không tồn tại: {file_txt}")
                    exit()
                message_files = [file_txt]
                file_url = None
                uid_share = None
                name_file = None
                nickname = None
            elif option == 2:
                uid_share = input("[+] Nhập UID muốn share (mặc định là chính bạn):\n> ").strip()
                print("[*] Chế độ gửi danh bạ")
                file_txt = input("[+] Nhập đường dẫn file .txt chứa nội dung tin nhắn:\n> ").strip()
                if not os.path.isfile(file_txt):
                    print(f"[!] File không tồn tại: {file_txt}")
                    exit()
                message_files = [file_txt]
                file_url = None
                name_file = None
                nickname = None
            elif option == 3:
                uid_share = input("[+] Nhập UID cho link (mặc định là chính bạn):\n> ").strip()
                print("[*] Chế độ gửi share link (URL từ UID)")
                file_txt = input("[+] Nhập đường dẫn file .txt chứa nội dung tin nhắn:\n> ").strip()
                if not os.path.isfile(file_txt):
                    print(f"[!] File không tồn tại: {file_txt}")
                    exit()
                message_files = [file_txt]
                file_url = None
                name_file = None
                nickname = None
            elif option == 4:
                print("[*] Chế độ đổi tên nhóm chat")
                name_file = input("[+] Nhập đường dẫn file nhay.txt chứa danh sách tên nhóm:\n> ").strip()
                if not os.path.isfile(name_file):
                    print(f"[!] File không tồn tại: {name_file}")
                    exit()
                message_files = []
                file_url = None
                uid_share = None
                nickname = None
            elif option == 5:
                print("[*] Chế độ gửi ảnh hoặc video từ URL")
                file_url = input("[+] Nhập URL của ảnh hoặc video:\n> ").strip()
                if not file_url.startswith(('http://', 'https://')):
                    print("[!] URL không hợp lệ, phải bắt đầu bằng http:// hoặc https://")
                    exit()
                file_txt = input("[+] Nhập đường dẫn file .txt chứa nội dung tin nhắn (bỏ qua nếu không có):\n> ").strip()
                if file_txt and not os.path.isfile(file_txt):
                    print(f"[!] File không tồn tại: {file_txt}")
                    exit()
                message_files = [file_txt] if file_txt else []
                name_file = None
                uid_share = None
                nickname = None
            else:
                print("[!] Chế độ không hợp lệ")
                exit()

        if not os.path.isfile(cookie_file):
            print(f"[!] File cookie không tồn tại: {cookie_file}")
            exit()

        cookies = read_cookies_from_file(cookie_file)
        print(f"[*] Đã đọc {len(cookies)} cookie từ file.")

        if option == 6:
            for cookie in cookies:
                cookie_hash = hashlib.md5(cookie.encode()).hexdigest()
                
                if cookie_attempts[cookie_hash]['permanent_ban']:
                    print(f"Cookie {cookie_hash[:10]} Đã Bị Ngưng Hoạt Động Vĩnh Viễn\nLí Do: Cookies Die, CheckPoint V.V")
                    continue
                
                current_time = time.time()
                if current_time < cookie_attempts[cookie_hash]['banned_until']:
                    remaining = cookie_attempts[cookie_hash]['banned_until'] - current_time
                    print(f"Cookie {cookie_hash[:10]} Bị Tạm Khóa, Còn {remaining/3600:.1f} Giờ\nLí Do: Checkpoint, Mõm, Cookies Die")
                    continue

                try:
                    fb = minhloi(cookie)
                    dataFB = {
                        "FacebookID": fb.user_id,
                        "fb_dtsg": fb.fb_dtsg,
                        "clientRevision": fb.rev,
                        "jazoest": fb.jazoest,
                        "cookieFacebook": cookie
                    }

                    for i in range(num_groups):
                        group_title = f"{base_group_name} {i+1}"
                        print(f"[*] Tạo nhóm: {group_title}")
                        success, thread_id, log = create_new_group(dataFB, user_ids, group_title)
                        print(log)
                        
                        if success:
                            print(f"[*] Đã tạo nhóm thành công, ID: {thread_id}")
                        time.sleep(2)

                except Exception as e:
                    print(f"Lỗi Trong Luồng Xử Lý Với Cookie {cookie_hash[:10]}: {e}")
                    handle_failed_connection(cookie_hash)
                    continue
        else:
            if not thread_ids:
                print("[!] Chưa nhập ID box nào.")
                exit()

            send_messages_with_cookie(
                cookies,
                thread_ids,
                message_files,
                delay,
                option=option,
                file_path=file_url if option == 5 else None,
                contact_uid=uid_share if option in [2, 3] else None,
                name_file=name_file if option in [4, 7, 8] else None,
                nickname=nickname if option == 10 else None
            )

    except KeyboardInterrupt:
        print("\n[*] Dừng chương trình.")
    except Exception as e:
        print(f"[!] Lỗi: {str(e)}")