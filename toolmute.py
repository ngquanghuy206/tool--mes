import threading
import time
import concurrent.futures
from zlapi import ZaloAPI, ThreadType, Message, Mention
from zlapi.models import *
from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES, PREFIX, ADMIN

class MuteBot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.muted_users = {}  
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50000000000)  
        self.isMuteLoop = False
        self.delete_counts = {}  

    def fetchGroupInfoList(self):
        try:
            all_groups = self.fetchAllGroups()
            group_list = []
            for group_id in all_groups.gridVerMap:
                group_info = self.fetchGroupInfo(group_id)
                group_name = group_info.gridInfoMap[group_id]["name"]
                group_list.append({'id': group_id, 'name': group_name})
            return group_list
        except Exception:
            return []

    def parse_selection(self, input_str, max_index):
        try:
            numbers = [int(i.strip()) for i in input_str.split(',')]
            return [n for n in numbers if 1 <= n <= max_index]
        except ValueError:
            print("[❌] Định dạng không hợp lệ! Vui lòng nhập số cách nhau bởi dấu phẩy.")
            return []

    def select_groups(self):
        groups = self.fetchGroupInfoList()
        if not groups:
            print("Không có nhóm nào.")
            return []
        for idx, g in enumerate(groups, 1):
            print(f"{idx}. {g['name']} (ID: {g['id']})")
        while True:
            input_str = input("Chọn các nhóm (cách nhau bởi dấu phẩy, ví dụ: 1,3,5): ").strip()
            selected = self.parse_selection(input_str, len(groups))
            if selected:
                return [groups[i-1]['id'] for i in selected]
            else:
                print("[❌] Lựa chọn không hợp lệ, vui lòng thử lại.")

    def fetchGroupMembers(self, group_id):
        try:
            group_info = self.fetchGroupInfo(group_id)
            if not group_info or group_id not in group_info.gridInfoMap:
                print(f"[❌] Không lấy được thông tin nhóm {group_id}")
                return []
            mem_ver_list = group_info.gridInfoMap[group_id]["memVerList"]
            member_ids = [mem.split("_")[0] for mem in mem_ver_list]
            members = []
            for user_id in member_ids:
                try:
                    user_info = self.fetchUserInfo(user_id)
                    user_data = user_info.changed_profiles.get(user_id, {})
                    members.append({
                        'uid': user_data.get('userId', user_id),
                        'name': user_data.get('displayName', f"[Lỗi: {user_id}]")
                    })
                except Exception as e:
                    print(f"[⚠️] Lỗi lấy thông tin user {user_id}: {e}")
                    members.append({
                        'uid': user_id,
                        'name': f"[Lỗi: {user_id}]"
                    })
            return members
        except Exception as e:
            print(f"[❌] Lỗi lấy danh sách thành viên: {e}")
            return []

    def select_members(self, thread_id):
        try:
            members = self.fetchGroupMembers(thread_id)
            if not members:
                print(f"[❌] Không lấy được danh sách thành viên nhóm {thread_id}")
                return []
            for idx, member in enumerate(members, 1):
                print(f"{idx}. {member['name']} (UID: {member['uid']})")
            input_str = input("Chọn các thành viên để mute (cách nhau bởi dấu phẩy, ví dụ: 1,2,4): ").strip()
            selected = self.parse_selection(input_str, len(members))
            if selected:
                return [members[i-1] for i in selected]
            else:
                print("[❌] Lựa chọn không hợp lệ!")
                return []
        except Exception as e:
            print(f"[❌] Lỗi khi chọn thành viên: {e}")
            return []

    def delete_all_messages(self, thread_id, message_object):
        """Xóa tất cả tin nhắn của những người bị mute trong nhóm"""
        if thread_id not in self.muted_users or not self.muted_users[thread_id]:
            return
        num_to_delete = 50
        try:
            group_data = self.getRecentGroup(thread_id)
            if not group_data or not hasattr(group_data, 'groupMsgs'):
                print(f"[❌] Không có tin nhắn nào để xóa trong nhóm {thread_id}")
                return
            messages_to_delete = [msg for msg in group_data.groupMsgs if str(msg['uidFrom']) in self.muted_users[thread_id]]
            if not messages_to_delete:
                print(f"[❌] Không có tin nhắn nào từ người bị mute trong nhóm {thread_id}")
                return
            if len(messages_to_delete) < num_to_delete:
                num_to_delete = len(messages_to_delete)
            deleted_count = 0
            failed_count = 0
            for i in range(num_to_delete):
                msg = messages_to_delete[-(i + 1)]
                user_id = str(msg['uidFrom']) if msg['uidFrom'] != '0' else None
                if user_id:
                    try:
                        deleted_msg = self.deleteGroupMsg(msg['msgId'], user_id, msg['cliMsgId'], thread_id)
                        if deleted_msg.status == 0:
                            deleted_count += 1
                        else:
                            failed_count += 1
                            print(f"[❌] Không thể xóa tin nhắn {msg['msgId']} trong nhóm {thread_id}. Trạng thái: {deleted_msg.status}")
                    except Exception as e:
                        failed_count += 1
                        print(f"[❌] Lỗi khi xóa tin nhắn {msg['msgId']} trong nhóm {thread_id}: {str(e)}")
            print(f"[✅] Đã xóa {deleted_count} tin nhắn, thất bại {failed_count} tin nhắn trong nhóm {thread_id}")
        except Exception as e:
            print(f"[❌] Lỗi khi lấy tin nhắn nhóm {thread_id}: {str(e)}")

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        if thread_id in self.muted_users and author_id in self.muted_users[thread_id]:
            try:
                media_types = {2, 3, 4, 5, 6}
                if hasattr(message_object, "msgType") and message_object.msgType not in media_types:
                    
                    self.executor.submit(self._delete_message, message_object.msgId, message_object.cliMsgId, author_id, thread_id)
                    
                    self.delete_counts[thread_id] = self.delete_counts.get(thread_id, 0) + 1
                    if self.delete_counts[thread_id] >= 1:
                        print(f"[ℹ️] Đã xóa 1 tin nhắn, bắt đầu xóa toàn bộ tin nhắn của người bị mute trong nhóm {thread_id}")
                        self.executor.submit(self.delete_all_messages, thread_id, message_object)
                        self.delete_counts[thread_id] = 0  
            except Exception as e:
                print(f"[❌] Lỗi khi xử lý tin nhắn: {e}")

    def _delete_message(self, msgId, cliMsgId, ownerId, groupId):
        try:
            self.deleteGroupMsg(
                msgId=msgId,
                clientMsgId=cliMsgId,
                ownerId=ownerId,
                groupId=groupId
            )
            print(f"[✅] Đã xóa tin nhắn {msgId} của user {ownerId} trong nhóm {groupId}")
        except Exception as e:
            print(f"[❌] Lỗi khi xóa tin nhắn {msgId}: {e}")

    def mute_members(self, thread_id, members):
        if thread_id not in self.muted_users:
            self.muted_users[thread_id] = set()
            self.delete_counts[thread_id] = 0  
        for member in members:
            self.muted_users[thread_id].add(member["uid"])
            print(f"Đã mute vĩnh viễn: {member['name']} (UID: {member['uid']}) trong nhóm {thread_id}")

    def start_mute_loop(self):
        if not self.isMuteLoop:
            self.isMuteLoop = True
            print("[ℹ️] Bắt đầu theo dõi tất cả các nhóm và mute nó...")
            self.listen(run_forever=True, thread=False, delay=0.1, type='requests')  # Delay 0.1s để theo dõi nhanh nhất

def run_tool():
    bot = MuteBot(API_KEY, SECRET_KEY, imei=IMEI, session_cookies=SESSION_COOKIES)
    thread_ids = bot.select_groups()
    if not thread_ids:
        print("[❌] Không chọn được nhóm, thoát chương trình.")
        return
    for thread_id in thread_ids:
        while True:
            members = bot.select_members(thread_id)
            if members:
                bot.mute_members(thread_id, members)
            continue_choice = input(f"Bạn muốn tiếp tục mute thành viên khác trong nhóm {thread_id}? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
    bot.start_mute_loop()

if __name__ == "__main__":
    run_tool()