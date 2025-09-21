import multiprocessing
import time
import random
from zlapi import ZaloAPI, ZaloAPIException, Message, ThreadType

def in_thong_bao(noi_dung):
    print(noi_dung)

def doc_file_noi_dung(ten_file):
    try:
        with open(ten_file, "r", encoding="utf-8") as file:
            return [dong.strip() for dong in file if dong.strip()]
    except Exception as e:
        in_thong_bao(f"Lỗi đọc file {ten_file}: {e}")
        return []

def phan_tich_lua_chon(chuoi_nhap, so_luong_toi_da):
    try:
        cac_so = [int(i.strip()) for i in chuoi_nhap.split(',')]
        return [n for n in cac_so if 1 <= n <= so_luong_toi_da]
    except:
        in_thong_bao("Định dạng nhập sai!")
        return []

def doc_danh_sach_ten(ten_file_ten):
    try:
        with open(ten_file_ten, "r", encoding="utf-8") as file:
            return [dong.strip() for dong in file if dong.strip()]
    except Exception as e:
        in_thong_bao(f"Lỗi đọc file tên {ten_file_ten}: {e}")
        return []

class Bot(ZaloAPI):
    def __init__(self, imei, session_cookies, delay_min, delay_max):
        super().__init__('api_key', 'secret_key', imei, session_cookies)
        self.delay_min = delay_min
        self.delay_max = delay_max if delay_max is not None else delay_min
        self.cac_dong_tin_nhan = doc_file_noi_dung("nhayhoa.txt")
        self.cac_co_chay = {}
        self.cac_tien_trinh = {}

    def bat_dau_gui_tin(self, id_nhom, loai_nhom):
        if not self.cac_dong_tin_nhan:
            in_thong_bao("File nhaychet.txt rỗng hoặc không đọc được!")
            return
        if id_nhom not in self.cac_co_chay:
            self.cac_co_chay[id_nhom] = multiprocessing.Value('b', False)
        if id_nhom not in self.cac_tien_trinh:
            self.cac_tien_trinh[id_nhom] = None
        if not self.cac_co_chay[id_nhom].value:
            self.send(Message(text=""), id_nhom, loai_nhom, ttl=60000)
            self.cac_co_chay[id_nhom].value = True
            self.cac_tien_trinh[id_nhom] = multiprocessing.Process(
                target=self.gui_tin_nhan_thuong,
                args=(id_nhom, loai_nhom, self.cac_co_chay[id_nhom])
            )
            self.cac_tien_trinh[id_nhom].start()

    def gui_tin_nhan_thuong(self, id_nhom, loai_nhom, co_chay):
        danh_sach_ten = doc_danh_sach_ten("ten_nguoi.txt")
        if not danh_sach_ten:
            in_thong_bao("Danh sách tên rỗng, chỉ gửi nội dung gốc!")
    
        while co_chay.value:
            if not self.cac_dong_tin_nhan:
                self.cac_dong_tin_nhan = doc_file_noi_dung("nhayhoa.txt")
                if not self.cac_dong_tin_nhan:
                    in_thong_bao("File nhayhoa.txt rỗng!")
                    co_chay.value = False
                    break
            tin_nhan = random.choice(self.cac_dong_tin_nhan)
            if danh_sach_ten:
                ten = random.choice(danh_sach_ten)
                tin_nhan = f"{ten} {tin_nhan}"
            try:
                self.setTyping(id_nhom, loai_nhom)
                time.sleep(1)
                self.send(Message(text=tin_nhan), id_nhom, loai_nhom)
                in_thong_bao(f"Chửi tag tới nhóm {id_nhom}: {tin_nhan[:30]}...")
            except Exception as e:
                in_thong_bao(f"Lỗi gửi tin nhắn: {e}")
                time.sleep(3)
                continue
            delay = random.uniform(self.delay_min, self.delay_max)
            in_thong_bao(f"Đợi {delay:.2f} giây")
            time.sleep(delay)

    def onMessage(self, *args, **kwargs):
        pass

    def onEvent(self, *args, **kwargs):
        pass

    def onAdminMessage(self, *args, **kwargs):
        pass

    def lay_danh_sach_nhom(self):
        try:
            tat_ca_nhom = self.fetchAllGroups()
            danh_sach_nhom = []
            for id_nhom, _ in tat_ca_nhom.gridVerMap.items():
                thong_tin_nhom = self.fetchGroupInfo(id_nhom)
                ten_nhom = thong_tin_nhom.gridInfoMap[id_nhom]["name"]
                danh_sach_nhom.append({
                    'id': id_nhom,
                    'ten': ten_nhom
                })
            return type('DoiTuongNhom', (), {'nhom': [type('MucNhom', (), {'grid': g['id'], 'ten': g['ten']})() for g in danh_sach_nhom]})()
        except Exception as e:
            in_thong_bao(f"Lỗi lấy danh sách nhóm: {e}")
            return None

def khoi_dong_bot_nhaybox(imei, session_cookies, delay_min, delay_max, id_nhom):
    bot = Bot(imei, session_cookies, delay_min, delay_max)
    for nhom in id_nhom:
        in_thong_bao(f"Bắt đầu nhây nhóm {nhom}")
        bot.bat_dau_gui_tin(nhom, ThreadType.GROUP)
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def khoi_dong_nhieu_tai_khoan():
    while True:
        print("Tool Nhây Box V10.8")
        print("Hướng dẫn sử dụng:")
        print("1. Nhập số lượng tài khoản Zalo muốn chạy.")
        print("2. Nhập IMEI, Cookie cho từng tài khoản.")
        print("3. Nhập tên file chứa danh sách tên người bị chửi.")
        print("4. Chọn nhóm để gửi tin nhắn.")
        print("5. Chọn delay cố định hoặc random (Y/N).")
        print("6. Nếu random, nhập khoảng delay min và max.")
        print("Lưu ý: Phải dz như dzi và gay như nanh")
        
        try:
            so_tai_khoan = int(input("Nhập số tài khoản Zalo muốn chạy [1]: ") or "1")
        except ValueError:
            in_thong_bao("Nhập sai, phải là số nguyên!")
            continue
        ten_file_ten = input("Nhập tên file chứa danh sách tên (VD: ten_nguoi.txt): ") or "ten_nguoi.txt"
        cac_tien_trinh = []
        for i in range(so_tai_khoan):
            in_thong_bao(f"\nNhập thông tin cho tài khoản {i+1}")
            try:
                imei = input("Nhập IMEI Zalo: ")
                cookie_str = input("Nhập Cookie: ")
                try:
                    session_cookies = eval(cookie_str)
                    if not isinstance(session_cookies, dict):
                        in_thong_bao("Cookie phải là dạng dictionary!")
                        continue
                except:
                    in_thong_bao("Cookie sai định dạng, dùng dạng {'key': 'value'}!")
                    continue
                bot = Bot(imei, session_cookies, 0, None)
                delay_type = input("Delay cố định hay random? (Y/N) [N]: ").lower() or 'n'
                if delay_type == 'y':
                    while True:
                        try:
                            delay_min = float(input("Nhập delay ít nhất (giây) [0]: ") or "0")
                            if delay_min < 0:
                                in_thong_bao("Delay min phải không âm!")
                                continue
                            break
                        except ValueError:
                            in_thong_bao("Delay min phải là số!")
                    while True:
                        try:
                            delay_max = float(input("Nhập delay nhiều nhất (giây) [5]: ") or "5")
                            if delay_max < delay_min:
                                in_thong_bao("Delay max phải lớn hơn hoặc bằng delay min!")
                                continue
                            break
                        except ValueError:
                            in_thong_bao("Delay max phải là số!")
                else:
                    while True:
                        try:
                            delay_min = float(input("Nhập delay cố định (giây) [5]: ") or "5")
                            if delay_min < 0:
                                in_thong_bao("Delay phải không âm!")
                                continue
                            break
                        except ValueError:
                            in_thong_bao("Delay phải là số!")
                    delay_max = delay_min
                nhom = bot.lay_danh_sach_nhom()
                if not nhom or not hasattr(nhom, 'nhom') or not nhom.nhom:
                    in_thong_bao("Không lấy được nhóm nào!")
                    continue
                print("\nDanh sách nhóm:")
                for idx, nhom_item in enumerate(nhom.nhom, 1):
                    print(f"{idx}. {nhom_item.ten} (ID: {nhom_item.grid})")
                lua_chon = input("Nhập số thứ tự nhóm để nhây (VD: 1,3): ")
                nhom_chon = phan_tich_lua_chon(lua_chon, len(nhom.nhom))
                if not nhom_chon:
                    in_thong_bao("Không chọn nhóm nào!")
                    continue
                id_nhom_chon = [nhom.nhom[i - 1].grid for i in nhom_chon]
                tien_trinh = multiprocessing.Process(
                    target=khoi_dong_bot_nhaybox,
                    args=(imei, session_cookies, delay_min, delay_max, id_nhom_chon)
                )
                cac_tien_trinh.append(tien_trinh)
                tien_trinh.start()
            except Exception as e:
                in_thong_bao(f"Lỗi nhập liệu: {e}")
                continue
        in_thong_bao("\nTất cả bot đã khởi động thành công")
        while True:
            restart = input("Bạn muốn dùng lại tool? (Y/N) [N]: ").lower() or 'n'
            if restart in ['y', 'n']:
                break
            in_thong_bao("Vui lòng nhập Y hoặc N!")
        if restart == 'y':
            continue
        else:
            in_thong_bao("\nChào tạm biệt! Cảm ơn bạn đã sử dụng tool!")
            break

if __name__ == "__main__":
    khoi_dong_nhieu_tai_khoan()