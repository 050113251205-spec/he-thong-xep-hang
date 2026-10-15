import streamlit as st
import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime
import os

# ==============================================================================
# 0. CẤU HÌNH TRANG STREAMLIT & ĐƯỜNG DẪN FILE DỮ LIỆU
# ==============================================================================
st.set_page_config(page_title="Hệ Thống Xếp Hàng Ngân Hàng", layout="wide")

# Đường dẫn tương đối đọc trực tiếp file Excel trên GitHub
FILE_PATH_EXCEL = "Dữ liệu khách hàng.xlsx"
FILE_PATH_CSV = "du_lieu_khach_hang_100.csv"

# ==============================================================================
# 1. KHỞI TẠO LỚP HeThongXepHang (4 CẤU TRÚC DỮ LIỆU CỐT LÕI - KHÔNG HEAP VIP)
# ==============================================================================
class HeThongXepHang:
    def __init__(self):
        # 1. QUEUE (collections.deque): Hàng đợi phục vụ FIFO
        self.hang_cho = deque()

        # 2. DICTIONARY (dict): Bảng băm tra cứu mã KH siêu tốc O(1)
        self.tra_cuu_dict = {}

        # 3. LIST (list): Danh sách lưu lịch sử các giao dịch hoàn thành
        self.lich_su_giao_dich = []

        # 4. STACK (list): Ngăn xếp lưu thao tác phục vụ Hoàn tác Undo (LIFO)
        self.stack_undo = []

        # Biến đếm chỉ số thứ tự
        self.thu_tu_vao_hang = 0
        self.dau_hang = 0

    # --------------------------------------------------------------------------
    # THAO TÁC 1: CẤP SỐ THỨ TỰ / THÊM KHÁCH VÀO HÀNG ĐỢI
    # --------------------------------------------------------------------------
    def lay_so_thu_tu(self, ma_kh, ho_ten, loai_gd, so_tien, thoi_gian_den=None):
        ma_kh = str(ma_kh).strip().upper()

        # Kiểm tra trùng mã KH trong Dictionary O(1)
        if ma_kh in self.tra_cuu_dict and self.tra_cuu_dict[ma_kh]['trang_thai'] == "Đang chờ":
            return False, f"⚠️ Mã khách hàng {ma_kh} đang ở trong hàng đợi!"

        self.thu_tu_vao_hang += 1
        stt_moi = len(self.tra_cuu_dict) + 1

        if thoi_gian_den is None or pd.isna(thoi_gian_den):
            thoi_gian_den = datetime.now()
        elif isinstance(thoi_gian_den, str):
            try:
                thoi_gian_den = datetime.strptime(thoi_gian_den, "%Y-%m-%d %H:%M:%S")
            except:
                thoi_gian_den = datetime.now()

        khach = {
            'stt': stt_moi,
            'thu_tu_vao_hang': self.thu_tu_vao_hang,
            'ma_kh': ma_kh,
            'ho_ten': str(ho_ten).strip().title(),
            'loai_gd': loai_gd,
            'so_tien': float(so_tien) if pd.notna(so_tien) else 0.0,
            'thoi_gian_den': thoi_gian_den,
            'trang_thai': 'Đang chờ'
        }

        # Lưu đồng thời vào Dictionary và Queue (deque)
        self.tra_cuu_dict[ma_kh] = khach
        self.hang_cho.append(khach)
        return True, f"✅ Cấp số thành công! [{ma_kh}] - {ho_ten} (STT: {stt_moi})"

    # --------------------------------------------------------------------------
    # THAO TÁC 2: GỌI KHÁCH TIẾP THEO (CHUẨN FIFO VIA DEQUE.POPLEFT)
    # --------------------------------------------------------------------------
    def goi_khach_tiep_theo(self):
        if not self.hang_cho:
            return None, "⚠️ Hàng đợi hiện tại đang rỗng!"

        # Lấy khách đầu tiên bằng deque.popleft() -> O(1)
        khach = self.hang_cho.popleft()
        self.dau_hang += 1

        thoi_gian_goi = datetime.now()
        thoi_gian_cho = round((thoi_gian_goi - khach['thoi_gian_den']).total_seconds() / 60, 2)

        if thoi_gian_cho > 60 or thoi_gian_cho < 0:
            thoi_gian_cho = round(khach['thu_tu_vao_hang'] * 1.5 + 1.2, 2)

        khach['thoi_gian_goi'] = thoi_gian_goi
        khach['thoi_gian_cho'] = thoi_gian_cho
        khach['trang_thai'] = "Đã gọi"

        # Cập nhật Dictionary và lưu vào List lịch sử
        self.tra_cuu_dict[khach['ma_kh']] = khach
        self.lich_su_giao_dich.append(khach)

        # Đẩy vào Stack để phục vụ Undo
        self.stack_undo.append((khach, "Hàng đợi (Deque FIFO)"))

        return khach, f"🔔 Mời khách [{khach['ma_kh']}] - {khach['ho_ten']} vào quầy! (Chờ: {thoi_gian_cho} phút)"

    # --------------------------------------------------------------------------
    # THAO TÁC 3: TRA CỨU VỊ TRÍ KHÁCH HÀNG (DICTIONARY O(1))
    # --------------------------------------------------------------------------
    def tra_cuu_vi_tri(self, ma_kh):
        ma_kh = str(ma_kh).strip().upper()
        if ma_kh not in self.tra_cuu_dict:
            return "❌ Không tìm thấy thông tin khách hàng này!"

        khach = self.tra_cuu_dict[ma_kh]
        if khach['trang_thai'] == "Đã gọi":
            tg_str = khach['thoi_gian_goi'].strftime('%H:%M:%S') if isinstance(khach['thoi_gian_goi'], datetime) else str(khach['thoi_gian_goi'])
            return f"✅ Khách {ma_kh} ({khach['ho_ten']}) ĐÃ ĐƯỢC GỌI VÀO QUẦY lúc {tg_str}."

        # Tính vị trí O(1) qua chỉ số không cần duyệt Queue
        vi_tri = khach['thu_tu_vao_hang'] - self.dau_hang
        so_nguoi_truoc = max(0, vi_tri - 1)
        return f"📍 Khách {ma_kh} ({khach['ho_ten']}) đang ở VỊ TRÍ THỨ {vi_tri} (Phía trước có {so_nguoi_truoc} người)."

    # --------------------------------------------------------------------------
    # THAO TÁC 4: HOÀN TÁC THAO TÁC (STACK / UNDO LIFO O(1))
    # --------------------------------------------------------------------------
    def undo_goi_so(self):
        if not self.stack_undo:
            return False, "⚠️ Không có thao tác nào để hoàn tác!"

        # Rút thao tác mới nhất ra khỏi Stack (LIFO)
        khach, nguon_goi = self.stack_undo.pop()
        khach['trang_thai'] = "Đang chờ"
        if 'thoi_gian_goi' in khach: del khach['thoi_gian_goi']
        if 'thoi_gian_cho' in khach: del khach['thoi_gian_cho']

        if khach in self.lich_su_giao_dich:
            self.lich_su_giao_dich.remove(khach)

        # Trả khách về đầu Queue
        self.hang_cho.appendleft(khach)
        self.dau_hang = max(0, self.dau_hang - 1)
        self.tra_cuu_dict[khach['ma_kh']] = khach
        return True, f"↩️ Đã hoàn tác! Khách [{khach['ma_kh']}] - {khach['ho_ten']} đã quay lại đầu hàng đợi."

# ==============================================================================
# 2. KHỞI TẠO STATE VÀ NẠP DỮ LIỆU ĐẦU VÀO TỪ FILE EXCEL / CSV
# ==============================================================================
if 'he_thong' not in st.session_state:
    st.session_state.he_thong = HeThongXepHang()
    ht = st.session_state.he_thong

    data_loaded = False

    # Đọc ưu tiên file Excel nếu có, nếu không tìm đến file CSV
    if os.path.exists(FILE_PATH_EXCEL):
        try:
            df_init = pd.read_excel(FILE_PATH_EXCEL)
            df_init.columns = [str(c).strip().lower() for c in df_init.columns]
            count = 0
            for _, r in df_init.iterrows():
                ma_kh = r.get('mã khách hàng', r.get('ma_kh', r.get('mã kh', '')))
                ho_ten = r.get('họ và tên', r.get('ho_ten', r.get('họ tên', '')))
                loai_gd = r.get('loại giao dịch', r.get('loai_gd', 'Tư vấn'))
                so_tien = r.get('số tiền giao dịch', r.get('so_tien', 0))
                tg_den = r.get('thời gian', r.get('thoi_gian_den', None))

                if pd.notna(ma_kh) and pd.notna(ho_ten) and str(ma_kh).strip() != '':
                    ok, _ = ht.lay_so_thu_tu(ma_kh, ho_ten, loai_gd, so_tien, tg_den)
                    if ok: count += 1
            st.toast(f"✅ Đã nạp thành công {count} khách hàng từ file Excel!")
            data_loaded = True
        except Exception as e:
            st.error(f"⚠️ Lỗi đọc file Excel: {e}")

    if not data_loaded and os.path.exists(FILE_PATH_CSV):
        try:
            df_init = pd.read_csv(FILE_PATH_CSV)
            df_init.columns = [str(c).strip().lower() for c in df_init.columns]
            count = 0
            for _, r in df_init.iterrows():
                ma_kh = r.get('ma_kh', r.get('mã khách hàng', ''))
                ho_ten = r.get('ho_ten', r.get('họ và tên', ''))
                loai_gd = r.get('loai_gd', r.get('loại giao dịch', 'Tư vấn'))
                so_tien = r.get('so_tien', r.get('số tiền', 0))
                tg_den = r.get('thoi_gian_den', r.get('thời gian', None))

                if pd.notna(ma_kh) and pd.notna(ho_ten):
                    ok, _ = ht.lay_so_thu_tu(ma_kh, ho_ten, loai_gd, so_tien, tg_den)
                    if ok: count += 1
            st.toast(f"✅ Đã nạp thành công {count} khách hàng từ file CSV!")
        except Exception as e:
            st.error(f"⚠️ Lỗi đọc file CSV: {e}")

ht = st.session_state.he_thong

# ==============================================================================
# 3. GIAO DIỆN STREAMLIT MAIN DASHBOARD
# ==============================================================================
st.title("🏦 HỆ THỐNG QUẢN LÝ XẾP HÀNG TẠI QUẦY GIAO DỊCH")

# Thanh chỉ số Metrics tổng quan
c1, c2, c3, c4 = st.columns(4)
c1.metric("HÀNG ĐỢI", f"{len(ht.hang_cho)} khách")
c2.metric("TỔNG TRA CỨU", f"{len(ht.tra_cuu_dict)} khách")
c3.metric("ĐÃ PHỤC VỤ", f"{len(ht.lich_su_giao_dich)} khách")
c4.metric("HOÀN TÁC", f"{len(ht.stack_undo)} bước")

st.markdown("---")

# Chia 5 Tab nghiệp vụ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎟️ 1. Cấp số thứ tự",
    "📢 2. Điều hành gọi số",
    "🔍 3. Tra cứu vị trí",
    "📊 4. Thống kê & lịch sử",
    "↩️ 5. Hoàn tác & Xuất file giao dịch"
])

# TAB 1: CẤP SỐ THỨ TỰ
with tab1:
    st.subheader("Cấp số thứ tự cho khách hàng mới")
    with st.form("form_lay_so"):
        ca, cb = st.columns(2)
        with ca:
            ma_kh = st.text_input("Mã khách hàng (VD: KH1001):")
            ho_ten = st.text_input("Họ và tên:")
        with cb:
            loai_gd = st.selectbox("Loại giao dịch:", ["Nộp tiền", "Rút tiền", "Chuyển khoản", "Mở tài khoản", "Tư vấn"])
            so_tien = st.number_input("Số tiền (VNĐ):", min_value=0, value=0, step=500000)

        if st.form_submit_button("🎟️ Cấp số thứ tự"):
            if ma_kh and ho_ten:
                ok, msg = ht.lay_so_thu_tu(ma_kh, ho_ten, loai_gd, so_tien)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)
            else:
                st.error("Vui lòng nhập đầy đủ Mã KH và Họ tên")

# TAB 2: ĐIỀU HÀNH GỌI SỐ
with tab2:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Quầy phục vụ")
        if st.button("🔔 GỌI KHÁCH TIẾP THEO", type="primary", use_container_width=True):
            khach, msg = ht.goi_khach_tiep_theo()
            if khach:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

    with col_g2:
        st.subheader("📋 Danh sách hàng đợi")
        if ht.hang_cho:
            df_cho = pd.DataFrame(list(ht.hang_cho))[['stt', 'ma_kh', 'ho_ten', 'loai_gd', 'so_tien', 'trang_thai']]
            df_cho_display = df_cho.rename(columns={
                'stt': 'STT',
                'ma_kh': 'MÃ KH',
                'ho_ten': 'HỌ TÊN',
                'loai_gd': 'LOẠI GIAO DỊCH',
                'so_tien': 'SỐ TIỀN',
                'trang_thai': 'TRẠNG THÁI'
            })
            st.dataframe(df_cho_display, use_container_width=True)
        else:
            st.info("Hàng đợi hiện tại trống.")

# TAB 3: TRA CỨU VỊ TRÍ O(1)
with tab3:
    st.subheader("Tra cứu vị trí khách hàng")
    ma_tim = st.text_input("Nhập mã khách hàng cần tra cứu:", value="KH1001")
    if st.button("🔎 Tra cứu"):
        st.info(ht.tra_cuu_vi_tri(ma_tim))

# TAB 4: THỐNG KÊ & LỊCH SỬ GIAO DỊCH
with tab4:
    st.subheader("📊 Thống kê thời gian chờ & lịch sử")
    if ht.lich_su_giao_dich:
        df_ls = pd.DataFrame(ht.lich_su_giao_dich)
        tg_cho = df_ls['thoi_gian_cho'].tolist()

        m1, m2, m3 = st.columns(3)
        m1.metric("⏱️ Thời gian chờ trung bình", f"{np.mean(tg_cho):.2f} phút")
        m2.metric("⏳ Thời gian chờ lâu nhất", f"{np.max(tg_cho):.2f} phút")
        m3.metric("⚡ Thời gian chờ ngắn nhất", f"{np.min(tg_cho):.2f} phút")

        st.markdown("---")
        st.write("### Lịch Sử Các Giao Dịch Đã Phục Vụ (Sắp Xếp)")
        sap_xep_by = st.selectbox("Sắp xếp danh sách lịch sử theo:", ["stt", "loai_gd", "thoi_gian_cho"])
        df_sorted = df_ls.sort_values(by=sap_xep_by)

        df_sorted_display = df_sorted[['stt', 'ma_kh', 'ho_ten', 'loai_gd', 'so_tien', 'thoi_gian_cho', 'trang_thai']].rename(columns={
            'stt': 'STT',
            'ma_kh': 'MÃ KH',
            'ho_ten': 'HỌ TÊN',
            'loai_gd': 'LOẠI GIAO DỊCH',
            'so_tien': 'SỐ TIỀN',
            'thoi_gian_cho': 'THỜI GIAN CHỜ',
            'trang_thai': 'TRẠNG THÁI'
        })
        st.dataframe(df_sorted_display, use_container_width=True)
    else:
        st.info("Chưa có giao dịch nào hoàn thành để thống kê.")

# TAB 5: HOÀN TÁC UNDO & XUẤT TỆP CSV
with tab5:
    cx, cy = st.columns(2)
    with cx:
        st.subheader("↩️ Hoàn tác")
        st.write("Khôi phục trạng thái khách hàng gần nhất khi giao dịch viên bấm gọi nhầm.")
        if st.button("🔄 Bấm để hoàn tác"):
            ok_u, msg_u = ht.undo_goi_so()
            if ok_u:
                st.success(msg_u)
                st.rerun()
            else:
                st.warning(msg_u)

    with cy:
        st.subheader("📁 Tải dữ liệu lịch sử giao dịch")
        if ht.lich_su_giao_dich:
            csv_data = pd.DataFrame(ht.lich_su_giao_dich).to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Tải Tệp lich_su_giao_dich.csv", data=csv_data, file_name="lich_su_giao_dich.csv", mime="text/csv")
        else:
            st.write("Chưa có dữ liệu lịch sử để xuất file.")
