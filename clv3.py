import multiprocessing
import time
import random
import os
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.box import DOUBLE
from rich.table import Table
from zlapi import ZaloAPI, ZaloAPIException, Message, Mention, MultiMention, ThreadType

console = Console()

def console_print(text, style="white"):
    console.print(text, style=style)

def create_main_banner():
    banner = Text(justify="center")
    banner.append("""
░█████╗░███████╗░██████╗██╗░░██╗
██╔══██╗██╔════╝██╔════╝██║░░██║
███████║█████╗░░╚█████╗░███████║
██╔══██║██╔══╝░░░╚═══██╗██╔══██║
██║░░██║███████╗██████╔╝██║░░██║
╚═╝░░╚═╝╚══════╝╚═════╝░╚═╝░░╚═╝
░█████╗░███████╗██╗░░██╗███╗░░░███╗
██╔══██╗██╔════╝██║░░██║████╗░████║
███████║█████╗░░███████║██╔████╔██║
██╔══██║██╔══╝░░██╔══██║██║╚██╔╝██║
██║░░██║███████╗██║░░██║██║░╚═╝░██║
╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░░░░╚═╝
""", style="cyan")
    banner.append("\n🌟 TOOL NHÂY TAG ZALO BY NG QUANG HUY 🌟\n", style="magenta")
    banner.append("👑 Admin: Ng Quang Huy\n", style="magenta")
    banner.append("📱 Thông tin liên hệ:\n", style="blue")
    banner.append("   • Zalo: 0904562214\n", style="cyan")
    banner.append("   • Nhóm Zalo: https://zalo.me/g/fkrvry389\n", style="cyan")
    banner.append("\nℹ️ Phiên bản: v10.8\n", style="cyan")
    banner.append(f"⏰ Thời gian: {time.strftime('%I:%M %p, %d/%m/%Y')}\n", style="blue")
    banner.append("🔄 Cập nhật lần cuối: 04/07/2025\n", style="blue")
    banner.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="cyan")
    banner.append("Mua tool liên hệ dzi!\n", style="cyan")
    banner.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style="cyan")
    return banner

def create_instructions_panel():
    instructions = Text(justify="left")
    instructions.append("🔹 HƯỚNG DẪN SỬ DỤNG TOOL NHÂY TAG 🔹\n", style="bold cyan")
    instructions.append("1️⃣ Nhập số lượng tài khoản Zalo muốn chạy.\n", style="white")
    instructions.append("2️⃣ Nhập IMEI, Cookie cho từng tài khoản.\n", style="white")
    instructions.append("3️⃣ Chọn nhóm và thành viên để tag.\n", style="white")
    instructions.append("4️⃣ Chọn delay cố định hoặc random (Y/N).\n", style="white")
    instructions.append("5️⃣ Nếu random, nhập khoảng delay min và max.\n", style="white")
    instructions.append("6️⃣ Chọn tag nhiều người trong 1 tin nhắn hay từng người (Y/N).\n", style="white")
    instructions.append("7️⃣ Chọn réo ngẫu nhiên hay theo thứ tự (Y/N).\n", style="white")
    instructions.append("8️⃣ Chọn có nhập tên người để chửi không (Y/N).\n", style="white")
    instructions.append("   • Nếu Y, nhập danh sách tên cách nhau bởi dấu phẩy.\n", style="white")
    instructions.append("9️⃣ Chọn có gửi kèm ảnh không (Y/N).\n", style="white")
    instructions.append("   • Nếu Y, nhập thư mục chứa ảnh và số lần réo min/max.\n", style="white")
    instructions.append("📌 Đảm bảo file nhaychet.txt chứa nội dung tag và cookie hợp lệ!\n", style="bold blue")
    return Panel(instructions, title="Hướng Dẫn Sử Dụng", border_style="cyan", box=DOUBLE, width=60, padding=(0, 1))

def read_file_content(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        console_print(f"[❌] Lỗi đọc file {filename}: {e}", style="bold magenta")
        return []

def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(',')]
        return [n for n in numbers if 1 <= n <= max_index]
    except:
        console_print("[❌] Định dạng không hợp lệ!", style="bold magenta")
        return []

def get_image_files(folder_path):
    try:
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    except Exception as e:
        console_print(f"[❌] Lỗi đọc thư mục ảnh {folder_path}: {e}", style="bold magenta")
        return []

class Bot(ZaloAPI):
    def __init__(self, imei, session_cookies, delay_min=0, delay_max=None, tag_multiple=False, tag_random=False, tagged_users=None, target_names=None, anti_expose="n", image_folder="", send_image=False, image_freq_min=1, image_freq_max=1):
        super().__init__('api_key', 'secret_key', imei, session_cookies)
        self.delay_min = delay_min
        self.delay_max = delay_max if delay_max is not None else delay_min
        self.tag_multiple = tag_multiple
        self.tag_random = tag_random
        self.tagged_users = tagged_users or {}
        self.target_names = target_names or []  # Danh sách tên để chửi
        self.anti_expose = anti_expose.lower()  # y or n
        self.image_folder = image_folder
        self.send_image = send_image
        self.image_freq_min = image_freq_min
        self.image_freq_max = image_freq_max
        self.message_lines = read_file_content("nhaychet.txt")
        self.running_flags = {}
        self.processes = {}
        self.tagged_users_internal = {}
        self.message_count = {}  # Đếm số tin nhắn đã gửi cho mỗi thread_id

    def start_spam(self, thread_id, thread_type, tagged_users=None):
        if not self.message_lines:
            console_print("[❌] File nhaychet.txt rỗng hoặc không đọc được!", style="bold magenta")
            return
        if thread_id not in self.running_flags:
            self.running_flags[thread_id] = multiprocessing.Value('b', False)
        if thread_id not in self.processes:
            self.processes[thread_id] = None
        if thread_id not in self.tagged_users_internal:
            self.tagged_users_internal[thread_id] = tagged_users or []
        if thread_id not in self.message_count:
            self.message_count[thread_id] = 0
        if not self.running_flags[thread_id].value:
            self.send(Message(text=""), thread_id, thread_type, ttl=60000)
            self.running_flags[thread_id].value = True
            self.processes[thread_id] = multiprocessing.Process(
                target=self.spam_messages_with_tag,
                args=(thread_id, thread_type, self.running_flags[thread_id])
            )
            self.processes[thread_id].start()

    def spam_messages_with_tag(self, thread_id, thread_type, running_flag):
        user_index = 0
        image_files = get_image_files(self.image_folder) if self.send_image else []
        while running_flag.value and self.tagged_users_internal[thread_id]:
            if not self.message_lines:
                self.message_lines = read_file_content("nhaychet.txt")
                if not self.message_lines:
                    console_print("[❌] File nhaychet.txt rỗng!", style="bold magenta")
                    running_flag.value = False
                    break
            raw_msg = random.choice(self.message_lines)
            target_name = random.choice(self.target_names) if self.target_names else ""
            # Nếu chống lộ = Y, random giữa tag từng người và tag nhiều người
            use_multiple = self.tag_multiple if self.anti_expose != 'y' else random.choice([True, False])
            if use_multiple:
                valid_users = []
                mention_names = []
                users_to_tag = self.tagged_users_internal[thread_id].copy()
                if self.tag_random:
                    random.shuffle(users_to_tag)
                for user_id in users_to_tag:
                    try:
                        user_info = self.fetchUserInfo(user_id)
                        if not user_info or user_id not in user_info.changed_profiles:
                            console_print(f"[⚠️] Thành viên {user_id} không còn trong nhóm!", style="bold blue")
                            continue
                        user_name = user_info.changed_profiles[user_id]['displayName']
                        valid_users.append(user_id)
                        mention_names.append(user_name)
                    except Exception as e:
                        console_print(f"[⚠️] Lỗi lấy thông tin user {user_id}: {e}", style="bold blue")
                        continue
                self.tagged_users_internal[thread_id] = valid_users
                if not self.tagged_users_internal[thread_id]:
                    console_print("[🛑] Không còn thành viên để tag!", style="bold magenta")
                    running_flag.value = False
                    break
                mentions = []
                mention_placeholders = [f"@{i+1}" for i in range(len(mention_names))]
                random.shuffle(mention_placeholders)  # Random thứ tự mention
                msg_parts = [raw_msg]
                if self.anti_expose == 'y' and target_name:
                    msg_parts.append(target_name)
                    if random.choice([True, False]):
                        final_msg = " ".join(mention_placeholders + msg_parts)
                    else:
                        final_msg = " ".join(msg_parts + mention_placeholders)
                else:
                    final_msg = f"{' '.join(mention_placeholders)} {raw_msg}"
                for i, user_name in enumerate(mention_names):
                    placeholder = f"@{i+1}"
                    final_msg = final_msg.replace(placeholder, f"@{user_name}", 1)
                    offset = final_msg.find(f"@{user_name}")
                    mentions.append(Mention(valid_users[i], length=len(f"@{user_name}"), offset=offset, auto_format=False))
                try:
                    self.setTyping(thread_id, thread_type)
                    time.sleep(0.1)
                    message_to_send = Message(text=final_msg.strip(), mention=MultiMention(mentions))
                    self.send(message_to_send, thread_id=thread_id, thread_type=thread_type)
                    self.message_count[thread_id] += 1
                    console_print(f"[✅] Đã gửi tin nhắn tới nhóm {thread_id}", style="bold cyan")
                except Exception as e:
                    console_print(f"[❌] Lỗi gửi tin nhắn: {e}", style="bold magenta")
                    time.sleep(3)
                    continue
            else:
                if self.tag_random:
                    user_id = random.choice(self.tagged_users_internal[thread_id])
                else:
                    user_id = self.tagged_users_internal[thread_id][user_index]
                try:
                    user_info = self.fetchUserInfo(user_id)
                    if not user_info or user_id not in user_info.changed_profiles:
                        console_print(f"[⚠️] Thành viên {user_id} không còn trong nhóm!", style="bold blue")
                        self.tagged_users_internal[thread_id].remove(user_id)
                        if not self.tagged_users_internal[thread_id]:
                            console_print("[🛑] Không còn thành viên để tag!", style="bold magenta")
                            running_flag.value = False
                            break
                        continue
                    user_name = user_info.changed_profiles[user_id]['displayName']
                    if self.anti_expose == 'y' and target_name:
                        if random.choice([True, False]):
                            msg = f"@{user_name} {raw_msg} {target_name}"
                            offset_mention = 0
                        else:
                            msg = f"{target_name} {raw_msg} @{user_name}"
                            offset_mention = len(f"{target_name} {raw_msg} ")
                    else:
                        msg = f"{raw_msg} @{user_name}"
                        offset_mention = len(raw_msg) + 1
                    mention = Mention(user_id, offset=offset_mention, length=len(f"@{user_name}"))
                    self.setTyping(thread_id, thread_type)
                    time.sleep(0.1)
                    self.send(Message(text=msg, mention=mention), thread_id, thread_type)
                    self.message_count[thread_id] += 1
                    
                except Exception as e:
                    console_print(f"[❌] Lỗi gửi tin nhắn: {e}", style="bold magenta")
                    time.sleep(3)
                    continue
                if not self.tag_random:
                    user_index = (user_index + 1) % len(self.tagged_users_internal[thread_id])
            # Gửi ảnh nếu bật tính năng gửi ảnh
            if self.send_image and image_files:
                freq = random.randint(self.image_freq_min, self.image_freq_max)
                if self.message_count[thread_id] >= freq:
                    image_path = random.choice(image_files)
                    try:
                        self.sendLocalImage(
                            thread_id=thread_id,
                            thread_type=thread_type,
                            message=Message(text=""),
                            imagePath=image_path
                        )
                        console_print(f"[🖼️] Đã gửi ảnh {os.path.basename(image_path)} tới nhóm {thread_id}", style="bold cyan")
                        self.message_count[thread_id] = 0  # Reset đếm tin nhắn sau khi gửi ảnh
                    except Exception as e:
                        console_print(f"[❌] Lỗi gửi ảnh {image_path}: {e}", style="bold magenta")
            delay = random.uniform(self.delay_min, self.delay_max)
            console_print(f"[⏳] Delay {delay:.2f} giây", style="bold blue")
            time.sleep(delay)

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
        except Exception as e:
            console_print(f"[❌] Lỗi lấy danh sách nhóm: {e}", style="bold magenta")
            return None

    def fetchGroupMembers(self, group_id):
        try:
            group_info = self.fetchGroupInfo(group_id)
            if not group_info or not hasattr(group_info, 'gridInfoMap') or group_id not in group_info.gridInfoMap:
                console_print(f"[❌] Không lấy được thông tin nhóm {group_id}", style="bold magenta")
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
                    console_print(f"[⚠️] Lỗi lấy thông tin user {user_id}: {e}", style="bold blue")
                    members.append({
                        'id': user_id,
                        'name': f"[Lỗi: {user_id}]"
                    })
            return members
        except Exception as e:
            console_print(f"[❌] Lỗi lấy danh sách thành viên: {e}", style="bold magenta")
            return []

def start_bot_nhaytag(imei, session_cookies, delay_min, delay_max, tag_multiple, tag_random, group_ids, tagged_users, target_names, anti_expose, image_folder, send_image, image_freq_min, image_freq_max):
    bot = Bot(imei, session_cookies, delay_min, delay_max, tag_multiple, tag_random, tagged_users, target_names, anti_expose, image_folder, send_image, image_freq_min, image_freq_max)
    for group_id in group_ids:
        console_print(f"[▶️] Bắt đầu nhây tag nhóm {group_id}", style="bold cyan")
        bot.start_spam(group_id, ThreadType.GROUP, tagged_users.get(group_id, []))
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def start_multiple_accounts():
    while True:
        console.clear()
        console.print(Panel(create_main_banner(), title="Tool Nhây Tag Zalo", border_style="cyan", box=DOUBLE, width=60, padding=(0, 1)))
        console.print(create_instructions_panel())
        try:
            num_accounts = int(Prompt.ask("[💠] Nhập số lượng tài khoản Zalo muốn chạy", default="1"))
        except ValueError:
            console_print("[❌] Nhập sai, phải là số nguyên!", style="bold magenta")
            continue
        processes = []
        for i in range(num_accounts):
            console.print(f"\n[🔹] Nhập thông tin cho tài khoản {i+1} [🔹]", style="bold cyan")
            try:
                imei = Prompt.ask("[📱] Nhập IMEI của Zalo")
                cookie_str = Prompt.ask("[🍪] Nhập Cookie")
                try:
                    session_cookies = eval(cookie_str)
                    if not isinstance(session_cookies, dict):
                        console_print("[❌] Cookie phải là dictionary!", style="bold magenta")
                        continue
                except:
                    console_print("[❌] Cookie không hợp lệ, dùng dạng {'key': 'value'}!", style="bold magenta")
                    continue
                bot = Bot(imei, session_cookies)
                groups = bot.fetch_groups()
                if not groups or not hasattr(groups, 'groups') or not groups.groups:
                    console_print("[⚠️] Không lấy được nhóm nào!", style="bold blue")
                    continue
                table = Table(show_header=True, header_style="bold cyan", show_lines=False, box=None)
                table.add_column("STT", width=5, justify="center", style="white")
                table.add_column("Tên nhóm", width=25, justify="left", style="bold cyan")
                table.add_column("ID nhóm", width=15, justify="left", style="blue")
                for idx, group in enumerate(groups.groups, 1):
                    table.add_row(str(idx), group.name, str(group.grid))
                console.print(Panel(table, title="[bold cyan]📋 Danh sách nhóm[/bold cyan]", border_style="cyan", width=60, padding=(0, 1)))
                raw = Prompt.ask("[🔸] Nhập số nhóm muốn chạy (VD: 1,3)", default="")
                selected = parse_selection(raw, len(groups.groups))
                if not selected:
                    console_print("[⚠️] Không chọn nhóm nào!", style="bold blue")
                    continue
                selected_ids = [groups.groups[i - 1].grid for i in selected]
                delay_type = Prompt.ask("[⏳] Delay cố định hay random? (Y/N)", default="N").lower()
                if delay_type == 'y':
                    while True:
                        try:
                            delay_min = float(Prompt.ask("[⏳] Nhập delay ít nhất (giây)", default="0"))
                            if delay_min < 0:
                                console_print("[❌] Delay min phải không âm!", style="bold magenta")
                                continue
                            break
                        except ValueError:
                            console_print("[❌] Delay min phải là số!", style="bold magenta")
                    while True:
                        try:
                            delay_max = float(Prompt.ask("[⏳] Nhập delay nhiều nhất (giây)", default="5"))
                            if delay_max < delay_min:
                                console_print("[❌] Delay max phải lớn hơn hoặc bằng delay min!", style="bold magenta")
                                continue
                            break
                        except ValueError:
                            console_print("[❌] Delay max phải là số!", style="bold magenta")
                else:
                    while True:
                        try:
                            delay_min = float(Prompt.ask("[⏳] Nhập delay cố định (giây)", default="5"))
                            if delay_min < 0:
                                console_print("[❌] Delay phải không âm!", style="bold magenta")
                                continue
                            break
                        except ValueError:
                            console_print("[❌] Delay phải là số!", style="bold magenta")
                    delay_max = delay_min
                tag_multiple = Prompt.ask("[🏷] Tag nhiều người trong 1 tin nhắn hay từng người? (Y/N)", default="Y").lower() == 'y'
                tag_random = Prompt.ask("[🔀] Réo ngẫu nhiên hay theo thứ tự? (Y/N)", default="N").lower() == 'y'
                use_target_name = Prompt.ask("[🔹] Có nhập tên người để chửi không? (Y/N)", default="N").lower()
                if use_target_name == 'y':
                    target_names = Prompt.ask("[🔹] Nhập danh sách tên (VD: DUY K11,NamK12)", default="").split(',')
                    target_names = [name.strip() for name in target_names if name.strip()]
                    if not target_names:
                        console_print("[❌] Danh sách tên rỗng!", style="bold magenta")
                        continue
                else:
                    target_names = []
                anti_expose = Prompt.ask("[🔒] Bật chống lộ? (Y/N)", default="N").lower()
                if anti_expose not in ['y', 'n']:
                    console_print("[❌] Vui lòng nhập Y hoặc N!", style="bold magenta")
                    continue
                send_image = Prompt.ask("[🖼️] Có gửi kèm ảnh không? (Y/N)", default="N").lower() == 'y'
                image_folder = ""
                image_freq_min = 1
                image_freq_max = 1
                if send_image:
                    image_folder = Prompt.ask("[📁] Nhập đường dẫn thư mục chứa ảnh")
                    if not os.path.isdir(image_folder):
                        console_print("[❌] Thư mục không tồn tại!", style="bold magenta")
                        continue
                    while True:
                        try:
                            image_freq_min = int(Prompt.ask("[📸] Nhập số lần réo ít nhất trước khi gửi ảnh", default="1"))
                            if image_freq_min < 1:
                                console_print("[❌] Số lần réo min phải lớn hơn 0!", style="bold magenta")
                                continue
                            break
                        except ValueError:
                            console_print("[❌] Số lần réo min phải là số nguyên!", style="bold magenta")
                    while True:
                        try:
                            image_freq_max = int(Prompt.ask("[📸] Nhập số lần réo nhiều nhất trước khi gửi ảnh", default=str(image_freq_min)))
                            if image_freq_max < image_freq_min:
                                console_print("[❌] Số lần réo max phải lớn hơn hoặc bằng min!", style="bold magenta")
                                continue
                            break
                        except ValueError:
                            console_print("[❌] Số lần réo max phải là số nguyên!", style="bold magenta")
                tagged_users = {}
                for group_id in selected_ids:
                    members = bot.fetchGroupMembers(group_id)
                    if not members:
                        console_print(f"[⚠️] Nhóm {group_id} không có thành viên!", style="bold blue")
                        continue
                    table = Table(show_header=True, header_style="bold cyan", show_lines=False, box=None)
                    table.add_column("STT", width=5, justify="center", style="white")
                    table.add_column("Tên thành viên", width=25, justify="left", style="bold cyan")
                    table.add_column("ID", width=15, justify="left", style="blue")
                    for idx, member in enumerate(members, 1):
                        table.add_row(str(idx), member['name'], member['id'])
                    console.print(Panel(table, title=f"[bold cyan]📋 Thành viên nhóm {group_id}[/bold cyan]", border_style="cyan", width=60, padding=(0, 1)))
                    raw = Prompt.ask("[🔸] Nhập số thứ tự thành viên để tag (VD: 1,2,3, 0 để không tag)", default="0")
                    if raw.strip() == "0":
                        tagged_users[group_id] = []
                    else:
                        selected_members = parse_selection(raw, len(members))
                        tagged_users[group_id] = [members[i - 1]['id'] for i in selected_members]
                p = multiprocessing.Process(
                    target=start_bot_nhaytag,
                    args=(imei, session_cookies, delay_min, delay_max, tag_multiple, tag_random, selected_ids, tagged_users, target_names, anti_expose, image_folder, send_image, image_freq_min, image_freq_max)
                )
                processes.append(p)
                p.start()
            except Exception as e:
                console_print(f"[❌] Lỗi nhập liệu: {e}", style="bold magenta")
                continue
        console_print("\n[✅] TẤT CẢ BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG", style="bold cyan")
        while True:
            restart = Prompt.ask("[🔄] Bạn muốn dùng lại tool? (Y/N)", default="N").lower()
            if restart in ['y', 'n']:
                break
            console_print("[❌] Vui lòng nhập Y hoặc N!", style="bold magenta")
        if restart == 'y':
            continue
        else:
            console_print("\n👋 Chào tạm biệt! Cảm ơn bạn đã sử dụng tool!", style="bold magenta")
            break

if __name__ == "__main__":
    start_multiple_accounts()