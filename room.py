import requests
import os
import asyncio
import websockets
import json
import random
from concurrent.futures import ThreadPoolExecutor
from pystyle import Colors, Colorate
import sys
import uuid
from datetime import datetime as dt

sys.stdout.reconfigure(encoding='utf-8')
VERSION = 2.3
def clear_screen():
    if os.name == 'nt':  
        os.system('cls')
    else: 
        os.system('clear')

def get_terminal_size():
    try:
        return os.get_terminal_size().columns
    except:
        return 80 
size = get_terminal_size()
def print_main_banner():
    banner = """
██╗░░░░░░█████╗░░██████╗░██╗███╗░░██║
██║░░░░░██╔══██╗██╔════╝░██║████╗░██║
██║░░░░░██║░░██║██║░░██╗░██║██╔██╗██║
██║░░░░░██║░░██║██║░░╚██╗██║██║╚████║
███████╗╚█████╔╝╚██████╔╝██║██║░╚███║
╚══════╝░╚════╝░░╚═════╝░╚═╝╚═╝░░╚══╝       
"""
    border = "═" * 80
    print(Colorate.Horizontal(Colors.rainbow, f"{border}\n{banner}{border}"))
def load_tokens():
    filename = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Nhập tên file chứa token (mặc định: tokens.txt): ")).strip() or "tokens.txt"
    if not os.path.isfile(filename):
        print(Colorate.Horizontal(Colors.rainbow, f"File '{filename}' không tồn tại!"))
        exit()
    with open(filename, "r", encoding="utf-8") as file:
        tokens = [line.strip() for line in file.readlines() if line.strip()]
    if not tokens:
        print(Colorate.Horizontal(Colors.rainbow, "File token trống!"))
        exit()
    return tokens

def get_channel_info(token, channel_id, user_agents):
    url = f"https://discord.com/api/v9/channels/{channel_id}"
    headers = {
        'Authorization': token,
        'User-Agent': random.choice(user_agents),
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            channel_name = data.get('name', 'Không rõ')
            guild_id = data.get('guild_id', None)
            if guild_id:
                guild_url = f"https://discord.com/api/v9/guilds/{guild_id}"
                guild_response = requests.get(guild_url, headers=headers, timeout=10)
                if guild_response.status_code == 200:
                    guild_data = guild_response.json()
                    guild_name = guild_data.get('name', 'Không rõ')
                    return guild_id, channel_name, guild_name
            return guild_id, channel_name, "Không rõ"
        else:
            return None, None, None
    except requests.RequestException:
        return None, None, None

async def send_heartbeat(ws, heartbeat_interval, token):
    while True:
        try:
            await ws.send(json.dumps({"op": 1, "d": None}))
            await asyncio.sleep(heartbeat_interval)
        except Exception:
            break

async def enable_screen_share(ws, token, guild_id, channel_id, session_id):
    screen_share_data = {
        "op": 18,
        "d": {
            "type": "guild",
            "guild_id": guild_id,
            "channel_id": channel_id,
            "preferred_region": None,
            "stream_type": "screen",
            "session_id": session_id,
            "video": False,
            "self_stream": True 
        }
    }
    max_retries = 1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
    retry_delay = 2 
    for attempt in range(max_retries):
        try:
            await ws.send(json.dumps(screen_share_data))
            response = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if response.get("op") == 0:
                print(Colorate.Horizontal(Colors.rainbow, f"[SCREEN-SHARE] Chia sẻ màn hình đã được kích hoạt thành công cho token {token[:10]}..."))
                return True
            else:
                print(Colorate.Horizontal(Colors.rainbow, f"[SCREEN-SHARE] Phản hồi không hợp lệ, thử lại lần {attempt + 1}/{max_retries}"))
        except Exception as e:
            print(Colorate.Horizontal(Colors.rainbow, f"[SCREEN-SHARE] Lỗi khi kích hoạt chia sẻ màn hình: {str(e)}, thử lại lần {attempt + 1}/{max_retries}"))
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2 
            continue
    print(Colorate.Horizontal(Colors.rainbow, f"[SCREEN-SHARE] Không thể kích hoạt chia sẻ màn hình sau {max_retries} lần thử"))
    return False

async def join_voice_channel_async(token, guild_id, channel_id, channel_name, guild_name, self_mute, self_deaf, self_video, self_screen, user_agents):
    url_ws = "wss://gateway.discord.gg/?v=9&encoding=json"
    attempt = 0
    session_id = None

    while True:
        attempt += 1
        try:
            async with websockets.connect(url_ws, ping_interval=None) as ws:
                try:
                    auth_data = {
                        "op": 2,
                        "d": {
                            "token": token,
                            "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"},
                            "compress": False,
                            "large_threshold": 250
                        }
                    }
                    await ws.send(json.dumps(auth_data))
                    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                    if response.get("op") == 10:
                        heartbeat_interval = response["d"]["heartbeat_interval"] / 1000
                        heartbeat_task = asyncio.create_task(send_heartbeat(ws, heartbeat_interval, token))
                    else:
                        raise Exception("Phản hồi WebSocket không hợp lệ")

                    while True:
                        try:
                            response = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                            if response.get("t") == "READY":
                                session_id = response["d"]["session_id"]
                                break
                        except asyncio.TimeoutError:
                            continue

                    if not session_id:
                        raise Exception("Không thể lấy session_id từ Discord")
                    await asyncio.sleep(1)

                    voice_state_data = {
                        "op": 4,
                        "d": {
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "self_mute": self_mute,
                            "self_deaf": self_deaf,
                            "self_video": self_video 
                        }
                    }
                    await ws.send(json.dumps(voice_state_data))
                    status_message = f"[VOICE-STATUS] Token: {token[:10]}... | Server: {guild_name} | Channel: {channel_name} | Status: Successfully | Code: 200 | Mic: {'Off' if self_mute else 'On'} | Loa: {'Off' if self_deaf else 'On'} | Camera: {'On' if self_video else 'Off'} | Screen: {'On' if self_screen else 'Off'}"
                    if self_screen:
                        success = await enable_screen_share(ws, token, guild_id, channel_id, session_id)
                        if not success:
                            status_message += " | Screen Share: Failed"
                    print(Colorate.Horizontal(Colors.rainbow, status_message))

                    while True:
                        try:
                            await asyncio.wait_for(ws.recv(), timeout=60)
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            break
                    heartbeat_task.cancel()
                except Exception:
                    raise
                finally:
                    try:
                        await ws.close()
                    except:
                        pass
        except Exception:
            wait_time = min(2 ** min(attempt, 10) * 5, 60)
            await asyncio.sleep(wait_time)
            continue

def run_bot(token, guild_id, channel_id, channel_name, guild_name, self_mute, self_deaf, self_video, self_screen, user_agents):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(join_voice_channel_async(token, guild_id, channel_id, channel_name, guild_name, self_mute, self_deaf, self_video, self_screen, user_agents))
    except KeyboardInterrupt:
        raise 
    except Exception:
        pass
    finally:
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()

def join_voice_channel():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    channel_id = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Nhập ID kênh voice (Channel ID): ")).strip()
    if not channel_id.isdigit():
        print(Colorate.Horizontal(Colors.rainbow, "ID kênh phải là số!"))
        return

    all_functions = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Kích hoạt tất cả chức năng (mic, loa, camera, screen share) cùng lúc? (y/n): ")).strip().lower() == 'y'

    if all_functions:
        self_mute = True   
        self_deaf = True     
        self_video = True       
        self_screen = True    
    else:
        self_mute = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Tắt mic? (y/n): ")).strip().lower() == 'y'
        self_deaf = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Tắt loa? (y/n): ")).strip().lower() == 'y'
        self_video = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Bật camera? (y/n): ")).strip().lower() == 'y'
        self_screen = input(Colorate.Horizontal(Colors.rainbow, "[INPUT] Bật chia sẻ màn hình? (y/n): ")).strip().lower() == 'y'

    tokens = load_tokens()
    first_token = tokens[0]
    guild_id, channel_name, guild_name = get_channel_info(first_token, channel_id, user_agents)
    if guild_id is None:
        print(Colorate.Horizontal(Colors.rainbow, "Không thể lấy thông tin kênh!"))
        return

    confirm = input(Colorate.Horizontal(Colors.rainbow, f"[SYSTEM] Xác Nhận Kết Nối | {len(tokens)} Token | Channel: {channel_name} | Server: {guild_name} | Mic: {'Off' if self_mute else 'On'} | Loa: {'Off' if self_deaf else 'On'} | Camera: {'On' if self_video else 'Off'} | Screen Share: {'On' if self_screen else 'Off'} (y/n): ")).strip().lower()

    if confirm != 'y':
        return

    print(Colorate.Horizontal(Colors.rainbow, f"[SYSTEM] Đang kết nối tới Channel: {channel_name} - ID Channel: {channel_id} | Server: {guild_name} - ID Guild: {guild_id} "))
    completed = 0
    total = len(tokens)
    with ThreadPoolExecutor(max_workers=len(tokens)) as executor:
        futures = [executor.submit(run_bot, token, guild_id, channel_id, channel_name, guild_name, self_mute, self_deaf, self_video, self_screen, user_agents) for token in tokens]
        try:
            for future in futures:
                try:
                    future.result()
                    completed += 1
                    print(Colorate.Horizontal(Colors.rainbow, f"[PROGRESS] Tiến độ: {completed}/{total} ({completed/total*100:.0f}%)"))
                except Exception:
                    completed += 1
                    print(Colorate.Horizontal(Colors.rainbow, f"[PROGRESS] Tiến độ: {completed}/{total} ({completed/total*100:.0f}%)"))
        except KeyboardInterrupt:
            print(Colorate.Horizontal(Colors.rainbow, "Đang dừng chương trình..."))
            executor.shutdown(wait=False, cancel_futures=True)
            raise

def main():
    print_main_banner()
    try:
        join_voice_channel()
    except KeyboardInterrupt:
        pass
    finally:
        print(Colorate.Horizontal(Colors.rainbow, "Stop the program. Thank you for using Treo Voice made by Hoang Gia Kiet x Nguyen Quang Huy!"))

if __name__ == "__main__":
    main()