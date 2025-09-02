import asyncio
import aiohttp
import random
import os

MAX_CONCURRENT_REQUESTS = 3

async def validate_token(token):
    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": token}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return response.status == 200

async def load_tokens_from_file(token_file):
    if not os.path.exists(token_file):
        print(f"[ERROR] File token '{token_file}' không tồn tại!")
        return []
    with open(token_file, 'r', encoding='utf-8') as file:
        tokens = [t.strip() for t in file.read().splitlines() if t.strip()]
    if not tokens:
        print(f"[ERROR] File token '{token_file}' trống!")
    return []

async def handle_response(response, channel_id, message, token):
    token_preview = token[:5] + "..." + token[-5:] if len(token) > 10 else token
    try:
        if response.status == 200:
            print(f"[SUCCESS] Gửi tin nhắn thành công - Token: {token_preview}")
            return 0
        elif response.status == 429:
            retry_after = (await response.json()).get("retry_after", 1)
            print(f"[INFO] Token {token_preview} bị giới hạn, chờ {retry_after}s")
            return retry_after
        elif response.status == 401:
            print(f"[ERROR] Token {token_preview} không hợp lệ!")
            return 0
        elif response.status in [500, 502, 408]:
            print(f"[ERROR] Lỗi server {response.status} - Token: {token_preview}")
            return 5
        else:
            print(f"[ERROR] Lỗi {response.status} - Token: {token_preview}")
            return 5
    except Exception as e:
        print(f"[ERROR] Lỗi xử lý phản hồi: {str(e)[:50]}...")
        return 5

def is_valid_delay(input_str):
    try:
        delay = float(input_str)
        return delay > 0
    except ValueError:
        return False

def is_valid_channel_id(input_str):
    return input_str.isdigit()

async def check_file_exists(file_path):
    exists = os.path.exists(file_path)
    if not exists:
        print(f"[ERROR] File '{file_path}' không tồn tại!")
    return exists

async def spam_message_nhay(token, channel_id, messages, delay, user_ids, semaphore):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    token_preview = token[:5] + "..." + token[-5:] if len(token) > 10 else token
    mention_string = " ".join([f"<@{user_id}>" for user_id in user_ids]) if user_ids else ""

    async with aiohttp.ClientSession() as session:
        while True:
            message = random.choice(messages).strip() if messages else ""
            try:
                async with semaphore:
                    message_to_send = f"# {mention_string} {message}" if mention_user else f"# {message}"
                    async with session.post(url, json={"content": message_to_send}, headers=headers) as response:
                        retry_after = await handle_response(response, channel_id, message, token)
                        if retry_after:
                            await asyncio.sleep(retry_after)
                        await asyncio.sleep(delay)
            except Exception as e:
                print(f"[ERROR] Token {token_preview}: {str(e)[:50]}...")
                await asyncio.sleep(1)

async def main():
    print("═══════ NHÂY TAG DISCORD ═══════")
    print("↦ Admin: Ng Quang Huy")
    print("↦ Discord: ngquanghuy")
    print("↦ Zalo: 0904562214")
    print("════════════════════════════════")

    mention_user = input("Có muốn tag người dùng? (y/n): ").strip().lower() == 'y'
    user_ids = []
    if mention_user:
        user_ids = input("Nhập ID người dùng (cách nhau bởi dấu phẩy): ").split(',')
        user_ids = [uid.strip() for uid in user_ids if uid.strip()]

    channel_ids = []
    while True:
        channel_id = input("Nhập ID kênh (hoặc 'done' để kết thúc): ").strip().lower()
        if channel_id == "done":
            break
        if is_valid_channel_id(channel_id):
            channel_ids.append(channel_id)
        else:
            print("[ERROR] ID kênh không hợp lệ!")

    tokens_map = {}
    for channel_id in channel_ids:
        token_file = input(f"Nhập file token cho kênh {channel_id}: ")
        if not await check_file_exists(token_file):
            continue
        tokens = await load_tokens_from_file(token_file)
        valid_tokens = [t for t in tokens if await validate_token(t)]
        if not valid_tokens:
            print(f"[ERROR] Không có token hợp lệ trong file {token_file}!")
            continue
        tokens_map[channel_id] = valid_tokens

    if not tokens_map:
        print("[ERROR] Không có kênh hoặc token hợp lệ để tiếp tục!")
        return

    txt_files = [f for f in os.listdir() if f.endswith('.txt')]
    if not txt_files:
        print("[ERROR] Không tìm thấy file .txt nào trong thư mục!")
        return
    print("═══════ DANH SÁCH FILE TIN NHẮN ═══════")
    for idx, file in enumerate(txt_files, 1):
        print(f"{idx}: {file}")
    file_indexes = input("Chọn file tin nhắn (số thứ tự, cách nhau bởi dấu phẩy): ")
    try:
        file_indexes = [int(i) - 1 for i in file_indexes.split(',') if i.strip()]
        if any(index < 0 or index >= len(txt_files) for index in file_indexes):
            print("[ERROR] Chỉ số file không hợp lệ!")
            return
    except ValueError:
        print("[ERROR] Vui lòng nhập số hợp lệ!")
        return

    files_content = []
    for file_index in file_indexes:
        with open(txt_files[file_index], 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.read().splitlines() if line.strip()]
            files_content.extend(lines)

    print("═══════ BẮT ĐẦU NHÂY TAG ═══════")
    print(f"[CONFIG] Số kênh: {len(channel_ids)} | Số dòng tin nhắn: {len(files_content)}")

    tasks = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    for channel_id, tokens in tokens_map.items():
        for i, token in enumerate(tokens):
            delay_input = input(f"Nhập delay cho token thứ {i + 1} (kênh {channel_id}): ")
            if not is_valid_delay(delay_input):
                print(f"[ERROR] Delay không hợp lệ cho token thứ {i + 1}!")
                return
            delay = float(delay_input)
            tasks.append(spam_message_nhay(token, channel_id, files_content, delay, user_ids, semaphore))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())