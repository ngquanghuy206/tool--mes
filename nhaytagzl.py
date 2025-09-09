import multiprocessing
import time
import json
import requests
from zlapi import ZaloAPI, ThreadType, Message, ZaloAPIException
from zlapi.models import Message, Mention, MultiMention

def create_main_banner():
    banner = f"""
██╗░░░░░░█████╗░░██████╗░██╗███╗░░██╗
██║░░░░░██╔══██╗██╔════╝░██║████╗░██║
██║░░░░░██║░░██║██║░░██╗░██║██╔██╗██║
██║░░░░░██║░░██║██║░░╚██╗██║██║╚████║
███████╗╚█████╔╝╚██████╔╝██║██║░╚███║
╚══════╝░╚════╝░░╚═════╝░╚═╝╚═╝░░╚══╝

████████╗░█████╗░░█████╗░██╗░░░░░
╚══██╔══╝██╔══██╗██╔══██╗██║░░░░░
░░░██║░░░██║░░██║██║░░██║██║░░░░░
░░░██║░░░██║░░██║██║░░██║██║░░░░░
░░░██║░░░╚█████╔╝╚█████╔╝███████╗
░░░╚═╝░░░░╚════╝░░╚═════╝░╚══════╝

🌟 TOOL ZALO NHÂY TAG BY NG QUANG HUY 🌟
👑 Admin: Ng Quang Huy
📱 Thông tin liên hệ:
   • Facebook: https://www.facebook.com/voidloveosutsuki
   • Zalo: 0868371089
   • Group Zalo: https://zalo.me/g/fkrvry389
ℹ️ Phiên bản: V8.26
⏰ Thời gian: {time.strftime('%I:%M %p, %d/%m/%Y')}
🔄 Cập nhật lần cuối: 07/06/2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Dịch vụ hot war chỉ từ 50k, ib dzi ngay nhé!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return banner

def create_instructions_panel():
    instructions = """🔹 HƯỚNG DẪN SỬ DỤNG TOOL NHÂY TAG 🔹
1️⃣ Nhập key xác thực từ web để đăng nhập.
2️⃣ Nhập số lượng tài khoản Zalo muốn chạy.
3️⃣ Nhập IMEI, Cookie cho từng tài khoản.
4️⃣ Nhập delay giữa các tin nhắn (giây).
5️⃣ Chọn nhóm từ danh sách để nhây tag (VD: 1,3).
6️⃣ Chọn thành viên để tag (VD: 1,2,3 hoặc 0 để không tag).
✅ Bot sẽ tự động nhây tag với nội dung từ nhaychet.txt, tag nhiều người trong cùng một tin nhắn.
⚠️ Lưu ý: Đảm bảo file nhaychet.txt và cookie hợp lệ!
"""
    return instructions

def read_file_content(filename="nhaychet.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"❌ Lỗi đọc file {filename}: {e}")
        return []

def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(',')]
        return [n for n in numbers if 1 <= n <= max_index]
    except:
        print("❌ Định dạng không hợp lệ!")
        return []

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies, delay, ttl=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.delay = delay
        self.ttl = ttl
        self.running_flags = {}
        self.processes = {}
        self.tagged_users = {}
        self.message_lines = read_file_content()

    def start_spam(self, thread_id, thread_type, tagged_users):
        if not self.message_lines:
            print("❌ File nhaychet.txt rỗng hoặc không đọc được!")
            return
        if thread_id not in self.running_flags:
            self.running_flags[thread_id] = multiprocessing.Value('b', False)
        if thread_id not in self.processes:
            self.processes[thread_id] = None
        if thread_id not in self.tagged_users:
            self.tagged_users[thread_id] = tagged_users
        if not self.running_flags[thread_id].value:
            self.send(Message(text=""), thread_id, thread_type, ttl=self.ttl)
            self.running_flags[thread_id].value = True
            self.processes[thread_id] = multiprocessing.Process(
                target=self.spam_messages_with_tag,
                args=(thread_id, thread_type, self.running_flags[thread_id])
            )
            self.processes[thread_id].start()

    def spam_messages_with_tag(self, thread_id, thread_type, running_flag):
        content_index = 0
        while running_flag.value and self.tagged_users[thread_id]:
            if not self.message_lines:
                self.message_lines = read_file_content()
                if not self.message_lines:
                    print("❌ File nhaychet.txt rỗng!")
                    running_flag.value = False
                    break
            raw_msg = self.message_lines[content_index]
            msg = raw_msg + " "
            mentions = []
            valid_users = []
            mention_names = []
            for user_id in self.tagged_users[thread_id]:
                try:
                    user_info = self.fetchUserInfo(user_id)
                    if not user_info or user_id not in user_info.changed_profiles:
                        print(f"[⚠️] Thành viên {user_id} không còn trong nhóm, loại bỏ!")
                        continue
                    user_name = user_info.changed_profiles[user_id]['displayName']
                    msg += "@Member "
                    mention_names.append(user_name)
                    valid_users.append(user_id)
                except Exception as e:
                    print(f"[⚠️] Lỗi khi lấy thông tin user {user_id}: {e}")
                    continue
            self.tagged_users[thread_id] = valid_users
            if not self.tagged_users[thread_id]:
                print("[🛑] Không còn thành viên để tag, dừng bot!")
                running_flag.value = False
                break
            final_msg = msg
            for i, user_name in enumerate(mention_names):
                placeholder = "@Member "
                final_msg = final_msg.replace(placeholder, f"@{user_name} ", 1)
                offset = final_msg.find(f"@{user_name}")
                mentions.append(Mention(valid_users[i], length=len(f"@{user_name}"), offset=offset, auto_format=False))
            try:
                self.setTyping(thread_id, thread_type)
                time.sleep(1)
                message_to_send = Message(text=final_msg.strip(), mention=MultiMention(mentions))
                self.send(message_to_send, thread_id=thread_id, thread_type=thread_type, ttl=self.ttl)
                print(f"[✅] Đã gửi tin nhắn tới nhóm {thread_id}: {final_msg[:30]}...")
            except Exception as e:
                print(f"[❌] Lỗi gửi tin nhắn: {e}")
                time.sleep(3)
                continue
            content_index = (content_index + 1) % len(self.message_lines)
            time.sleep(self.delay)

    def onMessage(self, *args, **kwargs):
        pass

    def onEvent(self, *args, **kwargs):
        pass

    def onAdminMessage(self, *args, **kwargs):
        pass

    def fetch_groups(self):
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
            print(f"❌ Lỗi: Phương thức hoặc thuộc tính không tồn tại: {e}")
            return None
        except ZaloAPIException as e:
            print(f"❌ Lỗi API Zalo: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi không xác định khi lấy danh sách nhóm: {e}")
            return None

    def fetchGroupInfo(self, group_id):
        try:
            return super().fetchGroupInfo(group_id)
        except ZaloAPIException as e:
            print(f"❌ Lỗi API Zalo khi lấy thông tin nhóm {group_id}: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin nhóm {group_id}: {e}")
            return None

    def fetchGroupMembers(self, group_id):
        try:
            group_info = self.fetchGroupInfo(group_id)
            if not group_info or not hasattr(group_info, 'gridInfoMap') or group_id not in group_info.gridInfoMap:
                print(f"❌ Không lấy được thông tin nhóm {group_id}")
                return []
            mem_ver_list = group_info.gridInfoMap[group_id]["memVerList"]
            member_ids = [mem.split("_")[0] for mem in mem_ver_list]
            members = []
            for user_id in member_ids:
                try:
                    user_info = self.fetchUserInfo(user_id)
                    user_data = user_info.changed_profiles[user_id]
                    members.append({
                        'id': user_data['userId'],
                        'name': user_data['displayName']
                    })
                except Exception as e:
                    print(f"⚠️ Lỗi khi lấy thông tin user {user_id}: {e}")
                    members.append({
                        'id': user_id,
                        'name': f"[Lỗi: {user_id}]"
                    })
            return members
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách thành viên: {e}")
            return []

def start_bot(api_key, secret_key, imei, session_cookies, delay, group_ids, tagged_users, ttl=None):
    bot = Bot(api_key, secret_key, imei, session_cookies, delay, ttl)
    for group_id in group_ids:
        print(f"▶️ Bắt đầu nhây tag nhóm {group_id}")
        bot.start_spam(group_id, ThreadType.GROUP, tagged_users.get(group_id, []))
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def start_multiple_accounts():
    print(create_main_banner())
    print(create_instructions_panel())
    try:
        num_accounts = int(input("💠 Nhập số lượng tài khoản Zalo muốn chạy: "))
    except ValueError:
        print("❌ Nhập sai, phải là số nguyên!")
        return
    processes = []
    for i in range(num_accounts):
        print(f"\n🔹 Nhập thông tin cho tài khoản {i+1} 🔹")
        try:
            imei = input("📱 Nhập IMEI của Zalo: ")
            cookie_str = input("🍪 Nhập Cookie: ")
            try:
                session_cookies = eval(cookie_str)
                if not isinstance(session_cookies, dict):
                    print("❌ Cookie phải là dictionary!")
                    continue
            except:
                print("❌ Cookie không hợp lệ, dùng dạng {'key': 'value'}!")
                continue
            delay = int(input("⏳ Nhập delay giữa các lần gửi (giây): "))
            ttl = None
            while True:
                ttl_choice = input("⏰ Bật thời gian tự hủy tin nhắn (TTL)? (Y/N): ").lower()
                if ttl_choice in ['y', 'n']:
                    break
                print("Vui lòng nhập Y hoặc N!")
            if ttl_choice == 'y':
                while True:
                    try:
                        ttl_seconds = float(input("⏰ Nhập thời gian tự hủy (giây): "))
                        if ttl_seconds <= 0:
                            print("Thời gian TTL phải lớn hơn 0!")
                            continue
                        ttl = int(ttl_seconds * 1000)
                        break
                    except ValueError:
                        print("Thời gian TTL phải là số!")
            bot = Bot('api_key', 'secret_key', imei, session_cookies, delay, ttl)
            groups = bot.fetch_groups()
            if not groups or not hasattr(groups, 'groups') or not groups.groups:
                print("⚠️ Không lấy được nhóm nào!")
                continue
            print("\nDanh sách nhóm:")
            for idx, group in enumerate(groups.groups, 1):
                print(f"{idx}. {group.name} (ID: {group.grid})")
            raw = input("🔸 Nhập số nhóm muốn nhây tag (VD: 1,3): ")
            selected = parse_selection(raw, len(groups.groups))
            if not selected:
                print("⚠️ Không chọn nhóm nào!")
                continue
            selected_ids = [groups.groups[i - 1].grid for i in selected]
            tagged_users = {}
            for group_id in selected_ids:
                members = bot.fetchGroupMembers(group_id)
                if not members:
                    print(f"⚠️ Nhóm {group_id} không có thành viên!")
                    continue
                print(f"\nThành viên nhóm {group_id}:")
                for idx, member in enumerate(members, 1):
                    print(f"{idx}. {member['name']} (ID: {member['id']})")
                raw = input("🔸 Nhập số thứ tự thành viên để tag (VD: 1,2,3, 0 để không tag): ")
                if raw.strip() == "0":
                    tagged_users[group_id] = []
                else:
                    selected_members = parse_selection(raw, len(members))
                    tagged_users[group_id] = [members[i - 1]['id'] for i in selected_members]
            p = multiprocessing.Process(
                target=start_bot,
                args=('api_key', 'secret_key', imei, session_cookies, delay, selected_ids, tagged_users, ttl))
            processes.append(p)
            p.start()
        except ValueError:
            print("❌ Delay phải là số nguyên!")
            continue
        except Exception as e:
            print(f"❌ Lỗi nhập liệu: {e}")
            continue
    print("\n✅ TẤT CẢ BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG")

if __name__ == "__main__":
    start_multiple_accounts()