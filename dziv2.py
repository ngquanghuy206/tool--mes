import json
import ssl
import random
import string
from main.fb import *
from main import *
import importlib.util
from collections import defaultdict
import time
import requests
import attr, re, httpx, ssl, hashlib
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
from colorama import init, Fore, Style
from multiprocessing import Process, Queue, Manager, Lock
from queue import Empty
import signal
import sys

init(autoreset=True)

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def load_config():
    try:
        print("🤖 Đã Tiếp Nhận Config")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Không Tìm Thấy File config.json")
        return {"cookiefb": "", "BOTNAME": "", "prefix": "!", "ownerID": []}
    except json.JSONDecodeError:
        print("File config.json Không Hợp Lệ")
        return {"cookiefb": "", "BOTNAME": "", "prefix": "!", "ownerID": []}

def save_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_modules():
    modules = {}
    invalid_modules = []
    
    if not os.path.exists("modules"):
        os.makedirs("modules")
        return modules, invalid_modules
        
    for filename in os.listdir("modules"):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            file_path = os.path.join("modules", filename)
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                has_des = hasattr(module, "des")
                has_get_tkit = hasattr(module, "get_tkit") and callable(getattr(module, "get_tkit"))
                
                if has_des and has_get_tkit:
                    command_info = module.get_tkit()
                    if isinstance(command_info, dict) and command_info:
                        for command_name, handler_name in command_info.items():
                            modules[command_name] = {
                                'module': module,
                                'handler': handler_name
                            }
                    else:
                        invalid_modules.append(filename)
                else:
                    invalid_modules.append(filename)
            except Exception as e:
                print(f"Lỗi khi load module {filename}: {e}")
                invalid_modules.append(filename)
    
    return modules, invalid_modules

def command_worker(task_queue, result_queue, modules_path, prefix, cookie, owner_ids):
    """Worker process để xử lý commands"""
    # Load modules trong worker process
    modules, _ = load_modules()
    
    # Khởi tạo fb_instance trong worker
    fb = facebook(cookie)
    
    print(f"🔧 Command Worker started (PID: {os.getpid()})")
    
    while True:
        try:
            task = task_queue.get(timeout=1)
            
            if task == "STOP":
                print(f"🛑 Worker {os.getpid()} stopping...")
                break
            
            message_data = task
            message = message_data.get("body")
            thread_id = message_data.get("replyToID")
            user_id = str(message_data.get("userID"))
            
            if message and message.startswith(prefix):
                if user_id in owner_ids:
                    parts = message.split(" ")
                    command = parts[0][len(prefix):]
                    args = parts[1:]
                    
                    if command in modules:
                        try:
                            module_info = modules[command]
                            module = module_info['module']
                            handler_name = module_info['handler']
                            handler = getattr(module, handler_name)
                            
                            if callable(handler):
                                result = handler(args, fb, thread_id)
                                result_queue.put({
                                    "status": "success",
                                    "command": command,
                                    "message": message,
                                    "result": result
                                })
                                print(f"✅ Command executed: {command}")
                        except Exception as e:
                            result_queue.put({
                                "status": "error",
                                "command": command,
                                "error": str(e)
                            })
                            print(f"❌ Error executing {command}: {e}")
                else:
                    print(f"⛔ User {user_id} không có quyền sử dụng lệnh")
        
        except Empty:
            continue
        except Exception as e:
            print(f"Worker error: {e}")

def parse_cookie_string(cookie_string):
    cookie_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookie_dict[key.strip()] = value.strip()
    return cookie_dict

def generate_offline_threading_id() -> str:
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))

def str_base(number, base):
    def digitToChar(digit):
        if digit < 10:
            return str(digit)
        return chr(ord('a') + digit - 10)
    
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

def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))

def formAll(dataFB, FBApiReqFriendlyName=None, docID=None, requireGraphql=None):
    __reg = [0]
    __reg[0] += 1
    
    dataForm = {}
    
    if requireGraphql is None:
        dataForm["fb_dtsg"] = dataFB["fb_dtsg"]
        dataForm["jazoest"] = dataFB["jazoest"]
        dataForm["__a"] = 1
        dataForm["__user"] = str(dataFB["FacebookID"])
        dataForm["__req"] = str_base(__reg[0], 36)
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
        dataForm["__req"] = str_base(__reg[0], 36)
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
            return False
        except KeyError as e:
            print(f"Key Error: {e}")
            return False

class listeningEvent:
    def __init__(self, fbt, dataFB, fb_instance, modules=None, prefix="!", owner_ids=None, num_workers=4):
        self.bodyResults = {
            "body": None,
            "timestamp": 0,
            "userID": 0,
            "messageID": None,
            "replyToID": 0,
            "type": None,
            "attachments": {
                "id": 0,
                "url": None,
            },
            "mentions": []
        }
        self.syncToken = None
        self.lastSeqID = None
        self.dataFB = dataFB
        self.fbt = fbt
        self.mqtt = None
        self.fb_instance = fb_instance
        self.modules = modules or {}
        self.prefix = prefix
        self.owner_ids = owner_ids or []
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.config = None
        
        # Multiprocessing setup
        self.num_workers = num_workers
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.manager = Manager()
        self.should_stop = self.manager.Value('b', False)
        
        try:
            import json
            with open("config.json", "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)
                if "prefix" in self.config and self.config["prefix"]:
                    self.prefix = self.config["prefix"]
                if "ownerID" in self.config and self.config["ownerID"]:
                    self.owner_ids = self.config["ownerID"]
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def start_workers(self):
        """Khởi động worker processes"""
        print(f"{Fore.CYAN}🔧 Starting {self.num_workers} worker processes...")
        
        for i in range(self.num_workers):
            worker = Process(
                target=command_worker,
                args=(
                    self.task_queue,
                    self.result_queue,
                    "modules",
                    self.prefix,
                    self.dataFB["cookieFacebook"],
                    self.owner_ids
                )
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            print(f"{Fore.GREEN}✅ Worker {i+1} started (PID: {worker.pid})")
    
    def stop_workers(self):
        """Dừng tất cả workers"""
        print(f"{Fore.YELLOW}🛑 Stopping all workers...")
        for _ in range(self.num_workers):
            self.task_queue.put("STOP")
        
        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()
        
        print(f"{Fore.GREEN}✅ All workers stopped")
    
    def get_last_seq_id(self):
        success = self.fbt.getAllThreadList()
        if success:
            self.lastSeqID = self.fbt.last_seq_id
            print(f"last_seq_id: {self.lastSeqID}")
        else:
            print("Failed To Get Last Sequence ID. Check Facebook Authentication.")
        return
    
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            j = json.loads(payload)

            if "syncToken" in j and "firstDeltaSeqId" in j:
                self.syncToken = j["syncToken"]
                self.lastSeqID = j["firstDeltaSeqId"]
                return

            if "errorCode" in j:
                error = j["errorCode"]
                print(f"ERROR: {error} - {j.get('errorMessage', 'Unknown error')}")
                if error == "ERROR_QUEUE_NOT_FOUND" or error == "ERROR_QUEUE_OVERFLOW":
                    print("Resetting Sync Token And Reconnecting...")
                    self.syncToken = None
                    self.lastSeqID = None
                    self.get_last_seq_id()
                    self._messenger_queue_publish(client, userdata, None, 0)
                return

            if j.get('deltas') is not None:
                for delta in j["deltas"]:
                    if delta.get('messageMetadata') is not None:
                        self.bodyResults["body"] = delta.get("body")
                        meta = delta["messageMetadata"]
                        self.bodyResults["timestamp"] = meta.get("timestamp")
                        self.bodyResults["userID"] = meta.get("actorFbId")
                        self.bodyResults["messageID"] = meta.get("messageId")

                        thread_key = meta.get("threadKey", {})
                        thread_id = thread_key.get("otherUserFbId") or thread_key.get("threadFbId")
                        self.bodyResults["replyToID"] = thread_id
                        self.bodyResults["type"] = "user" if thread_key.get("otherUserFbId") is not None else "thread"

                        try:
                            mentions = []
                            if "data" in delta and "prng" in delta["data"]:
                                try:
                                    m_data = json.loads(delta["data"]["prng"])
                                    for m in m_data:
                                        if "i" in m:
                                            mentions.append(m["i"])
                                except:
                                    pass
                            self.bodyResults["mentions"] = mentions
                        except Exception as e:
                            print(f"Error extracting mentions: {e}")
                            self.bodyResults["mentions"] = []

                        try:
                            attachments = delta.get("attachments", [])
                            if attachments:
                                attachment = attachments[0]
                                self.bodyResults["attachments"]["id"] = attachment.get("fbid")
                                if "mercury" in attachment and "blob_attachment" in attachment["mercury"]:
                                    self.bodyResults["attachments"]["url"] = attachment["mercury"]["blob_attachment"]["preview"]["uri"]
                            else:
                                self.bodyResults["attachments"]["id"] = None
                                self.bodyResults["attachments"]["url"] = None
                        except Exception as e:
                            print(f"Error processing attachment: {e}")
                            self.bodyResults["attachments"]["id"] = None
                            self.bodyResults["attachments"]["url"] = None

                        # Ghi log tin nhắn
                        with open(".mqttMessage", "w", encoding="utf-8") as f:
                            f.write(json.dumps(self.bodyResults, indent=5))
                        
                        print(f"📩 Message from {self.bodyResults['userID']}: {self.bodyResults['body']}")
                        
                        # Gửi task đến worker pool để xử lý
                        if self.bodyResults["body"] and self.bodyResults["body"].startswith(self.prefix):
                            print(f"🔄 Sending command to worker pool...")
                            self.task_queue.put(dict(self.bodyResults))

        except json.JSONDecodeError as e:
            print(f"Failed Parsing MQTT Data: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected With Code {rc}")
        if rc != 0:
            print("Attempting To Reconnect...")
            try:
                client.reconnect()
            except:
                print("Reconnect Failed")
    
    def on_log(self, client, userdata, level, buf):
        pass
    
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
        
        print("Message Published, Waiting For Responses...")
        
    def connect_mqtt(self):
        if not self.lastSeqID:
            print("Error: No last_seq_id available. Cannot connect to MQTT.")
            return
            
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
        
        host = f"wss://edge-chat.facebook.com/chat?region=eag&sid={session_id}"
        options = {
            "client_id": "mqttwsclient",
            "username": json_minimal(user),
            "clean": True,
            "ws_options": {
                "headers": {
                    "Cookie": self.dataFB['cookieFacebook'],
                    "Origin": "https://www.facebook.com",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
                    "Referer": "https://www.facebook.com/",
                    "Host": "edge-chat.facebook.com",
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
        self.mqtt.on_message = self.on_message
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_log = self.on_log
        
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
            print("Starting MQTT Loop...")
            self.mqtt.loop_forever()
        except Exception as e:
            print(f"MQTT connection error: {e}")
            
    def stop(self):
        if self.mqtt:
            print("Stopping MQTT Client...")
            self.mqtt.disconnect()
        self.stop_workers()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n{Fore.YELLOW}🛑 Nhận tín hiệu dừng. Đang tắt bot...")
    sys.exit(0)

def main():
    try:
        signal.signal(signal.SIGINT, signal_handler)
        
        clr()
        print(f"{Fore.YELLOW}🚀 Đang khởi động bot...")
        config = load_config()
        cookie = config.get("cookiefb", "")
        prefix = config.get("prefix", "!")
        num_workers = config.get("num_workers", 4)  # Số workers có thể config
        hidden_owner_ids = ["61575275421167", "61575137977841"]
        config_owner_ids = config.get("ownerID", [])

        if not cookie:
            cookie = input(f"{Fore.GREEN}🍪 Nhập Cookies: ")
            config["cookiefb"] = cookie
            save_config(config)

        print(f"{Fore.YELLOW}🔄 Đang xử lý dữ liệu Facebook...")
        fb = facebook(cookie)

        if not fb.user_id or str(fb.user_id).startswith("Unable to retrieve data"):
            print(f"{Fore.RED}❌ Không thể xác thực tài khoản. Vui lòng kiểm tra lại cookie!")
            return

        print(f"{Fore.GREEN}✅ Xác thực thành công Facebook ID: {fb.user_id}")

        config_owner_ids_clean = [str(i).strip() for i in config_owner_ids if str(i).strip()]
        hidden_owner_ids_clean = [str(i).strip() for i in hidden_owner_ids if str(i).strip()]
        owner_ids = config_owner_ids_clean + hidden_owner_ids_clean

        if not config_owner_ids_clean:
            print(f"{Fore.YELLOW}⚠️ Cảnh báo: Danh sách ownerID trong config trống!")
        else:
            print(f"{Fore.CYAN}👥 Danh sách người được sử dụng lệnh:")
            for idx, owner_id in enumerate(config_owner_ids_clean, 1):
                print(f"{Fore.GREEN}   {idx}. {owner_id}")

        facebook_data = {
            "FacebookID": fb.user_id,
            "fb_dtsg": fb.fb_dtsg,
            "clientRevision": fb.rev,
            "jazoest": fb.jazoest,
            "cookieFacebook": cookie
        }

        modules, invalid_modules = load_modules() or ([], [])
        if invalid_modules:
            print(f"{Fore.YELLOW}⚠️ Các module không hợp lệ: {', '.join(invalid_modules)}")
        if modules:
            print(f"{Fore.CYAN}📦 Đã load {len(modules)} module: {', '.join(modules.keys())}")
        else:
            print(f"{Fore.YELLOW}⚠️ Không có module nào được load")

        print(f"{Fore.CYAN}🤖 Bot By Nguyễn Quang Huy Dzi - Online 🌐")
        print(f"{Fore.CYAN}🔑 Prefix: {prefix}")
        print(f"{Fore.CYAN}⚙️ Workers: {num_workers}")

        fb_tools = fbTools(facebook_data)
        success = fb_tools.getAllThreadList()
        if not success:
            print(f"{Fore.RED}❌ Không thể lấy danh sách thread. Thoát chương trình...")
            return

        listener = listeningEvent(fb_tools, facebook_data, fb, modules, prefix, owner_ids, num_workers)
        
        # Khởi động workers trước
        listener.start_workers()
        
        listener.get_last_seq_id()

        if listener.lastSeqID:
            try:
                listener.connect_mqtt()
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}🛑 Đã dừng chương trình.")
                listener.stop()
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi kết nối MQTT: {e}")
                listener.stop()
        else:
            print(f"{Fore.RED}❌ Không thể bắt đầu theo dõi vì thiếu Sequence ID. Kiểm tra lại cookie hoặc kết nối mạng.")
            listener.stop()

    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi không xác định: {e}")

if __name__ == "__main__":
    main()