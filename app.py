import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import bisect
import requests  # Wajib ditambahkan untuk koneksi API ke Supabase

# Set konfigurasi layout dashboard industri
st.set_page_config(layout="wide", page_title="PREMIUM PROCESS ENGINEERING SIMULATOR")

# ==============================================================================
# SECURE CONFIGURATION: KONEKSI DATABASE SUPABASE
# ==============================================================================
# GANTI DENGAN DATA API KEY ANDA SENDIRI DARI LANGKAH 2
SUPABASE_URL = "https://mdlwswglvslxnwymvueq.supabase.co"  # <--- Ganti ini
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1kbHdzd2dsdnNseG53eW12dWVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3MDgzODIsImV4cCI6MjA5OTI4NDM4Mn0.mrnY9pYigBcnIR_Sjt68ja-Ipjsq8a7Sklli72Y-5Rw"            # <--- Ganti ini

def check_database_auth(username, password):
    """Memverifikasi username, password, dan status aktif langganan ke Cloud Database."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password_hash=eq.{password}"
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # JIKA SERVER MEMBALAS DENGAN ERROR DICTIONARY (Bukan List)
        if isinstance(data, dict) and "message" in data:
            return f"SERVER_ERROR: {data['message']}"
            
        # JIKA SERVER BERHASIL MENGEMBALIKAN DATA LIST USER
        if isinstance(data, list) and len(data) > 0:
            user_record = data[0]
            if user_record.get('is_active', False):
                return "SUCCESS"
            else:
                return "EXPIRED"
        return "FAILED"
    except Exception as e:
        return f"KONEKSI_ERROR: {str(e)}"

# ==============================================================================
# GATEWAY SCREEN: TAMPILAN INTERFAKS LOGIN PENGGUNA
# ==============================================================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔒 ACCESS RESTRICTED - PREMIUM SIMULATOR")
    st.markdown("Platform ini hanya dapat diakses oleh pengguna terverifikasi/berlangganan.")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Silakan Masuk ke Akun Anda")
        input_user = st.text_input("Username / Email Terdaftar")
        input_pass = st.text_input("Password Akses", type="password")
        btn_login = st.button("Verifikasi Lisensi Akun")
        
        if btn_login:
            if not input_user or not input_pass:
                st.error("Gagal: Username dan password wajib diisi.")
            else:
                auth_status = check_database_auth(input_user, input_pass)
                if auth_status == "SUCCESS":
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = input_user
                    st.rerun()
                elif auth_status == "EXPIRED":
                    st.error("Akses Ditolak: Masa tenggang langganan Anda telah habis (Expired).")
                elif auth_status == "FAILED":
                    st.error("Gagal: Kombinasi Username/Password tidak valid atau belum terdaftar.")
                else:
                    # MENAMPILKAN PESAN ERROR ASLI DARI SUPABASE DI LAYAR WEB STREAMLIT
                    st.error(f"Terjadi Gangguan Sistem: {auth_status}")

    with col_r:
        st.subheader("Belum Memiliki Akun / Lisensi?")
        st.markdown("""
        Untuk mendapatkan akses instan (Username & Password) ke platform komersial ini, 
        silakan selesaikan administrasi pembelian/langganan Anda pada tautan resmi etalase kami di bawah ini:
        
        👉 **Beli Akses Lisensi di Sini:** [lynk.id/username-anda]
        """)
    st.stop() # Hentikan seluruh sisa eksekusi kode di bawah jika belum login sukses

# ------------------------------------------------------------------------------
# TOMBOL LOGOUT DI SIDEBAR (Hanya muncul jika sudah login sukses)
# ------------------------------------------------------------------------------
st.sidebar.markdown(f"👤 Pengguna: **{st.session_state['username']}**")
if st.sidebar.button("Keluar Sistem (Log Out)"):
    st.session_state['authenticated'] = False
    st.rerun()

# ==============================================================================
# LANJUTAN KODE UTAMA ANDA (MASTER_DB, SOLVER NRTL, PR, STREAMLIT UI UTAMA, DLL.)
# ==============================================================================
# Taruh sisa kode lengkap gabungan NRTL & Peng-Robinson yang kemarin tepat di bawah baris ini...


import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import bisect

# Set konfigurasi layout dashboard industri
st.set_page_config(layout="wide", page_title="PREMIUM PROCESS ENGINEERING SIMULATOR")

# ==============================================================================
# 1. COMPREHENSIVE RIGOROUS HANDBOOK DATABASE (NIST / YAWS / DECHEMA)
# Standar data hulu kimia & migas disatukan dalam satu struktur matriks aman
# ==============================================================================
MASTER_DB = {
    'BENZENE': {
        'A': 4.01814, 'B': 1203.831, 'C': 219.976, 'MW': 78.11,
        'Acp': 61.2, 'Bcp': 0.46, 'Ccp': -0.0005, 'dH_vap': 30.72,
        'Tc': 562.1, 'Pc': 48.90, 'omega': 0.210
    },
    'TOLUENE': {
        'A': 4.07827, 'B': 1343.943, 'C': 219.377, 'MW': 92.14,
        'Acp': 82.5, 'Bcp': 0.52, 'Ccp': -0.0006, 'dH_vap': 33.18,
        'Tc': 591.8, 'Pc': 41.10, 'omega': 0.264
    },
    'ETHYLBENZENE': {
        'A': 4.10441, 'B': 1424.255, 'C': 213.206, 'MW': 106.17,
        'Acp': 102.1, 'Bcp': 0.59, 'Ccp': -0.0007, 'dH_vap': 35.57,
        'Tc': 617.2, 'Pc': 36.10, 'omega': 0.303
    },
    'ETHANOL': {
        'A': 5.24677, 'B': 1598.673, 'C': -46.424, 'MW': 46.07,
        'Acp': 75.6, 'Bcp': 0.35, 'Ccp': 0.0, 'dH_vap': 38.56,
        'Tc': 513.9, 'Pc': 61.40, 'omega': 0.645
    },
    'WATER': {
        'A': 5.11564, 'B': 1687.537, 'C': -43.154, 'MW': 18.02,
        'Acp': 75.3, 'Bcp': 0.0, 'Ccp': 0.0, 'dH_vap': 40.66,
        'Tc': 647.1, 'Pc': 220.60, 'omega': 0.344
    },
    'PROPANE': {
        'A': 3.92275, 'B': 803.997,  'C': 247.040, 'MW': 44.10,
        'Acp': 50.1, 'Bcp': 0.35, 'Ccp': -0.0004, 'dH_vap': 19.04,
        'Tc': 369.8, 'Pc': 42.48, 'omega': 0.152
    },
    'N-BUTANE': {
        'A': 3.93266, 'B': 945.453,  'C': 240.210, 'MW': 58.12,
        'Acp': 65.4, 'Bcp': 0.41, 'Ccp': -0.0005, 'dH_vap': 22.44,
        'Tc': 425.1, 'Pc': 37.96, 'omega': 0.200
    }
}

# Parameter Interaksi Biner Khas NRTL untuk sistem non-ideal Etanol-Air (J/mol)
NRTL_DG_12 = 3450.4
NRTL_DG_21 = -359.8
NRTL_ALPHA = 0.300
R_IDEAL = 8.314462  # J/mol.K
R_CUBIC = 8.314462e-5 # m3.bar/mol.K

# ==============================================================================
# 2. MODULE A: RIGOROUS CHEMICAL & AZEOTROPIC NRTL ENGINE
# ==============================================================================
def calculate_nrtl_gamma(x_vec, T_kelvin):
    x1 = max(x_vec[0], 1e-12)
    x2 = max(x_vec[1], 1e-12) if len(x_vec) > 1 else 1e-12
    tau_12 = NRTL_DG_12 / (R_IDEAL * T_kelvin)
    tau_21 = NRTL_DG_21 / (R_IDEAL * T_kelvin)
    G_12 = np.exp(-NRTL_ALPHA * tau_12)
    G_21 = np.exp(-NRTL_ALPHA * tau_21)
    den1 = x1 + x2 * G_21
    den2 = x1 * G_12 + x2
    ln_gamma1 = (x2**2) * (tau_21 * (G_21 / den1)**2 + (tau_12 * G_12) / (den2**2))
    ln_gamma2 = (x1**2) * (tau_12 * (G_12 / den2)**2 + (tau_21 * G_21) / (den1**2))
    return np.array([np.exp(ln_gamma1), np.exp(ln_gamma2)])

def get_antoine_psat(comp, T_kelvin):
    db = MASTER_DB[comp]
    # Konversi untuk penyesuaian basis parameter Antoine lokal/NIST
    if comp in ['ETHANOL', 'WATER']:
        return 10**(db['A'] - (db['B'] / (T_kelvin + db['C'])))
    else:
        T_celsius = T_kelvin - 273.15
        return 10**(db['A'] - (db['B'] / (T_celsius + db['C'])))

def rr_objective(psi, z, K):
    return np.sum(z * (K - 1) / (1 + psi * (K - 1)))

def solve_nrtl_flash(F, P, T_flash, T_feed, components, z):
    T_k = T_flash + 273.15
    P_sat = np.array([get_antoine_psat(c, T_k) for c in components])
    
    # Pendekatan iteratif loop-tunggal atau ganda tergantung jumlah biner komponen
    x = z.copy()
    is_binary_nrtl = (len(components) == 2 and 'ETHANOL' in components and 'WATER' in components)
    
    for _ in range(100):
        if is_binary_nrtl:
            gamma = calculate_nrtl_gamma(x, T_k)
        else:
            gamma = np.ones(len(components))
            
        K = (gamma * P_sat) / P
        f_zero = rr_objective(0, z, K)
        f_one = rr_objective(1, z, K)
        
        if f_zero <= 0:
            psi, regime = 0.0, "PURE SUBCOOLED LIQUID"
            x_new = z.copy()
            y = (z * K) / np.sum(z * K)
            break
        elif f_one >= 0:
            psi, regime = 1.0, "PURE SUPERHEATED VAPOR"
            y = z.copy()
            x_new = (z / K) / np.sum(z / K)
            break
        else:
            regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
            psi = bisect(rr_objective, 0.0, 1.0, args=(z, K))
            x_new = z / (1 + psi * (K - 1))
            y = K * x_new
            
        if not is_binary_nrtl or np.max(np.abs(x_new - x)) < 1e-9:
            x = x_new
            break
        x = x_new

    V, L = psi * F, F - (psi * F)
    
    # Perhitungan energi sensitif dan laten termal
    Q_sens, Q_lat = 0.0, 0.0
    F_mols, V_mols = (F * 1000) / 3600, (V * 1000) / 3600
    T_f_k = T_feed + 273.15
    for i, c in enumerate(components):
        db = MASTER_DB[c]
        Cp = db['Acp'] + db['Bcp']*((T_f_k+T_k)/2) + db['Ccp']*(((T_f_k+T_k)/2)**2)
        Q_sens += F_mols * z[i] * Cp * (T_k - T_f_k)
        Q_lat += V_mols * y[i] * (db['dH_vap'] * 1000)
        
    return psi, V, L, x, y, K, regime, (Q_sens + Q_lat) / 1000, gamma, P_sat

# ==============================================================================
# 3. MODULE B: HIGH-PRESSURE CUBIC PENG-ROBINSON ENGINE
# ==============================================================================
def calculate_pr_alpha(T_k, Tc, omega):
    Tr = T_k / Tc
    kappa = 0.37464 + 1.54226 * omega - 0.26992 * (omega**2)
    return (1 + kappa * (1 - np.sqrt(Tr)))**2

def solve_pr_vectors(components, T_k):
    a_p, b_p = [], []
    for c in components:
        db = MASTER_DB[c]
        alpha = calculate_pr_alpha(T_k, db['Tc'], db['omega'])
        a = 0.45724 * (R_CUBIC**2) * (db['Tc']**2) * alpha / db['Pc']
        b = 0.07780 * R_CUBIC * db['Tc'] / db['Pc']
        a_p.append(a)
        b_p.append(b)
    return np.array(a_p), np.array(b_p)

def mix_pr(fractions, a_p, b_p):
    b_m = np.sum(fractions * b_p)
    a_m = 0.0
    for i in range(len(fractions)):
        for j in range(len(fractions)):
            a_m += fractions[i] * fractions[j] * np.sqrt(a_p[i] * a_p[j])
    return a_m, b_m

def get_pr_z_roots(A, B, select_max=True):
    c2 = B - 1
    c1 = A - 3*(B**2) - 2*B
    c0 = (B**3) + (B**2) - A*B
    roots = np.roots([1, c2, c1, c0])
    real_roots = roots[np.isreal(roots)].real
    return np.max(real_roots) if select_max else np.min(real_roots)

def pr_fugacity(fractions, Z, A, B, a_p, b_p, a_m, b_m):
    phi = []
    for i in range(len(fractions)):
        term1 = (b_p[i] / b_m) * (Z - 1)
        term2 = -np.log(max(Z - B, 1e-12))
        sum_aj = np.sum(fractions * np.sqrt(a_p[i] * a_p))
        term3 = (A / (2 * np.sqrt(2) * B)) * ((2 * sum_aj / a_m) - (b_p[i] / b_m)) * np.log(max((Z + (1 + np.sqrt(2))*B) / (Z + (1 - np.sqrt(2))*B), 1e-12))
        phi.append(np.exp(term1 + term2 + term3))
    return np.array(phi)

def solve_peng_robinson_flash(F, P, T_flash, components, z):
    T_k = T_flash + 273.15
    a_p, b_p = solve_pr_vectors(components, T_k)
    
    # Inisialisasi K menggunakan persamaan estimasi Wilson
    K = np.array([(db['Pc']/P) * np.exp(5.37 * (1 + db['omega']) * (1 - db['Tc']/T_k)) for db in [MASTER_DB[c] for c in components]])
    x, y = z.copy(), z.copy()
    
    for _ in range(150):
        f_zero = rr_objective(0, z, K)
        f_one = rr_objective(1, z, K)
        
        if f_zero <= 0:
            psi, regime = 0.0, "PURE SUBCOOLED LIQUID"
            x = z.copy()
            y = z * K / np.sum(z * K)
            Z_L = get_pr_z_roots(mix_pr(x, a_p, b_p)[0]*P/((R_CUBIC*T_k)**2), mix_pr(x, a_p, b_p)[1]*P/(R_CUBIC*T_k), False)
            Z_V = Z_L
            break
        elif f_one >= 0:
            psi, regime = 1.0, "PURE SUPERHEATED VAPOR"
            y = z.copy()
            x = z / K / np.sum(z / K)
            Z_V = get_pr_z_roots(mix_pr(y, a_p, b_p)[0]*P/((R_CUBIC*T_k)**2), mix_pr(y, a_p, b_p)[1]*P/(R_CUBIC*T_k), True)
            Z_L = Z_V
            break
        else:
            regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
            psi = bisect(rr_objective, 0.0, 1.0, args=(z, K))
            x = z / (1 + psi * (K - 1))
            y = K * x
            
        a_L, b_L = mix_pr(x, a_p, b_p)
        A_L, B_L = a_L*P/((R_CUBIC*T_k)**2), b_L*P/(R_CUBIC*T_k)
        Z_L = get_pr_z_roots(A_L, B_L, False)
        phi_L = pr_fugacity(x, Z_L, A_L, B_L, a_p, b_p, a_L, b_L)
        
        a_V, b_V = mix_pr(y, a_p, b_p)
        A_V, B_V = a_V*P/((R_CUBIC*T_k)**2), b_V*P/(R_CUBIC*T_k)
        Z_V = get_pr_z_roots(A_V, B_V, True)
        phi_V = pr_fugacity(y, Z_V, A_V, B_V, a_p, b_p, a_V, b_V)
        
        K_new = phi_L / phi_V
        if np.max(np.abs(K_new - K)) < 1e-8:
            K = K_new
            break
        K = K_new
        
    V, L = psi * F, F - (psi * F)
    return psi, V, L, x, y, K, regime, Z_L, Z_V

# ==============================================================================
# 4. INTERACTIVE FRONTEND APPLICATION GATEWAY (STREAMLIT LIBRARIES)
# ==============================================================================
st.title("⚡ SIMULATOR FLASH INTEGRAL PARIPURNA — CORES GABUNGAN NRTL & PENG-ROBINSON")
st.markdown("---")

# Seleksi Model Inti Termodinamika
model_type = st.sidebar.selectbox("PILIH MODEL TERMODINAMIKA (ENGINE)", ["NRTL (Sistem Cairan Non-Ideal/Polar)", "PENG-ROBINSON (Sistem Gas Nyata/Migas Tekanan Tinggi)"])

st.sidebar.markdown("---")
st.sidebar.header("📋 UTILITY & PARAMETER OPERASI")
F = st.sidebar.number_input("Laju Massa Umpan (F) [kmol/h]", min_value=0.1, value=100.0)
P = st.sidebar.number_input("Tekanan Alat Separator (P) [bar]", min_value=0.01, value=1.013 if "NRTL" in model_type else 12.0)



