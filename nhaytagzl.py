import multiprocessing
import time
import json
import requests
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.box import DOUBLE
from rich.table import Table
from zlapi import *
from zlapi.models import *


console = Console()

def create_main_banner():
    banner = Text(justify="center")
    banner.append("""
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
░░░╚═╝░░░░╚════╝░░╚════╝░╚══════╝
""", style="cyan")
    banner.append("\n🌟 TOOL ZALO NHÂY TAG BY NG QUANG HUY 🌟\n", style="magenta")
    banner.append("👑 Admin: Ng Quang Huy\n", style="magenta")
    banner.append("📱 Thông tin liên hệ:\n", style="yellow")
    banner.append("   • Facebook: https://www.facebook.com/voidloveosutsuki\n", style="cyan")
    banner.append("   • Zalo: 0868371089\n", style="cyan")
    banner.append("   • Group Zalo: https://zalo.me/g/fkrvry389\n", style="cyan")
    banner.append("\nℹ️ Phiên bản: V8.26\n", style="green")
    banner.append(f"⏰ Thời gian: {time.strftime('%I:%M %p, %d/%m/%Y')}\n", style="green")
    banner.append("🔄 Cập nhật lần cuối: 07/06/2025\n", style="yellow")
    banner.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="cyan")
    banner.append("✅ Dịch vụ hot war chỉ từ 50k, ib ngay nhé!\n", style="green")
    banner.append("🚀 Chúc bạn nhây tag vui vẻ!\n", style="green")
    banner.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style="cyan")
    return banner

def create_instructions_panel():
    instructions = Text(justify="left")
    instructions.append("🔹 HƯỚNG DẪN SỬ DỤNG TOOL NHÂY TAG 🔹\n", style="bold cyan")
    instructions.append("1️⃣ Nhập key xác thực từ web để đăng nhập.\n", style="white")
    instructions.append("2️⃣ Nhập số lượng tài khoản Zalo muốn chạy.\n", style="white")
    instructions.append("3️⃣ Nhập IMEI, Cookie cho từng tài khoản.\n", style="white")
    instructions.append("4️⃣ Nhập delay giữa các tin nhắn (giây).\n", style="white")
    instructions.append("5️⃣ Chọn nhóm từ danh sách để nhây tag (VD: 1,3).\n", style="white")
    instructions.append("6️⃣ Chọn thành viên để tag (VD: 1,2,3 hoặc 0 để không tag).\n", style="white")
    instructions.append("✅ Bot sẽ tự động nhây tag với nội dung từ nhaychet.txt, tag nhiều người trong cùng một tin nhắn.\n", style="bold green")
    instructions.append("⚠️ Lưu ý: Đảm bảo file nhaychet.txt và cookie hợp lệ!\n", style="bold yellow")
    return Panel(instructions, title="Hướng Dẫn Sử Dụng", border_style="green", box=DOUBLE, width=50, padding=(0, 1))

        

import random

def read_file_content(filename="nhaychet.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"❌ Lỗi đọc file {filename}: {e}", style="bold red")
        return []
def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(',')]
        return [n for n in numbers if 1 <= n <= max_index]
    except:
        print("❌ Định dạng không hợp lệ!", style="bold red")
        return []

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies, delay):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.delay = delay
        self.running_flags = {}
        self.processes = {}
        self.tagged_users = {}
        self.message_lines = read_file_content()

    def start_spam(self, thread_id, thread_type, tagged_users):
        if not self.message_lines:
            print("❌ File nhaychet.txt rỗng hoặc không đọc được!", style="bold red")
            return
        if thread_id not in self.running_flags:
            self.running_flags[thread_id] = multiprocessing.Value('b', False)
        if thread_id not in self.processes:
            self.processes[thread_id] = None
        if thread_id not in self.tagged_users:
            self.tagged_users[thread_id] = tagged_users
        if not self.running_flags[thread_id].value:
            self.send(Message(text="""
"""), thread_id, thread_type, ttl=60000)
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
                    print("❌ File nhaychet.txt rỗng!", style="bold red")
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
                        print(f"[⚠️] Thành viên {user_id} không còn trong nhóm, loại bỏ!", style="bold yellow")
                        continue
                    user_name = user_info.changed_profiles[user_id]['displayName']
                    msg += "@Member "
                    mention_names.append(user_name)
                    valid_users.append(user_id)
                except Exception as e:
                    print(f"[⚠️] Lỗi khi lấy thông tin user {user_id}: {e}", style="bold yellow")
                    continue
            self.tagged_users[thread_id] = valid_users
            if not self.tagged_users[thread_id]:
                print("[🛑] Không còn thành viên để tag, dừng bot!", style="bold red")
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
                time.sleep(4)
                message_to_send = Message(text=final_msg.strip(), mention=MultiMention(mentions))
                self.send(message_to_send, thread_id=thread_id, thread_type=thread_type)
                print(f"[✅] Đã gửi tin nhắn tới nhóm {thread_id}: {final_msg[:30]}...", style="bold green")
            except Exception as e:
                print(f"[❌] Lỗi gửi tin nhắn: {e}", style="bold red")
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
            print(f"❌ Lỗi: Phương thức hoặc thuộc tính không tồn tại: {e}", style="bold red")
            return None
        except ZaloAPIException as e:
            print(f"❌ Lỗi API Zalo: {e}", style="bold red")
            return None
        except Exception as e:
            print(f"❌ Lỗi không xác định khi lấy danh sách nhóm: {e}", style="bold red")
            return None

    def fetchGroupInfo(self, group_id):
        try:
            return super().fetchGroupInfo(group_id)
        except ZaloAPIException as e:
            print(f"❌ Lỗi API Zalo khi lấy thông tin nhóm {group_id}: {e}", style="bold red")
            return None
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin nhóm {group_id}: {e}", style="bold red")
            return None

    def fetchGroupMembers(self, group_id):
        try:
            group_info = self.fetchGroupInfo(group_id)
            if not group_info or not hasattr(group_info, 'gridInfoMap') or group_id not in group_info.gridInfoMap:
                print(f"❌ Không lấy được thông tin nhóm {group_id}", style="bold red")
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
                    print(f"⚠️ Lỗi khi lấy thông tin user {user_id}: {e}", style="bold yellow")
                    members.append({
                        'id': user_id,
                        'name': f"[Lỗi: {user_id}]"
                    })
            return members
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách thành viên: {e}", style="bold red")
            return []

def start_bot(api_key, secret_key, imei, session_cookies, delay, group_ids, tagged_users):
    bot = Bot(api_key, secret_key, imei, session_cookies, delay)
    for group_id in group_ids:
        print(f"▶️ Bắt đầu nhây tag nhóm {group_id}", style="bold cyan")
        bot.start_spam(group_id, ThreadType.GROUP, tagged_users.get(group_id, []))
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def start_multiple_accounts():
    console.clear()
    console.print(Panel(create_main_banner(), title="Tool Nhây Tag V8", border_style="cyan", box=DOUBLE, width=60, padding=(0, 1)))
    console.print(create_instructions_panel())
    try:
        num_accounts = int(Prompt.ask("💠 Nhập số lượng tài khoản Zalo muốn chạy", default="1"))
    except ValueError:
        print("❌ Nhập sai, phải là số nguyên!", style="bold red")
        return
    processes = []
    for i in range(num_accounts):
        console.print(f"\n🔹 Nhập thông tin cho tài khoản {i+1} 🔹", style="bold cyan")
        try:
            imei = Prompt.ask("📱 Nhập IMEI của Zalo")
            cookie_str = Prompt.ask("🍪 Nhập Cookie")
            try:
                session_cookies = eval(cookie_str)
                if not isinstance(session_cookies, dict):
                    print("❌ Cookie phải là dictionary!", style="bold red")
                    continue
            except:
                print("❌ Cookie không hợp lệ, dùng dạng {'key': 'value'}!", style="bold red")
                continue
            delay = int(Prompt.ask("⏳ Nhập delay giữa các lần gửi (giây)", default="5"))
            bot = Bot('api_key', 'secret_key', imei, session_cookies, delay)
            groups = bot.fetch_groups()
            if not groups or not hasattr(groups, 'groups') or not groups.groups:
                print("⚠️ Không lấy được nhóm nào!", style="bold red")
                continue
            table = Table(show_header=True, header_style="bold cyan", show_lines=False, box=None)
            table.add_column("STT", width=5, justify="center", style="white")
            table.add_column("Tên nhóm", width=25, justify="left", style="bold green")
            table.add_column("ID nhóm", width=15, justify="left", style="cyan")
            for idx, group in enumerate(groups.groups, 1):
                table.add_row(str(idx), group.name, str(group.grid))
            console.print(Panel(table, title="[bold cyan]📋 Danh sách nhóm[/bold cyan]", border_style="bold cyan", width=50, padding=(0, 1)))
            raw = Prompt.ask("🔸 Nhập số nhóm muốn nhây tag (VD: 1,3)", default="")
            selected = parse_selection(raw, len(groups.groups))
            if not selected:
                print("⚠️ Không chọn nhóm nào!", style="bold red")
                continue
            selected_ids = [groups.groups[i - 1].grid for i in selected]
            tagged_users = {}
            for group_id in selected_ids:
                members = bot.fetchGroupMembers(group_id)
                if not members:
                    print(f"⚠️ Nhóm {group_id} không có thành viên!", style="bold red")
                    continue
                table = Table(show_header=True, header_style="bold cyan", show_lines=False, box=None)
                table.add_column("STT", width=5, justify="center", style="white")
                table.add_column("Tên thành viên", width=25, justify="left", style="bold green")
                table.add_column("ID", width=15, justify="left", style="cyan")
                for idx, member in enumerate(members, 1):
                    table.add_row(str(idx), member['name'], member['id'])
                console.print(Panel(table, title=f"[bold cyan]📋 Thành viên nhóm {group_id}[/bold cyan]", border_style="bold cyan", width=50, padding=(0, 1)))
                raw = Prompt.ask("🔸 Nhập số thứ tự thành viên để tag (VD: 1,2,3, 0 để không tag)", default="0")
                if raw.strip() == "0":
                    tagged_users[group_id] = []
                else:
                    selected_members = parse_selection(raw, len(members))
                    tagged_users[group_id] = [members[i - 1]['id'] for i in selected_members]
            p = multiprocessing.Process(
                target=start_bot,
                args=('api_key', 'secret_key', imei, session_cookies, delay, selected_ids, tagged_users))
            processes.append(p)
            p.start()
        except ValueError:
            print("❌ Delay phải là số nguyên!", style="bold red")
            continue
        except Exception as e:
            print(f"❌ Lỗi nhập liệu: {e}", style="bold red")
            continue
    print("\n✅ TẤT CẢ BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG", style="bold green")

if __name__ == "__main__":
    start_multiple_accounts()