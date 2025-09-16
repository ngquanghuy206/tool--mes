import multiprocessing
import time
import random
from zlapi import ZaloAPI, ZaloAPIException, Message, ThreadType, Mention, MultiMention

def in_thong_bao(noi_dung):
    print(noi_dung)

def doc_file_noi_dung(ten_file="nhaychet.txt"):
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

class Bot(ZaloAPI):
    def __init__(self, imei, session_cookies, delay_min, delay_max, ttl=None):
        super().__init__('api_key', 'secret_key', imei, session_cookies)
        self.delay_min = delay_min
        self.delay_max = delay_max if delay_max is not None else delay_min
        self.ttl = ttl
        self.cac_dong_tin_nhan = doc_file_noi_dung()
        self.cac_co_chay = {}
        self.cac_tien_trinh = {}
        self.cac_nguoi_duoc_tag = {}

    def bat_dau_nhay_tag(self, id_nhom, loai_nhom, nguoi_duoc_tag):
        if not self.cac_dong_tin_nhan:
            in_thong_bao("File nhaychet.txt rỗng hoặc không đọc được!")
            return
        if id_nhom not in self.cac_co_chay:
            self.cac_co_chay[id_nhom] = multiprocessing.Value('b', False)
        if id_nhom not in self.cac_tien_trinh:
            self.cac_tien_trinh[id_nhom] = None
        if id_nhom not in self.cac_nguoi_duoc_tag:
            self.cac_nguoi_duoc_tag[id_nhom] = nguoi_duoc_tag
        if not self.cac_co_chay[id_nhom].value:
            self.send(Message(text=""), id_nhom, loai_nhom, ttl=self.ttl if self.ttl is not None else 60000)
            self.cac_co_chay[id_nhom].value = True
            self.cac_tien_trinh[id_nhom] = multiprocessing.Process(
                target=self.gui_tin_nhan_tag,
                args=(id_nhom, loai_nhom, self.cac_co_chay[id_nhom])
            )
            self.cac_tien_trinh[id_nhom].start()

    def gui_tin_nhan_tag(self, id_nhom, loai_nhom, co_chay):
        chi_so_noi_dung = 0
        while co_chay.value and self.cac_nguoi_duoc_tag[id_nhom]:
            if not self.cac_dong_tin_nhan:
                self.cac_dong_tin_nhan = doc_file_noi_dung()
                if not self.cac_dong_tin_nhan:
                    in_thong_bao("File nhaychet.txt rỗng!")
                    co_chay.value = False
                    break
            tin_nhan_goc = self.cac_dong_tin_nhan[chi_so_noi_dung]
            tin_nhan = tin_nhan_goc + " "
            danh_sach_tag = []
            nguoi_hop_le = []
            ten_nguoi_tag = []
            for id_nguoi in self.cac_nguoi_duoc_tag[id_nhom]:
                try:
                    thong_tin_nguoi = self.fetchUserInfo(id_nguoi)
                    if not thong_tin_nguoi or id_nguoi not in thong_tin_nguoi.changed_profiles:
                        in_thong_bao(f"Thành viên {id_nguoi} không còn trong nhóm, bỏ qua!")
                        continue
                    ten_nguoi = thong_tin_nguoi.changed_profiles[id_nguoi]['displayName']
                    tin_nhan += "@ThanhVien "
                    ten_nguoi_tag.append(ten_nguoi)
                    nguoi_hop_le.append(id_nguoi)
                except Exception as e:
                    in_thong_bao(f"Lỗi lấy thông tin người {id_nguoi}: {e}")
                    continue
            self.cac_nguoi_duoc_tag[id_nhom] = nguoi_hop_le
            if not self.cac_nguoi_duoc_tag[id_nhom]:
                in_thong_bao("Hết người để tag, dừng bot!")
                co_chay.value = False
                break
            tin_nhan_cuoi = tin_nhan
            for i, ten_nguoi in enumerate(ten_nguoi_tag):
                placeholder = "@ThanhVien "
                tin_nhan_cuoi = tin_nhan_cuoi.replace(placeholder, f"@{ten_nguoi} ", 1)
                vi_tri = tin_nhan_cuoi.find(f"@{ten_nguoi}")
                danh_sach_tag.append(Mention(nguoi_hop_le[i], length=len(f"@{ten_nguoi}"), offset=vi_tri, auto_format=False))
            try:
                self.setTyping(id_nhom, loai_nhom)
                time.sleep(2)
                tin_nhan_gui = Message(text=tin_nhan_cuoi.strip(), mention=MultiMention(danh_sach_tag))
                if self.ttl is not None:
                    self.send(tin_nhan_gui, thread_id=id_nhom, thread_type=loai_nhom, ttl=self.ttl)
                else:
                    self.send(tin_nhan_gui, thread_id=id_nhom, thread_type=loai_nhom)
                in_thong_bao(f"Nhây tag tới nhóm {id_nhom}: {tin_nhan_cuoi[:30]}...")
            except Exception as e:
                in_thong_bao(f"Lỗi gửi tin nhắn: {e}")
                time.sleep(3)
                continue
            chi_so_noi_dung = (chi_so_noi_dung + 1) % len(self.cac_dong_tin_nhan)
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

    def lay_thong_tin_nhom(self, id_nhom):
        try:
            return self.fetchGroupInfo(id_nhom)
        except ZaloAPIException as e:
            in_thong_bao(f"Lỗi API Zalo khi lấy thông tin nhóm {id_nhom}: {e}")
            return None
        except Exception as e:
            in_thong_bao(f"Lỗi khi lấy thông tin nhóm {id_nhom}: {e}")
            return None

    def lay_thanh_vien_nhom(self, id_nhom):
        try:
            thong_tin_nhom = self.lay_thong_tin_nhom(id_nhom)
            if not thong_tin_nhom or not hasattr(thong_tin_nhom, 'gridInfoMap') or id_nhom not in thong_tin_nhom.gridInfoMap:
                in_thong_bao(f"Không lấy được thông tin nhóm {id_nhom}")
                return []
            danh_sach_thanh_vien = thong_tin_nhom.gridInfoMap[id_nhom]["memVerList"]
            id_thanh_vien = [mem.split("_")[0] for mem in danh_sach_thanh_vien]
            thanh_vien = []
            for id_nguoi in id_thanh_vien:
                try:
                    thong_tin_nguoi = self.fetchUserInfo(id_nguoi)
                    du_lieu_nguoi = thong_tin_nguoi.changed_profiles[id_nguoi]
                    thanh_vien.append({
                        'id': du_lieu_nguoi['userId'],
                        'ten': du_lieu_nguoi['displayName']
                    })
                except Exception as e:
                    in_thong_bao(f"Lỗi lấy thông tin người {id_nguoi}: {e}")
                    thanh_vien.append({
                        'id': id_nguoi,
                        'ten': f"[Lỗi: {id_nguoi}]"
                    })
            return thanh_vien
        except Exception as e:
            in_thong_bao(f"Lỗi lấy danh sách thành viên: {e}")
            return []

def khoi_dong_bot(imei, session_cookies, delay_min, delay_max, id_nhom, nguoi_duoc_tag, ttl):
    bot = Bot(imei, session_cookies, delay_min, delay_max, ttl)
    for nhom in id_nhom:
        in_thong_bao(f"Bắt đầu nhây tag nhóm {nhom}")
        bot.bat_dau_nhay_tag(nhom, ThreadType.GROUP, nguoi_duoc_tag.get(nhom, []))
    bot.listen(run_forever=True, thread=False, delay=1, type='requests')

def khoi_dong_nhieu_tai_khoan():
    while True:
        print("Tool Nhây Tag V8.0")
        print("Hướng dẫn sử dụng:")
        print("1. Nhập số lượng tài khoản Zalo muốn chạy.")
        print("2. Nhập IMEI, Cookie cho từng tài khoản.")
        print("3. Chọn có bật thời gian tự hủy tin nhắn (TTL) hay không (Y/N).")
        print("4. Chọn nhóm để nhây tag (VD: 1,3).")
        print("5. Chọn thành viên để tag (VD: 1,2,3 hoặc 0 để không tag).")
        print("6. Chọn delay cố định hoặc random (Y/N).")
        print("7. Nếu random, nhập khoảng delay min và max.")
        print("Lưu ý: Đảm bảo file nhaychet.txt chứa nội dung và cookie hợp lệ!")
        
        try:
            so_tai_khoan = int(input("Nhập số tài khoản Zalo muốn chạy [1]: ") or "1")
        except ValueError:
            in_thong_bao("Nhập sai, phải là số nguyên!")
            continue
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
                ttl = None
                while True:
                    ttl_choice = input("Bật thời gian tự hủy tin nhắn (TTL)? (Y/N) [N]: ").lower() or 'n'
                    if ttl_choice in ['y', 'n']:
                        break
                    in_thong_bao("Vui lòng nhập Y hoặc N!")
                if ttl_choice == 'y':
                    while True:
                        try:
                            ttl_seconds = float(input("Nhập thời gian tự hủy (giây): "))
                            if ttl_seconds <= 0:
                                in_thong_bao("Thời gian TTL phải lớn hơn 0!")
                                continue
                            ttl = int(ttl_seconds * 1000)
                            break
                        except ValueError:
                            in_thong_bao("Thời gian TTL phải là số!")
                bot = Bot(imei, session_cookies, 0, None, ttl)
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
                lua_chon = input("Nhập số thứ tự nhóm để nhây tag (VD: 1,3): ")
                nhom_chon = phan_tich_lua_chon(lua_chon, len(nhom.nhom))
                if not nhom_chon:
                    in_thong_bao("Không chọn nhóm nào!")
                    continue
                id_nhom_chon = [nhom.nhom[i - 1].grid for i in nhom_chon]
                nguoi_duoc_tag = {}
                for id_nhom in id_nhom_chon:
                    thanh_vien = bot.lay_thanh_vien_nhom(id_nhom)
                    if not thanh_vien:
                        in_thong_bao(f"Nhóm {id_nhom} không có thành viên!")
                        continue
                    print(f"\nThành viên nhóm {id_nhom}:")
                    for idx, tv in enumerate(thanh_vien, 1):
                        print(f"{idx}. {tv['ten']} (ID: {tv['id']})")
                    lua_chon_tv = input("Nhập số thứ tự thành viên để tag (VD: 1,2,3, 0 để không tag): ")
                    if lua_chon_tv.strip() == "0":
                        nguoi_duoc_tag[id_nhom] = []
                    else:
                        thanh_vien_chon = phan_tich_lua_chon(lua_chon_tv, len(thanh_vien))
                        nguoi_duoc_tag[id_nhom] = [thanh_vien[i - 1]['id'] for i in thanh_vien_chon]
                tien_trinh = multiprocessing.Process(
                    target=khoi_dong_bot,
                    args=(imei, session_cookies, delay_min, delay_max, id_nhom_chon, nguoi_duoc_tag, ttl)
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