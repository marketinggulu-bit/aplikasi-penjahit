import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Accounting System", 
    layout="centered", 
    initial_sidebar_state="expanded"  # Memaksa menu sidebar terbuka saat aplikasi dijalankan
)

# --- 2. CSS CUSTOM (STYLING UI) ---
st.markdown("""
    <style>
    /* Mengatur tombol panah menu agar tetap terlihat dan cantik */
    button[kind="headerNoPadding"] {
        color: #1e3a8a !important;
        background-color: #f0f7ff !important;
        border-radius: 50% !important;
        margin-left: 10px !important;
    }

    /* Menyembunyikan elemen default Streamlit yang tidak perlu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: rgba(0,0,0,0) !important;}

    /* Style Mini Card untuk Dashboard */
    .mini-card {
        background: white; padding: 12px 25px; border-radius: 12px; 
        margin-bottom: 8px; border-left: 5px solid #1a365d;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; justify-content: space-between; align-items: center;
    }
    .name-text { font-weight: 700; color: #1a365d; font-size: 1.1rem; flex: 2; }
    .qty-text { color: #718096; font-size: 0.9rem; flex: 1; text-align: center; }
    .price-text { font-weight: 800; color: #2f855a; font-size: 1.2rem; flex: 2; text-align: right; }

    /* CSS Khusus Form Input Produksi (Pink Style) */
    div[data-testid="stForm"] {
        border-radius: 20px;
        border: 2px solid #f8bbd0;
        padding: 30px;
        background-color: #fffafb;
    }
    </style>
    """, unsafe_allow_html=True)

from streamlit_gsheets import GSheetsConnection

# Ini adalah satu-satunya baris koneksi yang Anda butuhkan
conn = st.connection("gsheets", type=GSheetsConnection)

# Hubungkan menggunakan kredensial yang sudah bersih
conn = st.connection("gsheets", type=GSheetsConnection, **creds)

def get_data(sheet_name):
    # Mengambil data real-time dari Google Sheets
    return conn.read(worksheet=sheet_name, ttl=0).dropna(how="all")

def format_rupiah(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.markdown("### 💰 Finansial Penjahit")
    menu = st.radio("MENU UTAMA", ["📊 Dashboard", "📝 Input Kerja", "📂 Laporan", "⚙️ Setup System"])

# --- 5. LOGIKA MENU: DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #1e3a8a; margin-bottom: 20px;'>✨ Ringkasan Eksekutif Utama</h1>", unsafe_allow_html=True)
    df_kerja = get_data("Data_Kerja")
    df_p = get_data("Master_Penjahit")
    
    if not df_kerja.empty:
        df_kerja['Tanggal'] = pd.to_datetime(df_kerja['Tanggal'])
        
        # Area Filter
        st.markdown('<div style="background-color: #f0f7ff; padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #dbeafe;"><h4 style="color: #1e40af; margin-top:0;">🔍 Filter Periode & Personel</h4></div>', unsafe_allow_html=True)
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            tgl_range = st.date_input("Pilih Rentang Waktu", [])
        with c_f2:
            opsi_penjahit = ["SEMUA PENJAHIT"] + sorted(df_p['Nama'].unique().tolist())
            pilih_nama = st.selectbox("Pilih Nama Penjahit", options=opsi_penjahit)

        # Logika Filter
        mask = pd.Series([True] * len(df_kerja))
        if pilih_nama != "SEMUA PENJAHIT":
            mask &= (df_kerja['Nama'] == pilih_nama)
        if len(tgl_range) == 2:
            mask &= (df_kerja['Tanggal'].dt.date >= tgl_range[0]) & (df_kerja['Tanggal'].dt.date <= tgl_range[1])
        
        df_filtered = df_kerja[mask].copy()

# --- UPDATE BAGIAN METRICS DASHBOARD ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #10b981 100%); padding: 30px; border-radius: 25px; text-align: center; color: white; box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);">
                    <span style="font-size: 1.1rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">💰 Total Kewajiban Upah</span><br>
                    <span style="font-size: 2.2rem; font-weight: 900;">{format_rupiah(df_filtered['Total_Upah'].sum())}</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col_m2:
            # MENGHITUNG TOTAL PERSONEL UNIK SESUAI FILTER
            total_personel = df_filtered['Nama'].nunique()
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 25px; text-align: center; color: white; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);">
                    <span style="font-size: 1.1rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">👥 Total Personel Aktif</span><br>
                    <span style="font-size: 2.2rem; font-weight: 900;">{total_personel} Orang</span>
                </div>
            """, unsafe_allow_html=True)

        # PASTIKAN BARIS DI BAWAH INI SEJAJAR DENGAN 'st.markdown("<br>", ...)' DI ATAS
        st.markdown("<br><h3 style='color: #1e3a8a;'>👥 Rincian Per Personel</h3>", unsafe_allow_html=True)
        rekap = df_filtered.groupby('Nama').agg({'Qty':'sum', 'Total_Upah':'sum'}).sort_values('Total_Upah', ascending=False).reset_index()
        
        for index, row in rekap.iterrows():
            border_color = "#10b981" if index % 2 == 0 else "#3b82f6"
            st.markdown(f"""
                <div style="background: white; padding: 18px 30px; border-radius: 18px; margin-bottom: 12px; border-left: 8px solid {border_color}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <span style="color: #64748b; font-size: 0.8rem; font-weight: bold;">NAMA PERSONEL</span><br>
                            <span style="color: #1e293b; font-size: 1.2rem; font-weight: 800;">{row['Nama'].upper()}</span>
                        </div>
                        <div style="flex: 1; text-align: center; background: #f8fafc; padding: 10px; border-radius: 12px;">
                            <span style="color: #64748b; font-size: 0.7rem; font-weight: bold;">VOLUME</span><br>
                            <span style="color: #334155; font-size: 1.1rem; font-weight: 700;">{int(row['Qty'])} Pcs</span>
                        </div>
                        <div style="flex: 2; text-align: right;">
                            <span style="color: #64748b; font-size: 0.8rem; font-weight: bold;">UPAH TERAKUMULASI</span><br>
                            <span style="color: {border_color}; font-size: 1.4rem; font-weight: 900;">{format_rupiah(row['Total_Upah'])}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True) 
    else:
        st.info("Menunggu kiriman data dari Google Sheets...")

# --- 6. LOGIKA MENU: INPUT KERJA ---
elif menu == "📝 Input Kerja":
    st.markdown("<h1 style='text-align: center; color: #d63384;'>🌸 Form Pencatatan Produksi</h1>", unsafe_allow_html=True)
    df_p = get_data("Master_Penjahit")
    df_h = get_data("Master_Harga")
    
    with st.form("input_form_fix", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: tgl = st.date_input("📅 Tanggal Kerja", datetime.now())
        with c2: nama = st.selectbox("👤 Pilih Nama Penjahit", df_p['Nama'].unique())
        
        st.markdown("<br><h5 style='color: #d63384;'>📋 Detail Item Pekerjaan</h5>", unsafe_allow_html=True)
        items = []
        for i in range(5):
            col_item, col_qty = st.columns([3, 1])
            with col_item: job = st.selectbox(f"Jenis Pekerjaan {i+1}", ["-- Pilih Pekerjaan --"] + df_h['Pekerjaan'].tolist(), key=f"j_{i}")
            with col_qty: qty = st.number_input(f"Jumlah (Pcs)", min_value=0, step=1, key=f"q_{i}")
            st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #ffe1ec;'>", unsafe_allow_html=True)
            if job != "-- Pilih Pekerjaan --" and qty > 0:
                stat = df_p[df_p['Nama'] == nama]['Status'].values[0]
                h_row = df_h[df_h['Pekerjaan'] == job]
                val = h_row['Upah_Dalam'].values[0] if stat == "Dalam" else h_row['Upah_Luar'].values[0]
                items.append({"Tanggal": tgl.strftime('%Y-%m-%d'), "Nama": nama, "Pekerjaan": job, "Qty": qty, "Total_Upah": qty * val})
        
        if st.form_submit_button("✨ SIMPAN HASIL KERJA ✨"):
            if items:
                df_old = get_data("Data_Kerja")
                conn.update(worksheet="Data_Kerja", data=pd.concat([df_old, pd.DataFrame(items)], ignore_index=True))
                st.success(f"Selesai! Data {len(items)} item berhasil disimpan."); st.balloons()

# --- 7. LOGIKA MENU: LAPORAN ---
elif menu == "📂 Laporan":
    st.markdown("<h1 style='text-align: center; color: #1a365d;'>📂 Laporan Detail Pekerjaan</h1>", unsafe_allow_html=True)
    df_kerja = get_data("Data_Kerja")
    df_p = get_data("Master_Penjahit")
    
    c_f1, c_f2 = st.columns(2)
    with c_f1: tgl_laporan = st.date_input("Pilih Rentang Tanggal", [])
    with c_f2:
        opsi_p = ["-- PILIH PENJAHIT --"] + sorted(df_p['Nama'].unique().tolist())
        pilih_p = st.selectbox("Nama Penjahit", options=opsi_p, key="filter_laporan")

    if pilih_p != "-- PILIH PENJAHIT --":
        df_kerja['Tanggal'] = pd.to_datetime(df_kerja['Tanggal'])
        mask = (df_kerja['Nama'] == pilih_p)
        if len(tgl_laporan) == 2:
            mask &= (df_kerja['Tanggal'].dt.date >= tgl_laporan[0]) & (df_kerja['Tanggal'].dt.date <= tgl_laporan[1])
        
        df_filtered = df_kerja[mask].sort_values('Tanggal', ascending=False)
        if not df_filtered.empty:
            df_display = df_filtered.copy()
            df_display['Tanggal_Tampil'] = df_display['Tanggal'].dt.strftime('%d %b %Y')
            df_display['Qty'] = df_display['Qty'].map('{:,.0f} Pcs'.format)
            df_display['Total_Upah'] = df_display['Total_Upah'].apply(format_rupiah)
            
            st.dataframe(df_display[['Tanggal_Tampil', 'Pekerjaan', 'Qty', 'Total_Upah']].rename(columns={'Tanggal_Tampil':'📅 Tanggal','Pekerjaan':'🛠️ Pekerjaan','Qty':'📦 Jml','Total_Upah':'💰 Nominal'}), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.markdown(f'<div style="background: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;"><span style="color: #555;">TOTAL HARI KERJA</span><br><span style="font-size: 1.5rem; font-weight: bold; color: #1a365d;">{df_filtered["Tanggal"].nunique()} Hari</span></div>', unsafe_allow_html=True)
            m2.markdown(f'<div style="background: #e6f4ea; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #2f855a;"><span style="color: #2f855a;">TOTAL UPAH DITERIMA</span><br><span style="font-size: 1.5rem; font-weight: bold; color: #2f855a;">{format_rupiah(df_filtered["Total_Upah"].sum())}</span></div>', unsafe_allow_html=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Laporan')
            st.download_button(label="📥 Simpan Laporan ke Excel (.xlsx)", data=buffer, file_name=f"Laporan_{pilih_p}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("💡 Silakan pilih Nama Penjahit untuk melihat rincian laporan.")

# --- 8. LOGIKA MENU: SETUP SYSTEM (DENGAN LIST DATA) ---
elif menu == "⚙️ Setup System":
    st.markdown("<h1 style='text-align: center; color: #1a365d;'>⚙️ Konfigurasi Master Data</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6c757d;'>Kelola database personel dan skema harga produksi di sini.</p>", unsafe_allow_html=True)
    
    # Membuat Tab untuk memisahkan Penjahit dan Harga
    tab_p, tab_h = st.tabs(["👤 Master Penjahit", "💰 Master Harga"])
    
    # --- TAB 1: MASTER PENJAHIT ---
    with tab_p:
        # 1. Form Input Baru
        with st.form("form_p", clear_on_submit=True):
            st.markdown("### ➕ Tambah Penjahit Baru")
            col_nama, col_status = st.columns([2, 1])
            n = col_nama.text_input("Nama Lengkap Penjahit")
            s = col_status.selectbox("Kategori Upah", ["Dalam", "Luar"])
            
            if st.form_submit_button("✨ Daftarkan Penjahit"):
                if n:
                    df_p = get_data("Master_Penjahit")
                    # Mencegah nama ganda
                    if n in df_p['Nama'].values:
                        st.error(f"Nama {n} sudah ada di daftar!")
                    else:
                        new_row = pd.DataFrame([{"Nama": n, "Status": s}])
                        conn.update(worksheet="Master_Penjahit", data=pd.concat([df_p, new_row], ignore_index=True))
                        st.success(f"Berhasil! {n} resmi terdaftar."); st.rerun()
                else:
                    st.warning("Nama tidak boleh kosong ya!")

        st.markdown("---")
        
        # 2. LIST DATA PENJAHIT (Menggunakan Expander agar rapi)
        with st.expander("📋 Lihat & Kelola Daftar Penjahit Saat Ini"):
            df_list_p = get_data("Master_Penjahit")
            if not df_list_p.empty:
                # Menampilkan tabel yang bisa diatur lebarnya secara otomatis
                st.dataframe(df_list_p, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data penjahit.")

    # --- TAB 2: MASTER HARGA ---
    with tab_h:
        # 1. Form Input Harga Baru
        with st.form("form_h", clear_on_submit=True):
            st.markdown("### ➕ Tambah Skema Pekerjaan")
            p = st.text_input("Deskripsi Pekerjaan (Contoh: Jahit Kemeja)")
            c1, c2 = st.columns(2)
            u_d = c1.number_input("Upah Orang DALAM (Rp)", min_value=0, step=500)
            u_l = c2.number_input("Upah Orang LUAR (Rp)", min_value=0, step=500)
            
            if st.form_submit_button("💎 Simpan Master Harga"):
                if p:
                    df_h = get_data("Master_Harga")
                    new_row_h = pd.DataFrame([{"Pekerjaan": p, "Upah_Dalam": u_d, "Upah_Luar": u_l}])
                    conn.update(worksheet="Master_Harga", data=pd.concat([df_h, new_row_h], ignore_index=True))
                    st.success(f"Selesai! Harga '{p}' sudah disimpan."); st.rerun()
                else:
                    st.warning("Deskripsi pekerjaan diisi dulu ya!")

        st.markdown("---")
        
        # 2. LIST DATA HARGA
        with st.expander("📋 Lihat & Kelola Daftar Skema Harga"):
            df_list_h = get_data("Master_Harga")
            if not df_list_h.empty:
                # Membuat tampilan harga lebih cantik dengan format rupiah
                df_view_h = df_list_h.copy()
                df_view_h['Upah_Dalam'] = df_view_h['Upah_Dalam'].apply(format_rupiah)
                df_view_h['Upah_Luar'] = df_view_h['Upah_Luar'].apply(format_rupiah)
                st.dataframe(df_view_h, use_container_width=True, hide_index=True)
            else:

                st.info("Daftar harga masih kosong.")










