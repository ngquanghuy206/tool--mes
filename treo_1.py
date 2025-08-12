import re
import requests
import time
import random


xanh_la = "\033[1;32m"
do = "\033[1;31m"
xanhnhat = "\033[0;36m"
xanh_cyan_dam = "\033[1;36m"
vang = "\033[1;33m"
trang = "\033[0m"

class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            for url in ['https://www.facebook.com', 'https://mbasic.facebook.com', 'https://m.facebook.com']:
                response = requests.get(url, headers=headers)
                match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                if match:
                    self.fb_dtsg = match.group(1)
                    return
            raise Exception("Không tìm thấy fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khởi tạo: {str(e)}")

    def send_message(self, recipient_id, message):
        timestamp = int(time.time() * 1000)
        data = {
            'fb_dtsg': self.fb_dtsg,
            '__user': self.user_id,
            'body': message,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp,
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury'
        }
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            return response.status_code == 200
        except:
            return False

def load_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()  
        if not content.strip():
            raise Exception(f"File {file_path} trống!")
        return content
    except Exception as e:
        raise Exception(f"Lỗi đọc file {file_path}: {str(e)}")

def main():
    print(f"{xanh_la}===TOOL TREO MES BY DZI ==={trang}")
    
    while True:
        cookie_file = input(f"{vang}Nhập đường dẫn file cookies.txt (mỗi dòng một cookie): {trang}").strip()
        try:
            cookies = load_file(cookie_file).splitlines()  
            cookies = [cookie.strip() for cookie in cookies if cookie.strip()]
            if not cookies:
                raise Exception(f"File {cookie_file} trống!")
            print(f"{xanh_la}Đã tải {len(cookies)} cookie từ {cookie_file}{trang}")
            break
        except Exception as e:
            print(f"{do}Lỗi: {str(e)}{trang}")

    while True:
        recipient_id = input(f"{vang}Nhập ID box: {trang}").strip()
        if recipient_id.isdigit():
            break
        print(f"{do}ID box phải là số!{trang}")

    while True:
        message_file = input(f"{vang}Nhập đường dẫn file messages.txt: {trang}").strip()
        try:
            message = load_file(message_file)  
            print(f"{xanh_la}Đã tải nội dung từ {message_file}{trang}")
            break
        except Exception as e:
            print(f"{do}Lỗi: {str(e)}{trang}")

    while True:
        try:
            delay = float(input(f"{vang}Nhập delay giữa các tin nhắn (giây): {trang}").strip())
            if delay <= 0:
                raise ValueError
            break
        except:
            print(f"{do}Delay phải là số dương!{trang}")

    print(f"{xanh_la}Bắt đầu gửi tin nhắn...")

    try:
        while True:
            for cookie in cookies:
                try:
                    messenger = Messenger(cookie)
                    success = messenger.send_message(recipient_id, message)
                    status_text = f"{xanh_la}[THÀNH CÔNG]{trang}" if success else f"{do}[THẤT BẠI]{trang}"
                    print(f"{status_text} {xanhnhat}Cookie {messenger.user_id}{trang} gửi tới box: {xanh_cyan_dam}{recipient_id}{trang} | Nội dung: {vang}{message[:50].replace('\n', ' ')}...{trang}")
                except Exception as e:
                    print(f"{do}[LỖI] Cookie {cookie[:10]}...: {str(e)}{trang}")
                time.sleep(delay)
    except KeyboardInterrupt:
        print(f"{xanh_la}Đã dừng chương trình!{trang}")

if __name__ == "__main__":
    main()