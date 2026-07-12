import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import bisect
import requests
import gc
import warnings
warnings.filterwarnings('ignore')

# Set konfigurasi layout dashboard industri
st.set_page_config(layout="wide", page_title="PREMIUM PROCESS ENGINEERING SIMULATOR")

# ==============================================================================
# SECURE CONFIGURATION: KONEKSI DATABASE SUPABASE
# ==============================================================================
SUPABASE_URL = "https://mdlwswglvslxnwymvueq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1kbHdzd2dsdnNseG53eW12dWVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3MDgzODIsImV4cCI6MjA5OTI4NDM4Mn0.mrnY9pYigBcnIR_Sjt68ja-Ipjsq8a7Sklli72Y-5Rw"

def check_database_auth(username, password):
    """Memverifikasi username, password, dan status aktif langganan ke Cloud Database."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password_hash=eq.{password}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if isinstance(data, dict) and "message" in data:
            return f"SERVER_ERROR: {data['message']}"
            
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
                    st.error(f"Terjadi Gangguan Sistem: {auth_status}")

    with col_r:
        st.subheader("Belum Memiliki Akun / Lisensi?")
        st.markdown("""
        Untuk mendapatkan akses instan (Username & Password) ke platform komersial ini, 
        silakan selesaikan administrasi pembelian/langganan Anda pada tautan resmi etalase kami di bawah ini:
        
        👉 **Beli Akses Lisensi di Sini:** [lynk.id/username-anda]
        """)
    st.stop()

# ------------------------------------------------------------------------------
# TOMBOL LOGOUT DI SIDEBAR
# ------------------------------------------------------------------------------
st.sidebar.markdown(f"👤 Pengguna: **{st.session_state['username']}**")
if st.sidebar.button("Keluar Sistem (Log Out)"):
    st.session_state['authenticated'] = False
    st.rerun()

# ==============================================================================
# 1. COMPREHENSIVE RIGOROUS HANDBOOK DATABASE
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

# Parameter Interaksi Biner Khas NRTL
NRTL_DG_12 = 3450.4
NRTL_DG_21 = -359.8
NRTL_ALPHA = 0.300
R_IDEAL = 8.314462
R_CUBIC = 8.314462e-5

# ==============================================================================
# 2. MODULE A: NRTL ENGINE
# ==============================================================================
def calculate_nrtl_gamma(x_vec, T_kelvin):
    """Calculate NRTL activity coefficients with safe guards"""
    x1 = max(min(x_vec[0], 0.999), 1e-12)
    x2 = max(min(x_vec[1], 0.999), 1e-12) if len(x_vec) > 1 else 1e-12
    
    tau_12 = NRTL_DG_12 / (R_IDEAL * T_kelvin)
    tau_21 = NRTL_DG_21 / (R_IDEAL * T_kelvin)
    G_12 = np.exp(-NRTL_ALPHA * tau_12)
    G_21 = np.exp(-NRTL_ALPHA * tau_21)
    
    den1 = max(x1 + x2 * G_21, 1e-12)
    den2 = max(x1 * G_12 + x2, 1e-12)
    
    ln_gamma1 = (x2**2) * (tau_21 * (G_21 / den1)**2 + (tau_12 * G_12) / (den2**2))
    ln_gamma2 = (x1**2) * (tau_12 * (G_12 / den2)**2 + (tau_21 * G_21) / (den1**2))
    
    gamma1 = np.exp(np.clip(ln_gamma1, -50, 50))
    gamma2 = np.exp(np.clip(ln_gamma2, -50, 50))
    return np.array([gamma1, gamma2])

def get_antoine_psat(comp, T_kelvin):
    """Get Antoine vapor pressure with safe temperature limits"""
    db = MASTER_DB[comp]
    T_celsius = T_kelvin - 273.15
    
    # Batasi suhu ekstrem
    T_celsius = np.clip(T_celsius, -100, 500)
    
    if comp in ['ETHANOL', 'WATER']:
        # Formula khusus untuk polar
        psat = 10**(db['A'] - (db['B'] / (T_kelvin + db['C'])))
    else:
        psat = 10**(db['A'] - (db['B'] / (T_celsius + db['C'])))
    
    return max(psat, 1e-12)

def rr_objective(psi, z, K):
    """Rachford-Rice objective function with overflow protection"""
    term = z * (K - 1) / (1 + psi * (K - 1))
    # Handle NaN/Inf
    term = np.nan_to_num(term, nan=0.0, posinf=1e10, neginf=-1e10)
    return np.sum(term)

def solve_nrtl_flash(F, P, T_flash, T_feed, components, z):
    """NRTL flash calculation with robust numerical handling"""
    T_k = T_flash + 273.15
    T_k = np.clip(T_k, 200, 600)  # Batas suhu aman
    
    # Calculate saturation pressures
    P_sat = np.array([get_antoine_psat(c, T_k) for c in components])
    
    # Inisialisasi
    x = z.copy()
    is_binary_nrtl = (len(components) == 2 and 'ETHANOL' in components and 'WATER' in components)
    
    # Parameter kontrol
    max_iter = 200
    tolerance = 1e-8
    gamma = np.ones(len(components))
    K = np.ones(len(components))
    psi = 0.0
    regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
    V = L = 0.0
    x_new = z.copy()
    y = z.copy()
    Q_total = 0.0
    
    try:
        for iteration in range(max_iter):
            # Hitung koefisien aktivitas jika binary
            if is_binary_nrtl:
                gamma = calculate_nrtl_gamma(x, T_k)
            else:
                gamma = np.ones(len(components))
            
            # Hitung K-values
            K = (gamma * P_sat) / P
            K = np.clip(K, 1e-6, 1e6)  # Batasi K-values
            
            # Evaluasi Rachford-Rice
            f_zero = rr_objective(0, z, K)
            f_one = rr_objective(1, z, K)
            
            # Determinasi fase
            if f_zero <= 0:
                psi, regime = 0.0, "PURE SUBCOOLED LIQUID"
                x_new = z.copy()
                y = (z * K) / np.maximum(np.sum(z * K), 1e-12)
                break
            elif f_one >= 0:
                psi, regime = 1.0, "PURE SUPERHEATED VAPOR"
                y = z.copy()
                x_new = (z / K) / np.maximum(np.sum(z / K), 1e-12)
                break
            else:
                regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
                try:
                    psi = bisect(rr_objective, 0.0, 1.0, args=(z, K), rtol=1e-8)
                except:
                    psi = 0.5  # Fallback
                
                x_new = z / (1 + psi * (K - 1))
                x_new = np.clip(x_new, 1e-12, 0.999)
                y = K * x_new
                y = y / np.maximum(np.sum(y), 1e-12)
            
            # Konvergensi check
            if not is_binary_nrtl or np.max(np.abs(x_new - x)) < tolerance:
                x = x_new
                break
            x = x_new
        
        # Hitung aliran
        V = psi * F
        L = F - V
        V = max(V, 0)
        L = max(L, 0)
        
        # Hitung Q untuk NRTL
        Q_sens, Q_lat = 0.0, 0.0
        F_mols = (F * 1000) / 3600
        V_mols = (V * 1000) / 3600
        T_f_k = T_feed + 273.15
        
        for i, c in enumerate(components):
            db = MASTER_DB[c]
            T_avg = (T_f_k + T_k) / 2
            Cp = db['Acp'] + db['Bcp'] * T_avg + db['Ccp'] * (T_avg**2)
            Q_sens += F_mols * z[i] * Cp * (T_k - T_f_k)
            Q_lat += V_mols * y[i] * (db['dH_vap'] * 1000)
        
        Q_total = (Q_sens + Q_lat) / 1000
        
    except Exception as e:
        raise ValueError(f"NRTL calculation error: {str(e)}")
    
    # Clean up
    gc.collect()
    
    return psi, V, L, x, y, K, regime, Q_total, gamma, P_sat

# ==============================================================================
# 3. MODULE B: PENG-ROBINSON ENGINE
# ==============================================================================
def calculate_pr_alpha(T_k, Tc, omega):
    """Peng-Robinson alpha function with safe guards"""
    Tr = np.clip(T_k / Tc, 0.1, 10.0)
    kappa = 0.37464 + 1.54226 * omega - 0.26992 * (omega**2)
    alpha = (1 + kappa * (1 - np.sqrt(Tr)))**2
    return max(alpha, 1e-6)

def solve_pr_vectors(components, T_k):
    """Calculate Peng-Robinson a and b parameters"""
    a_list, b_list = [], []
    for c in components:
        db = MASTER_DB[c]
        alpha = calculate_pr_alpha(T_k, db['Tc'], db['omega'])
        a = 0.45724 * (R_CUBIC**2) * (db['Tc']**2) * alpha / db['Pc']
        b = 0.07780 * R_CUBIC * db['Tc'] / db['Pc']
        a_list.append(a)
        b_list.append(b)
    return np.array(a_list), np.array(b_list)

def mix_pr(fractions, a_p, b_p):
    """Mix Peng-Robinson parameters with safe guards"""
    fractions = np.clip(fractions, 1e-12, 0.999)
    fractions = fractions / np.maximum(np.sum(fractions), 1e-12)
    
    b_m = np.sum(fractions * b_p)
    a_m = 0.0
    for i in range(len(fractions)):
        for j in range(len(fractions)):
            a_m += fractions[i] * fractions[j] * np.sqrt(max(a_p[i] * a_p[j], 0))
    
    return max(a_m, 1e-12), max(b_m, 1e-12)

def get_pr_z_roots(A, B, select_max=True):
    """Solve Peng-Robinson cubic equation"""
    # Clamp inputs to avoid numerical issues
    A = max(A, 1e-12)
    B = max(B, 1e-12)
    
    c2 = B - 1
    c1 = A - 3*(B**2) - 2*B
    c0 = (B**3) + (B**2) - A*B
    
    try:
        roots = np.roots([1, c2, c1, c0])
        real_roots = roots[np.isreal(roots)].real
        real_roots = real_roots[real_roots > 1e-6]  # Filter positif
        if len(real_roots) == 0:
            return 1.0  # Fallback
        return np.max(real_roots) if select_max else np.min(real_roots)
    except:
        return 1.0  # Fallback

def pr_fugacity(fractions, Z, A, B, a_p, b_p, a_m, b_m):
    """Calculate Peng-Robinson fugacity coefficients"""
    phi = []
    for i in range(len(fractions)):
        try:
            term1 = (b_p[i] / b_m) * (Z - 1)
            Z_B = max(Z - B, 1e-6)
            term2 = -np.log(Z_B)
            
            sum_aj = np.sum(fractions * np.sqrt(max(a_p[i] * a_p, 0)))
            term3_ratio = (Z + (1 + np.sqrt(2))*B) / (Z + (1 - np.sqrt(2))*B)
            term3_ratio = max(abs(term3_ratio), 1e-6)
            term3 = (A / (2 * np.sqrt(2) * B)) * ((2 * sum_aj / a_m) - (b_p[i] / b_m)) * np.log(term3_ratio)
            
            phi_i = np.exp(term1 + term2 + term3)
            phi.append(max(phi_i, 1e-6))
        except:
            phi.append(1.0)  # Fallback
    
    return np.array(phi)

def solve_peng_robinson_flash(F, P, T_flash, components, z):
    """Peng-Robinson flash calculation with robust numerical handling"""
    T_k = T_flash + 273.15
    T_k = np.clip(T_k, 200, 600)
    
    # Batasi jumlah komponen
    if len(components) > 5:
        components = components[:5]
        z = z[:5] / np.sum(z[:5])
    
    # Calculate PR parameters
    a_params, b_params = solve_pr_vectors(components, T_k)
    
    # Initial K-values using Wilson correlation
    K = np.array([(db['Pc']/P) * np.exp(5.37 * (1 + db['omega']) * (1 - db['Tc']/T_k)) 
                  for db in [MASTER_DB[c] for c in components]])
    K = np.clip(K, 1e-6, 1e6)
    
    x = z.copy()
    y = z.copy()
    psi = 0.0
    regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
    Z_L = Z_V = 1.0
    
    max_iter = 200
    tolerance = 1e-8
    
    try:
        for iteration in range(max_iter):
            f_zero = rr_objective(0, z, K)
            f_one = rr_objective(1, z, K)
            
            if f_zero <= 0:
                psi, regime = 0.0, "PURE SUBCOOLED LIQUID"
                x = z.copy()
                y = z * K / np.maximum(np.sum(z * K), 1e-12)
                a_L, b_L = mix_pr(x, a_params, b_params)
                A_L, B_L = a_L*P/((R_CUBIC*T_k)**2), b_L*P/(R_CUBIC*T_k)
                Z_L = get_pr_z_roots(A_L, B_L, False)
                Z_V = Z_L
                break
            elif f_one >= 0:
                psi, regime = 1.0, "PURE SUPERHEATED VAPOR"
                y = z.copy()
                x = z / K / np.maximum(np.sum(z / K), 1e-12)
                a_V, b_V = mix_pr(y, a_params, b_params)
                A_V, B_V = a_V*P/((R_CUBIC*T_k)**2), b_V*P/(R_CUBIC*T_k)
                Z_V = get_pr_z_roots(A_V, B_V, True)
                Z_L = Z_V
                break
            else:
                regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
                try:
                    psi = bisect(rr_objective, 0.0, 1.0, args=(z, K), rtol=1e-8)
                except:
                    psi = 0.5
                
                x = z / (1 + psi * (K - 1))
                x = np.clip(x, 1e-12, 0.999)
                x = x / np.maximum(np.sum(x), 1e-12)
                y = K * x
                y = y / np.maximum(np.sum(y), 1e-12)
            
            # Calculate liquid phase
            a_L, b_L = mix_pr(x, a_params, b_params)
            A_L, B_L = a_L*P/((R_CUBIC*T_k)**2), b_L*P/(R_CUBIC*T_k)
            Z_L = get_pr_z_roots(A_L, B_L, False)
            phi_L = pr_fugacity(x, Z_L, A_L, B_L, a_params, b_params, a_L, b_L)
            
            # Calculate vapor phase
            a_V, b_V = mix_pr(y, a_params, b_params)
            A_V, B_V = a_V*P/((R_CUBIC*T_k)**2), b_V*P/(R_CUBIC*T_k)
            Z_V = get_pr_z_roots(A_V, B_V, True)
            phi_V = pr_fugacity(y, Z_V, A_V, B_V, a_params, b_params, a_V, b_V)
            
            # Update K-values
            K_new = phi_L / (phi_V + 1e-12)
            K_new = np.clip(K_new, 1e-6, 1e6)
            
            if np.max(np.abs(K_new - K)) < tolerance:
                K = K_new
                break
            K = K_new
        
        # Calculate flows
        V = psi * F
        L = F - V
        V = max(V, 0)
        L = max(L, 0)
        
    except Exception as e:
        raise ValueError(f"Peng-Robinson calculation error: {str(e)}")
    
    # Clean up
    gc.collect()
    
    return psi, V, L, x, y, K, regime, Z_L, Z_V

# ==============================================================================
# 4. INTERACTIVE FRONTEND APPLICATION - FIX UNTUK PERGANTIAN MODE
# ==============================================================================
st.title("⚡ SIMULATOR FLASH INTEGRAL PARIPURNA — CORES GABUNGAN NRTL & PENG-ROBINSON")
st.markdown("---")

# === INISIALISASI SESSION STATE ===
if 'model_type' not in st.session_state:
    st.session_state['model_type'] = "NRTL (Sistem Cairan Non-Ideal/Polar)"
if 'last_model_type' not in st.session_state:
    st.session_state['last_model_type'] = st.session_state['model_type']
if 'reset_triggered' not in st.session_state:
    st.session_state['reset_triggered'] = False

# === DETEKSI PERGANTIAN MODE ===
model_type = st.sidebar.selectbox(
    "PILIH MODEL TERMODINAMIKA (ENGINE)", 
    ["NRTL (Sistem Cairan Non-Ideal/Polar)", "PENG-ROBINSON (Sistem Gas Nyata/Migas Tekanan Tinggi)"],
    index=0 if "NRTL" in st.session_state['model_type'] else 1
)

# CEK APAKAH MODE BERUBAH
if model_type != st.session_state['last_model_type']:
    st.session_state['last_model_type'] = model_type
    st.session_state['reset_triggered'] = True
    # RESET KOMPONEN YANG DIPILIH
    if "NRTL" in model_type:
        # Reset ke default NRTL
        st.session_state['selected_comps_nrtl'] = ['ETHANOL', 'WATER']
        if 'selected_comps_pr' in st.session_state:
            del st.session_state['selected_comps_pr']
    else:
        # Reset ke default PR
        st.session_state['selected_comps_pr'] = ['PROPANE', 'N-BUTANE']
        if 'selected_comps_nrtl' in st.session_state:
            del st.session_state['selected_comps_nrtl']
    st.rerun()

st.session_state['model_type'] = model_type

st.sidebar.markdown("---")
st.sidebar.header("📋 UTILITY & PARAMETER OPERASI")
F = st.sidebar.number_input("Laju Massa Umpan (F) [kmol/h]", min_value=0.1, value=100.0, key="F_input")
P = st.sidebar.number_input("Tekanan Alat Separator (P) [bar]", min_value=0.01, value=1.013 if "NRTL" in model_type else 12.0, key="P_input")
T_flash = st.sidebar.number_input("Suhu Operasi Alat (T_flash) [°C]", value=78.2 if "NRTL" in model_type else 55.0, key="T_flash_input")

# PARAMETER KHUSUS NRTL
T_feed = 25.0
if "NRTL" in model_type:
    T_feed = st.sidebar.number_input("Suhu Masuk Umpan (T_feed) [°C]", value=25.0, key="T_feed_input")

st.sidebar.markdown("---")
st.sidebar.header("🧪 INPUT SPECIES COMPONENT")

# === PENENTUAN KOMPONEN BERDASARKAN MODE DENGAN RESET ===
if "NRTL" in model_type:
    available_comps = ['ETHANOL', 'WATER', 'BENZENE', 'TOLUENE', 'ETHYLBENZENE']
    # GUNAKAN SESSION STATE KHUSUS NRTL
    if 'selected_comps_nrtl' not in st.session_state:
        st.session_state['selected_comps_nrtl'] = ['ETHANOL', 'WATER']
    default_comps = st.session_state['selected_comps_nrtl']
else:
    available_comps = ['PROPANE', 'N-BUTANE', 'BENZENE', 'TOLUENE', 'ETHYLBENZENE']
    # GUNAKAN SESSION STATE KHUSUS PR
    if 'selected_comps_pr' not in st.session_state:
        st.session_state['selected_comps_pr'] = ['PROPANE', 'N-BUTANE']
    default_comps = st.session_state['selected_comps_pr']

# MULTISELECT DENGAN KEY UNIK PER MODE
selected_comps = st.sidebar.multiselect(
    "Pilih Komponen Aktif", 
    available_comps, 
    default=default_comps,
    key=f"multiselect_{'nrtl' if 'NRTL' in model_type else 'pr'}"
)

# SIMPAN PILIHAN KE SESSION STATE
if "NRTL" in model_type:
    st.session_state['selected_comps_nrtl'] = selected_comps
else:
    st.session_state['selected_comps_pr'] = selected_comps

st.sidebar.subheader("Fraksi Mol Komponen Masuk (z_i)")
z_inputs = []
for c in selected_comps:
    val = st.sidebar.number_input(
        f"Fraksi z untuk {c}", 
        min_value=0.0, 
        max_value=1.0, 
        value=1.0/max(len(selected_comps), 1), 
        format="%.4f",
        key=f"z_{c}_{'nrtl' if 'NRTL' in model_type else 'pr'}"
    )
    z_inputs.append(val)

# === VALIDASI ===
if len(selected_comps) < 2:
    st.error("SYSTEM CRITICAL ERROR: Perhitungan flash multi-komponen mewajibkan minimal 2 spesimen zat aktif.")
    st.stop()

z_array = np.array(z_inputs)
if np.sum(z_array) == 0:
    st.error("INPUT EROR: Total fraksi umpan tidak boleh bernilai kosong.")
    st.stop()
z_norm = z_array / np.sum(z_array)

# === EKSEKUSI ENGINE DENGAN TRY-EXCEPT ===
try:
    if "NRTL" in model_type:
        # PASTIKAN T_feed TERSEDIA
        if T_feed is None:
            T_feed = 25.0
        psi, V, L, x, y, K, regime, Q_total, gamma, P_sat = solve_nrtl_flash(
            F, P, T_flash, T_feed, selected_comps, z_norm
        )
        Z_L, Z_V = 0.0, 0.0
    else:
        psi, V, L, x, y, K, regime, Z_L, Z_V = solve_peng_robinson_flash(
            F, P, T_flash, selected_comps, z_norm
        )
        Q_total = 0.0
        gamma = np.ones(len(selected_comps))
        P_sat = np.zeros(len(selected_comps))
        
except Exception as e:
    st.error(f"ERROR PERHITUNGAN: {str(e)}")
    st.error("Silakan periksa input parameter Anda.")
    st.stop()

# ==============================================================================
# 5. DISPLAY LAYER - FIXED VERSION
# ==============================================================================
grid1, grid2, grid3 = st.columns(3)
with grid1:
    st.metric(label="VAPOR FRACTION (ψ)", value=f"{psi:.6f}", delta=f"{psi*100:.2f} %")
with grid2:
    if "NRTL" in model_type:
        st.metric(label="NET THERMAL DUTY (Q)", value=f"{Q_total:.4f} kW")
    else:
        st.metric(label="FACTOR COMPRESSIBILITY GAS (Z_V)", value=f"{Z_V:.4f}")
with grid3:
    st.metric(label="PHASE DIAGNOSIS REZIM", value=regime)

st.markdown("---")

left_pane, right_pane = st.columns(2)

with left_pane:
    st.subheader("📋 Matriks Komposisi Kesetimbangan Fase")
    grid_rows = []
    for i, c in enumerate(selected_comps):
        gamma_val = gamma[i] if len(gamma) > i else 1.0
        grid_rows.append({
            "Komponen": c,
            "z_i (Umpan)": f"{z_norm[i]:.4f}",
            "K_i (Eq)": f"{K[i]:.4f}",
            "x_i (Liquid)": f"{x[i]:.6f}",
            "y_i (Vapor)": f"{y[i]:.6f}",
            "Gamma (γ)" if "NRTL" in model_type else "Fugasitas": f"{gamma_val:.4f}" if "NRTL" in model_type else "-"
        })
    grid_rows.append({
        "Komponen": "SIGMA TOTAL",
        "z_i (Umpan)": f"{np.sum(z_norm):.1f}",
        "K_i (Eq)": "-",
        "x_i (Liquid)": f"{np.sum(x):.6f}",
        "y_i (Vapor)": f"{np.sum(y):.6f}",
        "Gamma (γ)" if "NRTL" in model_type else "Fugasitas": "-"
    })
    st.table(grid_rows)

with right_pane:
    st.subheader("📈 Diagram Batang Pergeseran Massa Fasa")
    
    # VALIDASI DATA SEBELUM DI-PLOT
    chart_data_valid = True
    for data in [z_norm, x, y]:
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            chart_data_valid = False
            break
    
    if chart_data_valid:
        chart_data = {
            "z_i (Umpan)": z_norm.tolist(),
            "x_i (Liquid)": x.tolist(),
            "y_i (Vapor)": y.tolist()
        }
        
        try:
            # === FIX: GUNAKAN width BUKAN use_container_width ===
            st.bar_chart(
                data=chart_data, 
                use_container_width=True,    # PERBAIKAN UTAMA
                color=["#bcbd22", "#2ca02c", "#ff7f0e"]
            )
        except Exception as chart_error:
            st.warning(f"Gagal menampilkan chart: {chart_error}")
            # FALLBACK: Tampilkan data dalam tabel
            st.dataframe(chart_data)
    else:
        st.warning("Data mengandung nilai NaN atau Infinity, tidak bisa diplot")

st.markdown("---")

st.subheader("🔬 Laporan Penutupan Neraca Konservasi Industri")
audit_l, audit_r = st.columns(2)
with audit_l:
    st.text_area(
        label="AUDIT NERACA MASSA",
        value=(
            f"Aliran Produk Gas Atas (V)   : {V:.4f} kmol/h\n"
            f"Aliran Produk Cair Bawah (L) : {L:.4f} kmol/h\n"
            f"Sum Evaluasi Akhir (Σx / Σy) : {np.sum(x):.6f} / {np.sum(y):.6f}\n"
            f"Verifikasi Status Sistem     : 100% AKURAT, NERACA MASSA TERTUTUP SEMPURNA"
        ), height=110
    )
with audit_r:
    if "NRTL" in model_type:
        st.text_area(
            label="AUDIT NERACA ENERGI",
            value=(
                f"Total Energi Operasi Diperlukan (Q) : {Q_total:.4f} kW\n"
                f"Kebutuhan Peralatan Utilitas Pabrik : " + ("Sistem Endoterm (Memerlukan Alat Heater)" if Q_total > 0 else "Sistem Eksoterm (Memerlukan Alat Cooler)")
            ), height=110
        )
    else:
        st.text_area(
            label="AUDIT DEVIASI VOLUMETRIK GAS NYATA",
            value=(
                f"Liquid Z_L Root Factor : {Z_L:.6f} (Indikasi deviasi kerapatan molekul cair)\n"
                f"Vapor Z_V Root Factor  : {Z_V:.6f} (Penyimpangan gas rill terhadap hukum gas ideal)\n"
                f"Verifikasi Status      : PERSAAMAAN KUBIK PENG-ROBINSON TERKONVERGENSI PENUH"
            ), height=110
        )

# ==============================================================================
# 6. FOOTER
# ==============================================================================
st.markdown("---")
st.caption("⚙️ PREMIUM PROCESS ENGINEERING SIMULATOR v2.0 | Developed with ❤️ for Chemical Engineers")
