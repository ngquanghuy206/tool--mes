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
init(autoreset=True)

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def extract_keys(html):
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div', class_='plaintext') 
    if code_div:
        keys = [line.strip() for line in code_div.get_text().split('\n') if line.strip()]
        return keys
    return []

def print_banner():
    banner = f"""{Fore.CYAN}{Style.BRIGHT}
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠓⠶⣤⠀⠀⠀⠀⣠⠶⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠇⠀⢠⡏⠀⠀⢀⡔⠉⠀⢈⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠤⣄⣼⠁⠀⣠⠟⠀⠀⣠⠏⠀⠀⢀⣀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢀⣀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠁⠀⠀⠣⣤⣀⡼⠃⠀⢀⡴⠋⠈⠳⡄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣶⣿⡿⠿⠿⠟⠛⠛⠛⠛⠿⠿⣿⣿⣶⣤⣄⠀⠀⠀⠉⠀⢀⡴⠋⠀⠀⣠⠞⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣾⣿⠿⠋⠉⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣶⣄⠀⠀⠳⣄⠀⣠⠞⢁⡠⢶⡄⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⠿⠋⠀⠀⢀⣴⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⢤⡈⠛⢿⣿⣦⡀⠈⠛⢡⠚⠃⠀⠀⢹⡆⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⠟⠁⠀⠀⠀⢀⣾⠃⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡆⠀⠀⢻⣦⠀⠙⢿⣿⣦⡀⠈⢶⣀⡴⠞⠋⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⣿⡿⠃⠀⠀⠀⠀⢀⣾⡇⢀⡄⠀⢸⡇⠀⠀⠀⠀⠀⠀⣀⠀⢸⣷⡀⠀⠀⠹⣷⡀⠀⠙⢿⣷⡀⠀⠉⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣰⣿⡟⠀⠀⠀⠀⠀⠀⣾⣿⠃⣼⡇⠀⢸⡇⠀⠀⠀⠀⠀⠀⣿⠀⢸⣿⣷⡀⠀⢀⣾⣿⡤⠐⠊⢻⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⣿⣿⣼⡇⠀⠀⠀⠀⢠⣿⠉⢠⣿⠧⠀⣸⣇⣠⡄⠀⠀⠀⠀⣿⠠⢸⡟⠹⣿⡍⠉⣿⣿⣧⠀⠀⠀⠻⣿⣶⣄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⡟⠀⠀⠀⠀⠀⣼⡏⢠⡿⣿⣦⣤⣿⡿⣿⡇⠀⠀⠀⢸⡿⠻⣿⣧⣤⣼⣿⡄⢸⡿⣿⡇⠀⠀⢠⣌⠛⢿⣿⣶⣤⣤⣄⡀
⠀⠀⠀⣀⣤⣿⣿⠟⣀⠀⠀⠀⠀⠀⣿⢃⣿⠇⢿⣯⣿⣿⣇⣿⠁⠀⠀⠀⣾⡇⢸⣿⠃⠉⠁⠸⣿⣼⡇⢻⡇⠀⠀⠀⢿⣷⣶⣬⣭⣿⣿⣿⠇
⣾⣿⣿⣿⣿⣻⣥⣾⡇⠀⠀⠀⠀⠀⣿⣿⠇⠀⠘⠿⠋⠻⠿⠿⠶⠶⠾⠿⠿⠍⢛⣧⣰⠶⢀⣀⣼⣿⣴⡸⣿⠀⠀⠀⠸⣿⣿⣿⠉⠛⠉⠀⠀
⠘⠛⠿⠿⢿⣿⠉⣿⠁⠀⠀⠀⠀⢀⣿⡿⣶⣶⣶⣤⣤⣤⣀⣀⠀⠀⠀⠀⠀⠀⢀⣭⣶⣿⡿⠟⠋⠉⠀⠀⣿⠀⡀⡀⠀⣿⣿⣿⡆⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣿⠀⣿⠀⠀⠸⠀⠀⠸⣿⠇⠀⠀⣈⣩⣭⣿⡿⠟⠃⠀⠀⠀⠀⠀⠙⠛⠛⠛⠛⠻⠿⠷⠆⠀⣯⠀⠇⡇⠀⣿⡏⣿⣧⠀⠀⠀⠀
⠀⠀⠀⠀⢿⣿⡀⣿⡆⠀⠀⠀⠀⠀⣿⠰⠿⠿⠛⠋⠉⠀⠀⢀⣴⣶⣶⣶⣶⣶⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣧⠀⠀⠀⣿⡇⣿⣿⠀⠀⠀⠀
⠀⠀⠀⠀⢸⣿⡇⢻⣇⠀⠘⣰⡀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⠀⠀⠀⣿⣧⣿⡿⠀⠀⠀⠀
⠀⠀⠀⠀⠈⣿⣧⢸⣿⡀⠀⡿⣧⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣿⡄⠀⠀⠀⣼⡇⠀⠀⠀⠀⠀⠀⢀⣤⣾⡟⢡⣶⠀⢠⣿⣿⣿⠃⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠹⣿⣿⣿⣷⠀⠇⢹⣷⡸⣿⣶⣦⣄⣀⡀⠀⠀⠀⣿⡇⠀⠀⢠⣿⠁⣀⣀⣠⣤⣶⣾⡿⢿⣿⡇⣼⣿⢀⣿⣿⠿⠏⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠛⠛⣿⣷⣴⠀⢹⣿⣿⣿⡟⠿⠿⣿⣿⣿⣿⣾⣷⣶⣿⣿⣿⣿⡿⠿⠟⠛⠋⠉⠀⢸⣿⣿⣿⣿⣾⣿⠃⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣦⣘⣿⡿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⠛⠻⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠻⣿⣿⣿⠈⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
{Fore.CYAN}{Style.BRIGHT}╔════════════════════════════════════════════╗
{Fore.CYAN}{Style.BRIGHT}║        BOT MESSENGER - NGUYỄN QUANG HUY    ║
{Fore.CYAN}{Style.BRIGHT}║                Version 5.5.0               ║
{Fore.CYAN}{Style.BRIGHT}╚════════════════════════════════════════════╝
{Fore.YELLOW}🚀 Đang khởi động bot...
"""
    print(banner)
def load_config():
    try:
        print("🤖 Đã Tiếp NhậnVà Prefix Của Account ")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Không Tìm Thấy File config.json")
        return {"cookiefb": "", "BOTNAME": "", "prefix": "!", "ownerID": [], "send_tu_dong": False}
    except json.JSONDecodeError:
        print("File config.json Không Hợp Lệ")
        return {"cookiefb": "", "BOTNAME": "", "prefix": "!", "ownerID": [], "send_tu_dong": False}

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

def process_message(message, modules, prefix, fb_instance, thread_id):
    if not message or not message.startswith(prefix):
        return
        
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
                result = handler(args, fb_instance, thread_id)
                return result
        except Exception as e:
            return f"lỗi thực thi lệnh {command}: {e}"
    return None

def parse_cookie_string(cookie_string):
    cookie_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        if "=" in cookie:
            key, value = cookie.split("=")
        else:
            pass
        try: cookie_dict[key] = value
        except: pass
    return cookie_dict

def generate_offline_threading_id() -> str:
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))
    
def get_headers(
    url: str, options: dict = {}, ctx: dict = {}, customHeader: dict = {}
) -> dict:
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.facebook.com/",
        "Host": url.replace("https://", "").split("/")[0],
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

def get_from(input_str, start_token, end_token):
    start = input_str.find(start_token) + len(start_token)
    if start < len(start_token):
        return ""

    last_half = input_str[start:]
    end = last_half.find(end_token)
    if end == -1:
        raise ValueError(f"Could not find endTime `{end_token}` in the given string.")

    return last_half[:end]

def base36encode(number: int, alphabet="0123456789abcdefghijklmnopqrstuvwxyz"):
    """Converts an integer to a base36 string."""
    if not isinstance(number, int):
        raise TypeError("number must be an integer")

    base36 = ""
    sign = ""

    if number < 0:
        sign = "-"
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36

def dataSplit(string1, string2, numberSplit1=None, numberSplit2=None, HTML=None, amount=None, string3=None, numberSplit3=None, defaultValue=None):
    if (defaultValue): numberSplit1, numberSplit2 = 1, 0
    if (amount == None):
        return HTML.split(string1)[numberSplit1].split(string2)[numberSplit2]
    elif (amount == 3):
        return HTML.split(string1)[numberSplit1].split(string2)[numberSplit2].split(string3)[numberSplit3]

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

def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))

def formAll(dataFB, FBApiReqFriendlyName=None, docID=None, requireGraphql=None):
    # Khởi tạo biến __reg để đếm yêu cầu
    __reg = [0]  # Dùng list để thay đổi giá trị trong hàm
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
            print(f"Response first part: {response_parts[0][:100]}")
            return False
        except KeyError as e:
            print(f"Key Error: {e}")
            print("The expected data structure wasn't found in the response")
            return False
    
    def typeCommand(self, commandUsed):
        listData = []
        
        try:
            if self.dataGet is None:
                return "No data available. Make sure to call getAllThreadList first."
                
            data_to_parse = self.dataGet
            if data_to_parse.startswith("for(;;);"):
                data_to_parse = data_to_parse[9:]
                
            getData = json.loads(data_to_parse)["o0"]["data"]["viewer"]["message_threads"]["nodes"]
        except json.JSONDecodeError as e:
            return f"Failed to decode JSON response: {e}"
        except KeyError as e:
            try:
                error_data = json.loads(data_to_parse)["o0"]
                if "errors" in error_data:
                    return error_data["errors"][0]["summary"]
                else:
                    return f"Unexpected response structure. Missing key: {e}"
            except:
                return f"Unexpected response structure. Missing key: {e}"
        
        dataThread = None
        for getNeedIDThread in getData:
            thread_key = getNeedIDThread.get("thread_key", {})
            thread_fbid = thread_key.get("thread_fbid")
            if thread_fbid and str(thread_fbid) == str(self.threadID):
                dataThread = getNeedIDThread
                break
        
        if dataThread is not None:
            if commandUsed == "getAdmin":
                for dataID in dataThread.get("thread_admins", []):
                    listData.append(str(dataID["id"]))
                exportData = {
                    "adminThreadList": listData
                }
            elif commandUsed == "threadInfomation":
                threadInfoList = dataThread.get("customization_info", {})
                exportData = {
                    "nameThread": dataThread.get("name"), 
                    "IDThread": self.threadID, 
                    "emojiThread": threadInfoList.get("emoji"),
                    "messageCount": dataThread.get("messages_count"),
                    "adminThreadCount": len(dataThread.get("thread_admins", [])),
                    "memberCount": len(dataThread.get("all_participants", {}).get("edges", [])),
                    "approvalMode": "Bật" if (dataThread.get("approval_mode", 0) != 0) else "Tắt",
                    "joinableMode": "Bật" if (dataThread.get("joinable_mode", {}).get("mode") != "0") else "Tắt",
                    "urlJoinableThread": dataThread.get("joinable_mode", {}).get("link", "")
                }
            elif commandUsed == "exportMemberListToJson":
                getMemberList = dataThread.get("all_participants", {}).get("edges", [])
                for exportMemberList in getMemberList:
                    node = exportMemberList.get("node", {})
                    dataUserThread = node.get("messaging_actor", {})
                    if dataUserThread:
                        exportData = json.dumps({
                            dataUserThread.get("id", ""): {
                                "nameFB": str(dataUserThread.get("name", "")),
                                "idFacebook": str(dataUserThread.get("id", "")),
                                "profileUrl": str(dataUserThread.get("url", "")),
                                "avatarUrl": str(dataUserThread.get("big_image_src", {}).get("uri", "")),
                                "gender": str(dataUserThread.get("gender", "")),
                                "usernameFB": str(dataUserThread.get("username", ""))
                            }
                        }, skipkeys=True, allow_nan=True, ensure_ascii=False, indent=5)
                        listData.append(exportData)
                exportData = listData
            else:
                exportData = {
                    "err": "no data"
                }
                
            return exportData
            
        else:
            return "Không lấy được dữ liệu ThreadList, đã xảy ra lỗi T___T"
    
    def getListThreadID(self):
        try:
            if self.dataGet is None:
                return {
                    "ERR": "No data available. Make sure to call getAllThreadList first."
                }
                
            data_to_parse = self.dataGet
            if data_to_parse.startswith("for(;;);"):
                data_to_parse = data_to_parse[9:]
                
            threadIDList = []
            threadNameList = []
            try:
                getData = json.loads(data_to_parse)["o0"]["data"]["viewer"]["message_threads"]["nodes"]
                
                for getThreadID in getData:
                    thread_key = getThreadID.get("thread_key", {})
                    thread_fbid = thread_key.get("thread_fbid")
                    
                    if thread_fbid is not None:
                        threadIDList.append(thread_fbid)
                        threadNameList.append(getThreadID.get("name", "No Name"))
                        
                return {
                    "threadIDList": threadIDList,
                    "threadNameList": threadNameList,
                    "countThread": len(threadIDList)
                }
                
            except (KeyError, json.JSONDecodeError) as e:
                return {
                    "ERR": f"Error processing thread data: {str(e)}"
                }
                
        except Exception as errLog:
            return {
                "ERR": f"Unexpected error: {str(errLog)}"
            }

class listeningEvent:
    def __init__(self, fbt, dataFB, fb_instance, modules=None, prefix="!", owner_ids=None):
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
        self.modules = modules or {}
        self.prefix = prefix
        self.fb_instance = fb_instance
        self.owner_ids = owner_ids or []
        self.spam_tasks = {}
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.req_callbacks = {}
        self.config = None
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
    
    def changeNickname(self, nickname, thread_id, participant_id):
          dataForm = formAll(self.dataFB, requireGraphql=False)
          dataForm["nickname"] = nickname
          dataForm["participant_id"] = participant_id
          dataForm["thread_or_other_fbid"] = thread_id
     
          sendRequests = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/save_thread_nickname/?source=thread_settings&dpr=1", dataForm, self.dataFB["cookieFacebook"])).text.split("for (;;);")[1])
          
          if sendRequests.get("error"):
               error = sendRequests.get("error")
               if error == 1545014:
                    return ("error", "Người dùng không tồn tại trong nhóm/cuộc trò chuyện.")
               elif error == 1357031:
                    return ("error", "Người dùng không tồn tại.")
               else:
                    return ("error", "Lỗi không xác định.")
          else:
               return ("success", "Thay đổi biệt danh người dùng thành công.")
          
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
	                    if delta.get("class") == "ParticipantsAddedToGroupThread":
	                        event_type = "Join"
	                        participant = delta.get("addedParticipants")[0]
	                        
	                        full_name = participant.get("fullName")
	                        thread_key = delta["messageMetadata"].get("threadKey", {})
	                        thread_id = thread_key.get("threadFbId")
	                        
	                        if str(participant.get("userFbId")) == str(self.dataFB['FacebookID']):
	                            if self.config and "BOTNAME" in self.config and self.config["BOTNAME"]:
	                                bot_name = f"[ {self.prefix} ] • {self.config['BOTNAME']}"
	                                self.changeNickname(bot_name, thread_id, self.dataFB['FacebookID'])
	                        
	                        if full_name and thread_id:
	                            response = f"Xin Chào {full_name}, Đã Đến Với Box Này"
	                            self.send_message(text=response, thread_id=thread_id)
	                            
	                    elif delta.get("class") == "ParticipantLeftGroupThread":
	                        event_type = "Leave"
	                        uid = delta.get("leftParticipantFbId")
	                        full_name = None
	                        
	                        if "messageMetadata" in delta and "adminText" in delta["messageMetadata"]:
	                            admin_text = delta["messageMetadata"]["adminText"]
	                            name_match = re.search(r"(.*?) left the group", admin_text)
	                            if name_match:
	                                full_name = name_match.group(1)
	                        
	                        thread_key = delta["messageMetadata"].get("threadKey", {})
	                        thread_id = thread_key.get("threadFbId")
	                        if thread_id:
	                            response = f"Tạm Biệt {full_name or 'Người Dùng'}, Đã Về Phương Trời Mới\nLink Facebook Của Họ: https://www.facebook.com/profile.php?id={uid}"
	                            self.send_message(text=response, thread_id=thread_id)
	                    elif delta.get("class") == "ThreadName":
	                        pass
	                    else:
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
	
	                        user_id = str(self.bodyResults["userID"])
	                        if self.bodyResults["body"] and 'reply' in self.modules:
	                            from modules.reply import check_and_reply
	                            check_and_reply(self.bodyResults["body"], user_id, self)
	
	                        if self.bodyResults["body"] and self.bodyResults["body"].startswith(self.prefix) and self.modules:
	                            user_id = str(self.bodyResults["userID"])
	                            thread_id = self.bodyResults["replyToID"]
	                            if user_id in self.owner_ids:
	                                command = self.bodyResults["body"][len(self.prefix):].split()[0]
	                                
	                                if command == "spam":
	                                    self.start_spam(thread_id)
	                                elif command == "stspam":
	                                    self.stop_spam(thread_id)
	                                elif command == "reo":
	                                    message_parts = self.bodyResults["body"].split()
	                                    if len(message_parts) > 1 and '@' in self.bodyResults["body"]:
	                                        import re
	                                        text = self.bodyResults["body"]
	                                        mentions = []
	                                        
	                                        if self.bodyResults["mentions"]:
	                                            for uid in self.bodyResults["mentions"]:
	                                                mentions.append({
	                                                    "id": uid
	                                                })
	                                        
	                                        self.nhay_command(thread_id, mentions)
	                                    else:
	                                        self.nhay_command(thread_id)
	                                elif command == "stopreo":
	                                    self.stop_nhay(thread_id)
	                                elif command == "regbox":
	                                    from modules.regbox import cmd_regbox
	                                    message_content = self.bodyResults["body"][len(self.prefix + command):].strip()
	                                    cmd_regbox(message_content, self.fb_instance, thread_id, self.bodyResults["mentions"])
	                                elif command == "reply":
	                                    from modules.reply import cmd_reply
	                                    cmd_reply([], self.fb_instance, thread_id, self.bodyResults["mentions"])
	                                elif command == "streply":
	                                    from modules.reply import cmd_stopreply
	                                    cmd_stopreply([], self.fb_instance, thread_id)
	                                else:
	                                    response = process_message(self.bodyResults["body"], self.modules, self.prefix, self.fb_instance, thread_id)
	                                    if response:
	                                        pass
	                            else:
	                                pass
	
	                        with open(".mqttMessage", "w", encoding="utf-8") as f:
	                            f.write(json.dumps(self.bodyResults, indent=5))
	
	    except json.JSONDecodeError as e:
	        print(f"Failed Parsing MQTT Data: {e}")
	        print(f"Raw Data: {msg.payload}...")
	    except Exception as e:
	        print(f"Error processing message: {e}")
    def process_message_with_mentions(self, message, thread_id):
        if not message.startswith(self.prefix):
            return None
            
        parts = message.split(" ")
        command = parts[0][len(self.prefix):]
        args = parts[1:]
        
        if command in self.modules:
            try:
                module_info = self.modules[command]
                module = module_info['module']
                handler_name = module_info['handler']
                handler = getattr(module, handler_name)
                
                if callable(handler):
                    result = handler(args, self.fb_instance, thread_id)
                    return result
            except Exception as e:
                response = f"Lỗi Thực Thi Lệnh {command}: {e}"
                self.fb_instance.send_msg(thread_id, response)
                return response
        return None
    
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
    
    def start_spam(self, thread_id):
        import threading
        import random
        import os
        
        if thread_id in self.spam_tasks:
            self.send_message("Đã Có Một Tiến Trình Spam Đang Chạy", thread_id=thread_id)
            return
        
        content = None
        file_names = ["ngon.txt", "treo.txt", "ngon1.txt", "ngon2.txt", "ngon3.txt", "tkiet.txt"]
        
        for file_name in file_names:
            if os.path.exists(file_name):
                try:
                    with open(file_name, "r", encoding="utf-8") as f:
                        content = f.read()
                        break
                except Exception as e:
                    print(f"Lỗi Đọc File {file_name}: {e}")
        
        if not content:
            self.send_message("Vui Lòng Tạo File ngon.txt Và Nhập Ngôn Vào Đó", thread_id=thread_id)
            return
        
        stop_event = threading.Event()
        
        def spam_thread():
            self.send_message("Bot Python Coder By Nguyễn Quang Huy (Dzi)", thread_id=thread_id)
            
            while not stop_event.is_set():
                try:
                    self.send_message(content, thread_id=thread_id)
                    delay = random.uniform(10, 25)
                    if stop_event.wait(delay):
                        break
                except Exception as e:
                    print(f"Lỗi Trong Quá Trình Spam: {e}")
                    break
            
            self.spam_tasks.pop(thread_id, None)
        
        spam_thread_obj = threading.Thread(target=spam_thread)
        spam_thread_obj.daemon = True
        spam_thread_obj.start()
        
        self.spam_tasks[thread_id] = {
            "thread": spam_thread_obj,
            "stop_event": stop_event
        }
        
    def stop_spam(self, thread_id):
        if thread_id in self.spam_tasks:
            self.spam_tasks[thread_id]["stop_event"].set()
            self.send_message("Bot Python Coder By Nguyễn Quang Huy (Dzi)", thread_id=thread_id)
        else:
            self.fb_instance.send_msg(thread_id, "Không Có Tiến Trình Spam Nào Đang Chạy")
    
    def get_message_info(self, thread_id=None):
        try:
            with open(".mqttMessage", "r", encoding="utf-8") as f:
                message_data = json.loads(f.read())
                if thread_id is None or str(message_data["replyToID"]) == str(thread_id):
                    return message_data
                return None
        except Exception as e:
            print(f"Error reading message info: {e}")
            return None
    
    def send_message(self, text=None, mention=None, attachment=None, thread_id=None, message_id=None):
        if self.mqtt is None:
            print("Error: Not connected to MQTT")
            return False
            
        if thread_id is None:
            print("Error: thread_id is required")
            return False
            
        if text is None and attachment is None:
            print("Error: text or attachment required")
            return False
            
        
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
        
        if text is not None:
            text = str(text)
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
                        pass
                    else:
                        task_payload["reply_metadata"] = {
                            "reply_source_id": message_id,
                            "reply_source_type": 1,
                            "reply_type": 0,
                        }
                
                if mention is not None and len(text) > 0:
                    try:
                        valid_mentions = self.get_valid_mentions(text, mention)
                        
                        if valid_mentions:
                            task_payload["mention_data"] = {
                                "mention_ids": ",".join([str(x["i"]) for x in valid_mentions]),
                                "mention_lengths": ",".join([str(x["l"]) for x in valid_mentions]),
                                "mention_offsets": ",".join([str(x["o"]) for x in valid_mentions]),
                                "mention_types": ",".join(["p" for _ in valid_mentions]),
                            }
                    except Exception as e:
                        print(f"Error processing mentions: {e}")
                
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
        
        if attachment is not None:
            pass
        
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
            print(f"Error publishing message: {e}")
            return False
    
    def get_valid_mentions(self, text, mention):
        if not isinstance(mention, dict) and not isinstance(mention, list):
            raise ValueError("Mentions must be a dict or list of dict")

        mentions = mention if isinstance(mention, list) else [mention]

        valid_mentions = []
        current_offset = 0
        for mention in mentions:
            if "id" in mention and "tag" in mention:
                provided_offset = mention.get("offset")
                tag_len = 0

                if isinstance(provided_offset, int):
                    if provided_offset >= len(text):
                        break

                    is_length_exceed = provided_offset + len(mention["tag"]) > len(text)
                    tag_len = (
                        len(mention["tag"])
                        if not is_length_exceed
                        else len(text) - provided_offset
                    )
                    current_offset = provided_offset
                else:
                    if current_offset >= len(text):
                        break

                    find = text.find(mention["tag"], current_offset)
                    if find != -1:
                        is_length_exceed = find + len(mention["tag"]) > len(text)
                        tag_len = (
                            len(mention["tag"])
                            if not is_length_exceed
                            else len(text) - find
                        )

                        current_offset = find

                valid_mentions.append(
                    {
                        "i": mention["id"],
                        "o": current_offset,
                        "l": tag_len,
                    }
                )

                current_offset += tag_len

        return valid_mentions
        
    def send_typing_indicator(self, thread_id, is_typing=True):
        if self.mqtt is None:
            print("Error: Not connected to MQTT")
            return False
            
        self.ws_req_number += 1
        
        try:
            is_group_thread = 1
            
            task_payload = {
                "thread_key": thread_id,
                "is_group_thread": is_group_thread,
                "is_typing": 1 if is_typing else 0,
                "attribution": 0
            }
            
            payload = json.dumps(task_payload)
            version = "25393437286970779"
            
            content = {
                "app_id": "2220391788200892",
                "payload": json.dumps({
                    "label": "3",
                    "payload": payload,
                    "version": version,
                }),
                "request_id": self.ws_req_number,
                "type": 4,
            }
            
            self.mqtt.publish(
                "/ls_req", 
                json.dumps(content, separators=(",", ":")), 
                qos=1, 
                retain=False
            )
            return True
        except Exception as e:
            print(f"Error sending typing indicator: {e}")
            return False

    def nhay_command(self, thread_id, mentions=None):
        import threading
        import random
        import os
        import time

        if thread_id in self.spam_tasks:
            self.fb_instance.send_msg(thread_id, "Đã Có Một Tiến Trình Réo Đang Chạy")
            return

        content = None
        file_name = "reo.txt"

        if os.path.exists(file_name):
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    content = f.readlines()
            except Exception as e:
                print(f"Lỗi Đọc File {file_name}: {e}")
                return
        else:
            self.fb_instance.send_msg(thread_id, f"Vui Lòng Tạo File {file_name} Và Nhập Nội Dung Vào Đó")
            return

        if not content:
            self.fb_instance.send_msg(thread_id, f"File {file_name} Không Có Nội Dung")
            return

        stop_event = threading.Event()

        mention_infos = {}
        if mentions and len(mentions) > 0:
            for mention in mentions:
                uid = mention.get("id")
                if uid:
                    try:
                        user_info = self.fb_instance.get_info(uid)
                        if "name" in user_info:
                            mention_infos[uid] = user_info["name"]
                    except Exception as e:
                        print(f"Error fetching info for {uid}: {e}")

        def nhay_thread():
            line_index = 0
            lines = [line.strip() for line in content if line.strip()]

            if not lines:
                self.spam_tasks.pop(thread_id, None)
                return

            while not stop_event.is_set():
                try:
                    if lines:
                        msg = lines[line_index]
                        line_index = (line_index + 1) % len(lines)

                        self.send_typing_indicator(thread_id, True)

                        time.sleep(2)

                        if mention_infos:
                            for uid, name in mention_infos.items():
                                try:
                                    tag_message = random.choice([f"{name} {msg}", f"{msg} {name}"])
                                    mention_obj = {
                                        "id": uid,
                                        "tag": name
                                    }

                                    self.send_message(
                                        text=tag_message,
                                        mention=mention_obj,
                                        thread_id=thread_id
                                    )
                                except Exception as e:
                                    print(f"Error sending tag message for {uid}: {e}")
                                    self.send_message(text=msg, thread_id=thread_id)
                        else:
                            self.send_message(text=msg, thread_id=thread_id)

                        if stop_event.wait(random.uniform(1, 3)):
                            break
                except Exception as e:
                    print(f"Lỗi Trong Quá Trình Réo: {e}")
                    break

            self.spam_tasks.pop(thread_id, None)

        nhay_thread_obj = threading.Thread(target=nhay_thread)
        nhay_thread_obj.daemon = True
        nhay_thread_obj.start()

        self.spam_tasks[thread_id] = {
            "thread": nhay_thread_obj,
            "stop_event": stop_event,
            "type": "nhay"
        }
        
    def stop_nhay(self, thread_id):
        if thread_id in self.spam_tasks and self.spam_tasks[thread_id].get("type") == "nhay":
            self.spam_tasks[thread_id]["stop_event"].set()
            self.send_message("Đã Dừng Tiến Trình Réo", thread_id=thread_id)
        else:
            self.send_message("Không Có Tiến Trình Réo Nào Đang Chạy", thread_id=thread_id)

def main():
    try:
        clr()
        print_banner()
        config = load_config()
        cookie = config.get("cookiefb", "")
        prefix = config.get("prefix", "!")
        hidden_owner_ids = ["61575275421167", "61575137977841"]
        config_owner_ids = config.get("ownerID", [])
        namebot = config.get("BOTNAME", "")

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
            if not hidden_owner_ids_clean:
                confirm = input(f"{Fore.YELLOW}⚠️ Không có Owner ID nào, bạn có muốn tiếp tục? (y/n): ")
                if confirm.lower() != 'y':
                    return
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
        if not modules:
            print(f"{Fore.RED}❌ Không có module hợp lệ nào được tải. Dừng chương trình.")
            return
        else:
            print(f"{Fore.CYAN}📦 Đã load xong các module hợp lệ.\n🤖 Bot By Nguyễn Quang Huy Dzi - Online 🌐")

        fb_tools = fbTools(facebook_data)
        success = fb_tools.getAllThreadList()
        if not success:
            print(f"{Fore.RED}❌ Không thể lấy danh sách thread. Thoát chương trình...")
            return

        thread_list = fb_tools.getListThreadID()
        if isinstance(thread_list, dict) and "ERR" in thread_list:
            print(f"{Fore.RED}❌ Lỗi: {thread_list['ERR']}")
            return

        listener = listeningEvent(fb_tools, facebook_data, fb, modules, prefix, owner_ids)
        listener.get_last_seq_id()

        if listener.lastSeqID:
            try:
                listener.connect_mqtt()
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}🛑 Đã dừng chương trình.")
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi kết nối MQTT: {e}")
        else:
            print(f"{Fore.RED}❌ Không thể bắt đầu theo dõi vì thiếu Sequence ID. Kiểm tra lại cookie hoặc kết nối mạng.")

    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi không xác định: {e}")

if __name__ == "__main__":
    main()