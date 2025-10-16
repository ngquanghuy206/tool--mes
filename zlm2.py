import multiprocessing
import time
import json
import requests
import os
import random
from zlapi import ZaloAPI, ThreadType, Message, Mention, MultiMsgStyle, MessageStyle

def dzixtool_in(text):
    print(text)

def dzixtool_taobanner():
    banner = """
⠤⣤⣤⣤⣄⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣠⣤⠤⠤⠴⠶⠶⠶⠶
⢠⣤⣤⡄⣤⣤⣤⠄⣀⠉⣉⣙⠒⠤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠴⠘⣉⢡⣤⡤⠐⣶⡆⢶⠀⣶⣶⡦
⣄⢻⣿⣧⠻⠇⠋⠀⠋⠀⢘⣿⢳⣦⣌⠳⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠞⣡⣴⣧⠻⣄⢸⣿⣿⡟⢁⡻⣸⣿⡿⠁
⠈⠃⠙⢿⣧⣙⠶⣿⣿⡷⢘⣡⣿⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣷⣝⡳⠶⠶⠾⣛⣵⡿⠋⠀⠀
⠀⠀⠀⠀⠉⠻⣿⣶⠂⠘⠛⠛⠛⢛⡛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠉⠛⠀⠉⠒⠛⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⢸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢻⡁⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠘⡇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀ ⠀⠀⠀⠿
\n🌟 TOOL ZALO TREO NGÔN BY NG QUANG HUY 🌟
👑 Admin: Ng Quang Huy
📱 Thông tin liên hệ:
   • Facebook: https://www.facebook.com/knamknam.05
   • Zalo: 0868371089
ℹ️ Phiên bản: v10.7
📲 Copyright: Dzi x Tool
⏰ Thời gian: {}
🔄 Cập nhật lần cuối: 15/9/2025
""".format(time.strftime('%I:%M %p, %d/%m/%Y'))
    return banner


def dzixtool_docfile(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        dzixtool_in(f"Lỗi đọc file {filename}: {e}")
        return ""

def dzixtool_layfileanh(directory):
    try:
        supported_extensions = ('.jpg', '.jpeg', '.png', '.gif')
        return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(supported_extensions)]
    except Exception as e:
        dzixtool_in(f"Lỗi đọc thư mục ảnh {directory}: {e}")
        return []

def dzixtool_docurlvideo(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [url.strip() for url in file.readlines() if url.strip()]
    except Exception as e:
        dzixtool_in(f"Lỗi đọc file video {filename}: {e}")
        return []

def dzixtool_phangiai(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(',')]
        return [n for n in numbers if 1 <= n <= max_index]
    except:
        dzixtool_in("Định dạng không hợp lệ!")
        return []

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies, mode="treongon", delay_min=0, message_text="", ttl=None, color_choices=[5], media_type="text", media_source=""):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.mode = mode
        self.delay_min = delay_min
        self.message_text = message_text
        self.ttl = ttl
        self.color_choices = color_choices
        self.media_type = media_type
        self.media_source = media_source
        self.running_flags = {}
        self.processes = {}
        self.last_selected_index = -1
        self.color_map = {
            1: "#db342e",  # Đỏ
            2: "#f27806",  # Cam
            3: "#f7b503",  # Vàng
            4: "#15a85f",  # Xanh lá
            5: "#ffffff",  # Trắng
        }

    def dzixtool_batdauspam(self, thread_id, thread_type, ttl=None):
        if not self.message_text and self.media_type == "text":
            dzixtool_in("Nội dung spam rỗng!")
            return
        if thread_id not in self.running_flags:
            self.running_flags[thread_id] = multiprocessing.Value('b', False)
        if thread_id not in self.processes:
            self.processes[thread_id] = None
        if not self.running_flags[thread_id].value:
            initial_message = ""
            self.send(Message(text=initial_message), thread_id, thread_type, ttl=ttl if ttl is not None else None)
            self.running_flags[thread_id].value = True
            self.processes[thread_id] = multiprocessing.Process(
                target=self.dzixtool_spamtreongon,
                args=(thread_id, thread_type, self.running_flags[thread_id], ttl)
            )
            self.processes[thread_id].start()

    def dzixtool_spamtreongon(self, thread_id, thread_type, running_flag, ttl=None):
        color_index = 0
        while running_flag.value:
            try:
                self.setTyping(thread_id, thread_type)
                time.sleep(4)
                if self.media_type == "image":
                    image_files = dzixtool_layfileanh(self.media_source)
                    if not image_files:
                        dzixtool_in("Không có ảnh nào trong thư mục!")
                        return
                    selected_image = random.choice(image_files)
                    self.sendLocalImage(
                        selected_image,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1920,
                        height=1080,
                        ttl=ttl if ttl is not None else None
                    )
                elif self.media_type == "video":
                    video_urls = dzixtool_docurlvideo(self.media_source)
                    if not video_urls:
                        dzixtool_in("Không có video nào trong file!")
                        return
                    selected_index = random.randint(0, len(video_urls) - 1)
                    while selected_index == self.last_selected_index and len(video_urls) > 1:
                        selected_index = random.randint(0, len(video_urls) - 1)
                    self.last_selected_index = selected_index
                    selected_url = video_urls[selected_index]
                    thumbnail_url = "https://i.imgur.com/5xcfuvJ.jpeg"
                    duration = "100000"
                    self.sendRemoteVideo(
                        selected_url,
                        thumbnail_url,
                        duration=duration,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1920,
                        height=1080,
                        ttl=ttl if ttl is not None else None
                    )
                mention = Mention("-1", length=len(self.message_text), offset=0) if self.message_text else None
                color = self.color_map[self.color_choices[color_index % len(self.color_choices)]]
                if color:
                    style = MultiMsgStyle(
                        [
                            MessageStyle(
                                offset=0,
                                length=1000,
                                style="color",
                                color=color,
                                auto_format=False,
                            ),
                            MessageStyle(
                                offset=0,
                                length=1000,
                                style="font",
                                size="40",
                                auto_format=False
                            ),
                        ]
                    )
                    if ttl is not None:
                        self.send(Message(text=self.message_text, mention=mention, style=style), thread_id=thread_id, thread_type=thread_type, ttl=ttl)
                    else:
                        self.send(Message(text=self.message_text, mention=mention, style=style), thread_id=thread_id, thread_type=thread_type)
                else:
                    if ttl is not None:
                        self.send(Message(text=self.message_text, mention=mention), thread_id=thread_id, thread_type=thread_type, ttl=ttl)
                    else:
                        self.send(Message(text=self.message_text, mention=mention), thread_id=thread_id, thread_type=thread_type)
                color_index += 1
            except Exception as e:
                dzixtool_in(f"Lỗi gửi tin nhắn: {e}")
            time.sleep(self.delay_min)

    def onMessage(self, *args, **kwargs):
        pass

    def onEvent(self, *args, **kwargs):
        pass

    def onAdminMessage(self, *args, **kwargs):
        pass

    def dzixtool_laynhom(self):
        try:
            all_groups = self.fetchAllGroups()
            group_list = []
            for group_id, _ in all_groups.gridVerMap.items():
                group_info = self.fetchGroupInfo(group_id)
                group_name = group_info.gridInfoMap[group_id]["name"]
                group_list.append({
                    'id': group_id,
                    'name': group_name
                })
            return type('GroupObj', (), {'groups': [type('GroupItem', (), {'grid': g['id'], 'name': g['name']})() for g in group_list]})()
        except AttributeError as e:
            dzixtool_in(f"Lỗi: Phương thức hoặc thuộc tính không tồn tại: {e}")
            return None
        except ZaloAPIException as e:
            dzixtool_in(f"Lỗi API Zalo: {e}")
            return None
        except Exception as e:
            dzixtool_in(f"Lỗi không xác định khi lấy danh sách nhóm: {e}")
            return None

def dzixtool_batdaubot(api_key, secret_key, imei, session_cookies, message_text, delay, group_ids, ttl=None, color_choices=[5], media_type="text", media_source=""):
    bot = Bot(api_key, secret_key, imei, session_cookies, mode="treongon", delay_min=delay, message_text=message_text, ttl=ttl, color_choices=color_choices, media_type=media_type, media_source=media_source)
    for group_id in group_ids:
        dzixtool_in(f"Bắt đầu treo ngôn nhóm {group_id}")
        bot.dzixtool_batdauspam(group_id, ThreadType.GROUP, ttl=ttl)
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def dzixtool_nhieutaikhoan():
    while True:
        print(dzixtool_taobanner())
        try:
            num_accounts = int(input("💠 Nhập số lượng tài khoản Zalo muốn chạy: "))
        except ValueError:
            dzixtool_in("Nhập sai, phải là số nguyên!")
            return
        processes = []
        for i in range(num_accounts):
            print(f"\nNhập thông tin cho tài khoản {i+1}")
            try:
                imei = input("📱 Nhập IMEI của Zalo: ")
                cookie_str = input("🍪 Nhập Cookie: ")
                try:
                    session_cookies = eval(cookie_str)
                    if not isinstance(session_cookies, dict):
                        dzixtool_in("Cookie phải là dictionary!")
                        continue
                except:
                    dzixtool_in("Cookie không hợp lệ, dùng dạng {'key': 'value'}!")
                    continue
                bot = Bot('api_key', 'secret_key', imei, session_cookies, mode="treongon")
                groups = bot.dzixtool_laynhom()
                if not groups or not hasattr(groups, 'groups') or not groups.groups:
                    dzixtool_in("Không lấy được nhóm nào!")
                    continue
                print("\nDanh sách nhóm:")
                for idx, group in enumerate(groups.groups, 1):
                    print(f"{idx}. {group.name} (ID: {group.grid})")
                raw = input("🔸 Nhập số nhóm muốn chạy (VD: 1,3): ")
                selected = dzixtool_phangiai(raw, len(groups.groups))
                if not selected:
                    dzixtool_in("Không chọn nhóm nào!")
                    continue
                selected_ids = [groups.groups[i - 1].grid for i in selected]
                file_txt = input("📂 Nhập tên file .txt chứa nội dung spam: ")
                message_text = dzixtool_docfile(file_txt)
                while True:
                    try:
                        delay = float(input("⏳ Nhập delay giữa các lần gửi (giây): "))
                        if delay < 0:
                            dzixtool_in("Delay phải không âm!")
                            continue
                        break
                    except ValueError:
                        dzixtool_in("Delay phải là số!")
                ttl = None
                while True:
                    ttl_choice = input("⏰ Bật thời gian tự hủy tin nhắn (TTL)? (Y/N): ").lower()
                    if ttl_choice in ['y', 'n']:
                        break
                    dzixtool_in("Vui lòng nhập Y hoặc N!")
                if ttl_choice == 'y':
                    while True:
                        try:
                            ttl_seconds = float(input("⏰ Nhập thời gian tự hủy (giây): "))
                            if ttl_seconds <= 0:
                                dzixtool_in("Thời gian TTL phải lớn hơn 0!")
                                continue
                            ttl = int(ttl_seconds * 1000)
                            break
                        except ValueError:
                            dzixtool_in("Thời gian TTL phải là số!")
                while True:
                    color_choice = input("🎨 Chọn màu tin nhắn (VD: 1,2,3): ")
                    color_choices = dzixtool_phangiai(color_choice, 5)
                    if color_choices:
                        break
                    dzixtool_in("Vui lòng nhập số từ 1-5, cách nhau bằng dấu phẩy!")
                while True:
                    media_choice = input("📸 Treo ảnh (Y), video (N), hay chỉ tin nhắn (O)? ").lower()
                    if media_choice in ['y', 'n', 'o']:
                        break
                    dzixtool_in("Vui lòng nhập Y, N hoặc O!")
                media_type = "text"
                media_source = ""
                if media_choice == 'y':
                    media_type = "image"
                    media_source = input("📂 Nhập thư mục chứa ảnh: ")
                    if not os.path.isdir(media_source):
                        dzixtool_in("Thư mục ảnh không hợp lệ!")
                        continue
                elif media_choice == 'n':
                    media_type = "video"
                    media_source = input("📂 Nhập tên file .txt chứa danh sách URL video: ")
                    if not os.path.isfile(media_source):
                        dzixtool_in("File video không hợp lệ!")
                        continue
                p = multiprocessing.Process(
                    target=dzixtool_batdaubot,
                    args=('api_key', 'secret_key', imei, session_cookies, message_text, delay, selected_ids, ttl, color_choices, media_type, media_source)
                )
                processes.append(p)
                p.start()
            except Exception as e:
                dzixtool_in(f"Lỗi nhập liệu: {e}")
                continue
        dzixtool_in("\nTẤT CẢ ACCOUNT ĐÃ KHỞI ĐỘNG THÀNH CÔNG")
        while True:
            restart = input("🔄 Bạn muốn dùng lại tool? (Y/N): ").lower()
            if restart in ['y', 'n']:
                break
            dzixtool_in("Vui lòng nhập Y hoặc N!")
        if restart == 'y':
            continue
        else:
            dzixtool_in("\n👋 Chào tạm biệt! Cảm ơn bạn đã sử dụng tool của Ng Quang Huy!")
            break

if __name__ == "__main__":
    dzixtool_nhieutaikhoan()