import re
import requests
import time

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
    print("=== TOOL TREO MES BY DZI ===")

    while True:
        cookie_file = input("Nhập đường dẫn file cookies.txt (mỗi dòng một cookie): ").strip()
        try:
            cookies = load_file(cookie_file).splitlines()
            cookies = [cookie.strip() for cookie in cookies if cookie.strip()]
            if not cookies:
                raise Exception(f"File {cookie_file} trống!")
            print(f"Đã tải {len(cookies)} cookie từ {cookie_file}")
            break
        except Exception as e:
            print(f"Lỗi: {str(e)}")

    while True:
        recipient_id = input("Nhập ID box: ").strip()
        if recipient_id.isdigit():
            break
        print("ID box phải là số!")

    while True:
        message_file = input("Nhập đường dẫn file messages.txt: ").strip()
        try:
            message = load_file(message_file)
            print(f"Đã tải nội dung từ {message_file}")
            break
        except Exception as e:
            print(f"Lỗi: {str(e)}")

    while True:
        try:
            delay = float(input("Nhập delay giữa các tin nhắn (giây): ").strip())
            if delay <= 0:
                raise ValueError
            break
        except:
            print("Delay phải là số dương!")

    print("Bắt đầu gửi tin nhắn...")

    try:
        while True:
            for cookie in cookies:
                try:
                    messenger = Messenger(cookie)
                    success = messenger.send_message(recipient_id, message)
                    if success:
                        print("[THÀNH CÔNG]")
                    else:
                        print("[THẤT BẠI]")
                except Exception as e:
                    print(f"[LỖI] Cookie {cookie[:10]}...: {str(e)}")
                time.sleep(delay)
    except KeyboardInterrupt:
        print("Đã dừng chương trình!")


if __name__ == "__main__":
    main()
