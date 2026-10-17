import streamlit as st
import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime
import os

# ==============================================================================
# 0. CẤU HÌNH TRANG STREAMLIT & ĐỌC DỮ LIỆU TỰ ĐỘNG
# ==============================================================================
st.set_page_config(page_title="Hệ Thống Xếp Hàng Ngân Hàng", layout="wide")

# ==============================================================================
# 1. KHỞI TẠO LỚP HeThongXepHang
# ==============================================================================
class HeThongXepHang:
    def __init__(self):
        self.hang_cho = deque()
        self.tra_cuu_dict = {}
        self.lich_su_giao_dich = []
        self.stack_undo = []
        self.thu_tu_vao_hang = 0
        self.dau_hang = 0
        self.start_time_per_day = {}

    def lay_so_thu_tu(self, ma_kh, ho_ten, loai_gd, so_tien, thoi_gian_den=None):
        ma_kh = str(ma_kh).strip().upper()

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

        ngay_hd = thoi_gian_den.strftime('%Y-%m-%d')
        if ngay_hd not in self.start_time_per_day:
            self.start_time_per_day[ngay_hd] = thoi_gian_den

        khach = {
            'stt': stt_moi,
            'thu_tu_vao_hang': self.thu_tu_vao_hang,
            'ma_kh': ma_kh,
            'ho_ten': str(ho_ten).strip().title(),
            'loai_gd': loai_gd,
            'so_tien': float(so_tien) if pd.notna(so_tien) else 0.0,
            'thoi_gian_den': thoi_gian_den,
            'ngay_hoat_dong': ngay_hd,
            'trang_thai': 'Đang chờ'
        }

        self.tra_cuu_dict[ma_kh] = khach
        self.hang_cho.append(khach)
        return True, f"✅ Cấp số thành công! [{ma_kh}] - {ho_ten} (STT: {stt_moi})"

    def goi_khach_tiep_theo(self):
        if not self.hang_cho:
            return None, "⚠️ Hàng đợi hiện tại đang rỗng!"

        khach = self.hang_cho.popleft()
        self.dau_hang += 1

        thoi_gian_goi = khach['thoi_gian_den']
        ngay_hd = khach['ngay_hoat_dong']
        start_time = self.start_time_per_day.get(ngay_hd, thoi_gian_goi)

        sec = max(0, (thoi_gian_goi - start_time).total_seconds())
        thoi_gian_cho_phut = round(sec / 60.0, 2)
        thoi_gian_cho_str = f"{int(sec//60):02d}:{int(sec%60):02d}"

        khach['thoi_gian_goi'] = thoi_gian_goi
        khach['thoi_gian_cho'] = thoi_gian_cho_phut
        khach['thoi_gian_cho_str'] = thoi_gian_cho_str
        khach['trang_thai'] = "Đã gọi"

        self.tra_cuu_dict[khach['ma_kh']] = khach
        self.lich_su_giao_dich.append(khach)
        self.stack_undo.append((khach, "Hàng đợi (Deque FIFO)"))

        return khach, f"🔔 Mời khách [{khach['ma_kh']}] - {khach['ho_ten']} vào quầy! (Ngày: {ngay_hd} | Thời gian chờ: {thoi_gian_cho_str})"

    def tra_cuu_vi_tri(self, ma_kh):
        ma_kh = str(ma_kh).strip().upper()
        if ma_kh not in self.tra_cuu_dict:
            return "❌ Không tìm thấy thông tin khách hàng này!"

        khach = self.tra_cuu_dict[ma_kh]
        if khach['trang_thai'] == "Đã gọi":
            tg_str = khach['thoi_gian_goi'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(khach['thoi_gian_goi'], datetime) else str(khach['thoi_gian_goi'])
            return f"✅ Khách {ma_kh} ({khach['ho_ten']}) ĐÃ ĐƯỢC GỌI VÀO QUẦY lúc {tg_str} (Thời gian chờ: {khach.get('thoi_gian_cho_str', '00:00')})."

        vi_tri = khach['thu_tu_vao_hang'] - self.dau_hang
        so_nguoi_truoc = max(0, vi_tri - 1)
        return f"📍 Khách {ma_kh} ({khach['ho_ten']}) đang ở VỊ TRÍ THỨ {vi_tri} (Phía trước có {so_nguoi_truoc} người)."

    def undo_goi_so(self):
        if not self.stack_undo:
            return False, "⚠️ Không có thao tác nào để hoàn tác!"

        khach, nguon_goi = self.stack_undo.pop()
        khach['trang_thai'] = "Đang chờ"
        if 'thoi_gian_goi' in khach: del khach['thoi_gian_goi']
        if 'thoi_gian_cho' in khach: del khach['thoi_gian_cho']
        if 'thoi_gian_cho_str' in khach: del khach['thoi_gian_cho_str']

        if khach in self.lich_su_giao_dich:
            self.lich_su_giao_dich.remove(khach)

        self.hang_cho.appendleft(khach)
        self.dau_hang = max(0, self.dau_hang - 1)
        self.tra_cuu_dict[khach['ma_kh']] = khach
        return True, f"↩️ Đã hoàn tác! Khách [{khach['ma_kh']}] - {khach['ho_ten']} đã quay lại đầu hàng đợi."

# ==============================================================================
# 2. KHỞI TẠO STATE VÀ TỰ ĐỘNG TÌM / NẠP FILE DỮ LIỆU
# ==============================================================================
if 'he_thong' not in st.session_state:
    st.session_state.he_thong = HeThongXepHang()
    st.session_state.df_all_10000 = None
    st.session_state.batch_index = 0

ht = st.session_state.he_thong

def doc_du_lieu_tu_dong():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.csv'))]
    if not files:
        return None, "❌ Không tìm thấy file dữ liệu (.xlsx hoặc .csv) nào trong kho chứa GitHub!"

    target_file = None
    for f in files:
        if '10000' in f or 'khach' in f.lower() or 'dữ liệu' in f.lower() or 'du_lieu' in f.lower():
            target_file = f
            break
    if not target_file:
        target_file = files[0]

    try:
        if target_file.endswith(('.xlsx', '.xls')):
            df_raw = pd.read_excel(target_file)
        else:
            df_raw = pd.read_csv(target_file)

        df_raw.columns = [str(c).strip() for c in df_raw.columns]

        col_map = {}
        for c in df_raw.columns:
            c_u = c.upper()
            if 'STT' in c_u: col_map['stt'] = c
            elif 'MÃ' in c_u or 'MA' in c_u: col_map['ma_kh'] = c
            elif 'HỌ' in c_u or 'HO' in c_u or 'TÊN' in c_u or 'TEN' in c_u: col_map['ho_ten'] = c
            elif 'LOẠI' in c_u or 'LOAI' in c_u or 'GD' in c_u: col_map['loai_gd'] = c
            elif 'THỜI GIAN' in c_u or 'THOI GIAN' in c_u or 'TIME' in c_u: col_map['thoi_gian_den'] = c
            elif 'TIỀN' in c_u or 'TIEN' in c_u or 'SỐ' in c_u or 'SO' in c_u: col_map['so_tien'] = c

        df_clean = pd.DataFrame({
            'stt': pd.to_numeric(df_raw[col_map.get('stt', df_raw.columns[0])], errors='coerce').fillna(0).astype(int),
            'ma_kh': df_raw[col_map.get('ma_kh', df_raw.columns[1])].astype(str).str.strip().str.upper(),
            'ho_ten': df_raw[col_map.get('ho_ten', df_raw.columns[2])].astype(str).str.strip().str.title(),
            'loai_gd': df_raw[col_map.get('loai_gd', df_raw.columns[3])].astype(str).str.strip(),
            'thoi_gian_den': pd.to_datetime(df_raw[col_map.get('thoi_gian_den', df_raw.columns[4])], errors='coerce'),
            'so_tien': pd.to_numeric(df_raw[col_map.get('so_tien', df_raw.columns[5])], errors='coerce').fillna(0)
        })

        df_clean = df_clean.sort_values(by=['thoi_gian_den', 'stt']).reset_index(drop=True)
        return df_clean, f"✅ Đã nạp thành công file: {target_file}"
    except Exception as e:
        return None, f"⚠️ Lỗi đọc file {target_file}: {e}."

if st.session_state.df_all_10000 is None:
    df_loaded, msg = doc_du_lieu_tu_dong()
    if df_loaded is not None:
        st.session_state.df_all_10000 = df_loaded
        batch_1 = st.session_state.df_all_10000.iloc[0:100]
        count = 0
        for _, r in batch_1.iterrows():
            ok, _ = ht.lay_so_thu_tu(r['ma_kh'], r['ho_ten'], r['loai_gd'], r['so_tien'], r['thoi_gian_den'])
            if ok: count += 1
        st.toast(f"{msg} ({count} khách đợt 1)!")
    else:
        st.error(msg)

def nap_100_khach_tiep_theo():
    if st.session_state.df_all_10000 is not None:
        st.session_state.batch_index += 1
        start_idx = st.session_state.batch_index * 100
        end_idx = start_idx + 100
        next_batch = st.session_state.df_all_10000.iloc[start_idx:end_idx]

        if len(next_batch) > 0:
            count = 0
            for _, r in next_batch.iterrows():
                ok, _ = ht.lay_so_thu_tu(r['ma_kh'], r['ho_ten'], r['loai_gd'], r['so_tien'], r['thoi_gian_den'])
                if ok: count += 1
            st.toast(f"✅ Đã nạp đợt {st.session_state.batch_index + 1} ({count} khách)!")
        else:
            st.warning("⚠️ Đã nạp toàn bộ 10.000 khách hàng!")

# ==============================================================================
# 3. GIAO DIỆN STREAMLIT MAIN DASHBOARD
# ==============================================================================
st.title("🏦 HỆ THỐNG QUẢN LÝ XẾP HÀNG TẠI QUẦY GIAO DỊCH")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("HÀNG ĐỢI", f"{len(ht.hang_cho)} khách")
c2.metric("TỔNG TRA CỨU", f"{len(ht.tra_cuu_dict)} khách")
c3.metric("ĐÃ PHỤC VỤ", f"{len(ht.lich_su_giao_dich)} khách")
c4.metric("ĐỢT ĐANG XỬ LÝ", f"Đợt {st.session_state.batch_index + 1}")
with c5:
    st.write("")
    if st.button("📥 Nạp 100 khách tiếp"):
        nap_100_khach_tiep_theo()
        st.rerun()

st.markdown("---")

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
            ma_kh = st.text_input("Mã khách hàng (VD: KH10001):")
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
    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        st.subheader("Quầy phục vụ")
        if st.button("🔔 GỌI KHÁCH TIẾP THEO", type="primary", use_container_width=True):
            khach, msg = ht.goi_khach_tiep_theo()
            if khach:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)
                if len(ht.hang_cho) == 0:
                    st.info("💡 Hàng đợi hiện tại đang trống.")
                    if st.button("📥 Nạp ngay 100 khách tiếp theo"):
                        nap_100_khach_tiep_theo()
                        st.rerun()

    with col_g2:
        st.subheader("📋 Danh sách hàng đợi")
        if ht.hang_cho:
            list_cho = list(ht.hang_cho)
            df_cho = pd.DataFrame(list_cho)[['stt', 'ma_kh', 'ho_ten', 'loai_gd', 'so_tien', 'ngay_hoat_dong', 'trang_thai']]
            df_cho_display = df_cho.rename(columns={
                'stt': 'STT',
                'ma_kh': 'MÃ KH',
                'ho_ten': 'HỌ TÊN',
                'loai_gd': 'LOẠI GIAO DỊCH',
                'so_tien': 'SỐ TIỀN',
                'ngay_hoat_dong': 'NGÀY HOẠT ĐỘNG',
                'trang_thai': 'TRẠNG THÁI'
            })
            st.dataframe(df_cho_display, use_container_width=True)
        else:
            st.info("Hàng đợi hiện tại trống.")

# TAB 3: TRA CỨU VỊ TRÍ O(1)
with tab3:
    st.subheader("Tra cứu vị trí khách hàng")
    ma_tim = st.text_input("Nhập mã khách hàng cần tra cứu:", value="KH00001")
    if st.button("🔎 Tra cứu"):
        st.info(ht.tra_cuu_vi_tri(ma_tim))

# TAB 4: THỐNG KÊ & LỊCH SỬ GIAO DỊCH
with tab4:
    st.subheader("📊 Thống kê thời gian chờ & lịch sử")
    if ht.lich_su_giao_dich:
        df_ls = pd.DataFrame(ht.lich_su_giao_dich)
        tg_cho_phut = df_ls['thoi_gian_cho'].tolist()

        avg_sec = int(np.mean(tg_cho_phut) * 60)
        max_sec = int(np.max(tg_cho_phut) * 60)
        min_sec = int(np.min(tg_cho_phut) * 60)

        m1, m2, m3 = st.columns(3)
        m1.metric("⏱️ Thời gian chờ trung bình", f"{avg_sec//60:02d}:{avg_sec%60:02d} ({np.mean(tg_cho_phut):.2f} phút)")
        m2.metric("⏳ Thời gian chờ lâu nhất", f"{max_sec//60:02d}:{max_sec%60:02d} ({np.max(tg_cho_phut):.2f} phút)")
        m3.metric("⚡ Thời gian chờ ngắn nhất", f"{min_sec//60:02d}:{min_sec%60:02d} ({np.min(tg_cho_phut):.2f} phút)")

        st.markdown("---")
        st.write("### Lịch Sử Các Giao Dịch Đã Phục Vụ")
        sap_xep_by = st.selectbox("Sắp xếp danh sách lịch sử theo:", ["stt", "loai_gd", "thoi_gian_cho"])
        df_sorted = df_ls.sort_values(by=sap_xep_by)

        df_sorted_display = df_sorted[['stt', 'ma_kh', 'ho_ten', 'loai_gd', 'so_tien', 'ngay_hoat_dong', 'thoi_gian_cho_str', 'trang_thai']].rename(columns={
            'stt': 'STT',
            'ma_kh': 'MÃ KH',
            'ho_ten': 'HỌ TÊN',
            'loai_gd': 'LOẠI GIAO DỊCH',
            'so_tien': 'SỐ TIỀN',
            'ngay_hoat_dong': 'NGÀY HOẠT ĐỘNG',
            'thoi_gian_cho_str': 'THỜI GIAN CHỜ (MM:SS)',
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
