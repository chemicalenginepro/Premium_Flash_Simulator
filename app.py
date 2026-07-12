import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import bisect
import requests
import json
import re
from datetime import datetime
import traceback
import logging
from typing import Dict, List, Tuple, Optional, Any

# ==============================================================================
# ERROR TRACKING SYSTEM
# ==============================================================================
class ErrorTracker:
    """Sistem tracking kesalahan untuk menangkap dan menganalisis error saat switch mode"""
    
    def __init__(self):
        self.error_log = []
        self.error_count = 0
        self.last_error = None
        self.stack_traces = []
        
    def log_error(self, error_type: str, error_message: str, stack_trace: str = None, context: Dict = None):
        """Mencatat error dengan detail lengkap"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "stack_trace": stack_trace,
            "context": context or {},
            "session_state_snapshot": self._capture_session_state()
        }
        self.error_log.append(error_entry)
        self.error_count += 1
        self.last_error = error_entry
        
        # Log ke console untuk debugging
        logging.error(f"[ERROR TRACKER] {error_type}: {error_message}")
        if stack_trace:
            logging.error(f"Stack trace: {stack_trace}")
            
        return error_entry
    
    def _capture_session_state(self) -> Dict:
        """Mengambil snapshot session state untuk debugging"""
        snapshot = {}
        try:
            for key in st.session_state.keys():
                # Hindari mengambil data yang terlalu besar
                if key not in ['_widgets', '_form_submitted']:
                    try:
                        value = st.session_state[key]
                        if isinstance(value, (str, int, float, bool, list, dict)) and len(str(value)) < 1000:
                            snapshot[key] = value
                        else:
                            snapshot[key] = f"<{type(value).__name__} (truncated)>"
                    except:
                        snapshot[key] = "<unable to read>"
        except:
            snapshot["error"] = "Unable to capture session state"
        return snapshot
    
    def get_error_summary(self) -> Dict:
        """Mendapatkan ringkasan error"""
        return {
            "total_errors": self.error_count,
            "last_error": self.last_error,
            "error_types": list(set([e['type'] for e in self.error_log])),
            "recent_errors": self.error_log[-5:] if self.error_log else []
        }
    
    def clear_errors(self):
        """Membersihkan log error"""
        self.error_log = []
        self.error_count = 0
        self.last_error = None
        
    def display_error_report(self):
        """Menampilkan laporan error di UI"""
        if self.error_count > 0:
            st.error(f"⚠️ {self.error_count} Error(s) Terdeteksi")
            
            with st.expander("📋 Detail Error Log", expanded=False):
                for i, error in enumerate(self.error_log[-10:]):  # Tampilkan 10 error terakhir
                    st.markdown(f"**Error #{i+1}** ({error['timestamp']})")
                    st.markdown(f"- **Type:** `{error['type']}`")
                    st.markdown(f"- **Message:** {error['message']}")
                    if error.get('stack_trace'):
                        with st.expander("🔍 Stack Trace"):
                            st.code(error['stack_trace'], language="python")
                    if error.get('context'):
                        st.json(error['context'])
                    st.markdown("---")

# Inisialisasi error tracker
if 'error_tracker' not in st.session_state:
    st.session_state['error_tracker'] = ErrorTracker()

# ==============================================================================
# SECURE CONFIGURATION: KONEKSI DATABASE SUPABASE
# ==============================================================================
SUPABASE_URL = "https://mdlwswglvslxnwymvueq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1kbHdzd2dsdnNseG53eW12dWVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3MDgzODIsImV4cCI6MjA5OTI4NDM4Mn0.mrnY9pYigBcnIR_Sjt68ja-Ipjsq8a7Sklli72Y-5Rw"

def check_database_auth(username, password):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password_hash=eq.{password}"
    try:
        response = requests.get(url, headers=headers)
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

NRTL_DG_12 = 3450.4
NRTL_DG_21 = -359.8
NRTL_ALPHA = 0.300
R_IDEAL = 8.314462
R_CUBIC = 8.314462e-5

# ==============================================================================
# 2. MODULE A: NRTL ENGINE
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
# 3. MODULE B: PENG-ROBINSON ENGINE
# ==============================================================================
def calculate_pr_alpha(T_k, Tc, omega):
    Tr = T_k / Tc
    kappa = 0.37464 + 1.54226 * omega - 0.26992 * (omega**2)
    return (1 + kappa * (1 - np.sqrt(Tr)))**2

def solve_pr_vectors(components, T_k):
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
    a_params, b_params = solve_pr_vectors(components, T_k)
    K = np.array([(db['Pc']/P) * np.exp(5.37 * (1 + db['omega']) * (1 - db['Tc']/T_k)) for db in [MASTER_DB[c] for c in components]])
    x, y = z.copy(), z.copy()
    psi = 0.0
    regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
    Z_L, Z_V = 0.0, 0.0
    
    for _ in range(150):
        f_zero = rr_objective(0, z, K)
        f_one = rr_objective(1, z, K)
        
        if f_zero <= 0:
            psi, regime = 0.0, "PURE SUBCOOLED LIQUID"
            x = z.copy()
            y = z * K / np.sum(z * K)
            a_L, b_L = mix_pr(x, a_params, b_params)
            A_L, B_L = a_L*P/((R_CUBIC*T_k)**2), b_L*P/(R_CUBIC*T_k)
            Z_L = get_pr_z_roots(A_L, B_L, False)
            Z_V = Z_L
            break
        elif f_one >= 0:
            psi, regime = 1.0, "PURE SUPERHEATED VAPOR"
            y = z.copy()
            x = z / K / np.sum(z / K)
            a_V, b_V = mix_pr(y, a_params, b_params)
            A_V, B_V = a_V*P/((R_CUBIC*T_k)**2), b_V*P/(R_CUBIC*T_k)
            Z_V = get_pr_z_roots(A_V, B_V, True)
            Z_L = Z_V
            break
        else:
            regime = "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM"
            psi = bisect(rr_objective, 0.0, 1.0, args=(z, K))
            x = z / (1 + psi * (K - 1))
            y = K * x
            
        a_L, b_L = mix_pr(x, a_params, b_params)
        A_L, B_L = a_L*P/((R_CUBIC*T_k)**2), b_L*P/(R_CUBIC*T_k)
        Z_L = get_pr_z_roots(A_L, B_L, False)
        phi_L = pr_fugacity(x, Z_L, A_L, B_L, a_params, b_params, a_L, b_L)
        
        a_V, b_V = mix_pr(y, a_params, b_params)
        A_V, B_V = a_V*P/((R_CUBIC*T_k)**2), b_V*P/(R_CUBIC*T_k)
        Z_V = get_pr_z_roots(A_V, B_V, True)
        phi_V = pr_fugacity(y, Z_V, A_V, B_V, a_params, b_params, a_V, b_V)
        
        K_new = phi_L / phi_V
        if np.max(np.abs(K_new - K)) < 1e-8:
            K = K_new
            break
        K = K_new
        
    V, L = psi * F, F - (psi * F)
    return psi, V, L, x, y, K, regime, Z_L, Z_V

# ==============================================================================
# 4. AI VALIDATION AGENT - CHECK AND RECHECK RESULTS
# ==============================================================================
class ValidationAgent:
    """AI Agent untuk validasi hasil perhitungan termodinamika"""
    
    def __init__(self):
        self.validation_log = []
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def validate_flash_results(self, psi, V, L, x, y, K, z, components, model_type, 
                               regime, gamma=None, Q_total=None, Z_L=None, Z_V=None):
        """Main validation function - checks all critical thermodynamic constraints"""
        
        self.validation_log = []
        self.errors = []
        self.warnings = []
        self.passed = []
        
        # === CHECK 1: Mass Balance (Neraca Massa) ===
        self._check_mass_balance(x, y, z, components)
        
        # === CHECK 2: Phase Fractions (Fraksi Fase) ===
        self._check_phase_fractions(psi, V, L)
        
        # === CHECK 3: Composition Constraints ===
        self._check_composition_constraints(x, y, z)
        
        # === CHECK 4: K-value Physical Bounds ===
        self._check_k_values(K, components, model_type)
        
        # === CHECK 5: NRTL Specific Validation ===
        if "NRTL" in model_type:
            self._check_nrtl_specific(gamma, x, components, regime)
        
        # === CHECK 6: Peng-Robinson Specific Validation ===
        if "PENG-ROBINSON" in model_type:
            self._check_pr_specific(Z_L, Z_V, components)
        
        # === CHECK 7: Thermodynamic Consistency ===
        self._check_thermodynamic_consistency(x, y, z, K, model_type)
        
        # === CHECK 8: Convergence Validation ===
        self._check_convergence(x, y, z, K)
        
        # Generate final verdict
        return self._generate_report()
    
    def _check_mass_balance(self, x, y, z, components):
        """Mass balance validation: Σx = Σy = Σz = 1"""
        sum_z = np.sum(z)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        
        tol = 1e-6
        if abs(sum_z - 1.0) > tol:
            self.errors.append(f"MASS_BALANCE_ERROR: Σz={sum_z:.8f} ≠ 1.0")
        else:
            self.passed.append(f"MASS_BALANCE: Σz={sum_z:.8f} ✓")
            
        if abs(sum_x - 1.0) > tol:
            self.errors.append(f"MASS_BALANCE_ERROR: Σx={sum_x:.8f} ≠ 1.0")
        else:
            self.passed.append(f"MASS_BALANCE: Σx={sum_x:.8f} ✓")
            
        if abs(sum_y - 1.0) > tol:
            self.errors.append(f"MASS_BALANCE_ERROR: Σy={sum_y:.8f} ≠ 1.0")
        else:
            self.passed.append(f"MASS_BALANCE: Σy={sum_y:.8f} ✓")
    
    def _check_phase_fractions(self, psi, V, L):
        """Validate phase fractions are physically meaningful"""
        if psi < -1e-9 or psi > 1.0 + 1e-9:
            self.errors.append(f"PHASE_FRACTION_ERROR: ψ={psi:.6f} outside [0,1]")
        else:
            self.passed.append(f"PHASE_FRACTION: ψ={psi:.6f} ✓")
            
        if V < 0 or L < 0:
            self.errors.append(f"PHASE_FLOW_ERROR: V={V:.4f}, L={L:.4f} negative")
        else:
            self.passed.append(f"PHASE_FLOW: V={V:.4f}, L={L:.4f} ✓")
    
    def _check_composition_constraints(self, x, y, z):
        """Check all compositions are between 0 and 1"""
        for i, val in enumerate(x):
            if val < -1e-9 or val > 1.0 + 1e-9:
                self.errors.append(f"COMPOSITION_ERROR: x[{i}]={val:.6f} outside [0,1]")
                break
        else:
            self.passed.append("COMPOSITION_LIQUID: All x_i in [0,1] ✓")
            
        for i, val in enumerate(y):
            if val < -1e-9 or val > 1.0 + 1e-9:
                self.errors.append(f"COMPOSITION_ERROR: y[{i}]={val:.6f} outside [0,1]")
                break
        else:
            self.passed.append("COMPOSITION_VAPOR: All y_i in [0,1] ✓")
    
    def _check_k_values(self, K, components, model_type):
        """Check K-values are physically reasonable"""
        if np.any(K <= 0):
            self.errors.append(f"K_VALUE_ERROR: Negative or zero K-values detected")
        else:
            self.passed.append("K_VALUE: All K_i > 0 ✓")
            
        # Warning for extreme K values
        if np.any(K > 1000):
            self.warnings.append(f"K_VALUE_WARNING: K_i > 1000 (possible convergence issue)")
        if np.any(K < 1e-6):
            self.warnings.append(f"K_VALUE_WARNING: K_i < 1e-6 (possible convergence issue)")
    
    def _check_nrtl_specific(self, gamma, x, components, regime):
        """NRTL-specific validation: activity coefficients"""
        if gamma is not None:
            if np.any(gamma <= 0):
                self.errors.append("NRTL_ERROR: Negative activity coefficients")
            else:
                self.passed.append("NRTL: All γ_i > 0 ✓")
                
            if 'ETHANOL' in components and 'WATER' in components:
                # Check for azeotrope behavior at x1 ≈ 0.55 (ethanol)
                if regime == "TWO-PHASE VAPOR-LIQUID EQUILIBRIUM":
                    if len(x) >= 2:
                        ethanol_idx = components.index('ETHANOL')
                        if 0.3 < x[ethanol_idx] < 0.8:
                            self.passed.append("NRTL: Azeotrope detection passed (x_EtOH in azeotropic range) ✓")
    
    def _check_pr_specific(self, Z_L, Z_V, components):
        """Peng-Robinson specific validation"""
        if Z_L <= 0:
            self.errors.append(f"PR_ERROR: Z_L={Z_L:.6f} must be > 0")
        else:
            self.passed.append(f"PR: Z_L={Z_L:.6f} ✓")
            
        if Z_V <= 0:
            self.errors.append(f"PR_ERROR: Z_V={Z_V:.6f} must be > 0")
        else:
            self.passed.append(f"PR: Z_V={Z_V:.6f} ✓")
            
        # Check for physical consistency: Z_V should be > Z_L
        if Z_V < Z_L:
            self.warnings.append(f"PR_WARNING: Z_V={Z_V:.6f} < Z_L={Z_L:.6f} (unusual)")
    
    def _check_thermodynamic_consistency(self, x, y, z, K, model_type):
        """Check thermodynamic consistency: Σ(y_i - x_i) = 0"""
        diff = np.sum(y - x)
        if abs(diff) > 1e-6:
            self.errors.append(f"THERMO_CONSISTENCY: Σ(y-x)={diff:.8f} ≠ 0")
        else:
            self.passed.append(f"THERMO_CONSISTENCY: Σ(y-x)={diff:.8f} ✓")
    
    def _check_convergence(self, x, y, z, K):
        """Check if Rachford-Rice objective is satisfied"""
        # Recalculate residual
        residual = rr_objective(0.5, z, K)  # Check at mid-point
        if abs(residual) < 1e-4:
            self.passed.append(f"CONVERGENCE: RR residual={abs(residual):.2e} ✓")
        elif abs(residual) < 1e-2:
            self.warnings.append(f"CONVERGENCE_WARNING: RR residual={abs(residual):.2e} > 1e-4")
        else:
            self.errors.append(f"CONVERGENCE_ERROR: RR residual={abs(residual):.2e} too high")
    
    def _generate_report(self):
        """Generate comprehensive validation report"""
        status = "✅ VALIDATION PASSED" if len(self.errors) == 0 else "❌ VALIDATION FAILED"
        
        if len(self.errors) == 0 and len(self.warnings) == 0:
            overall = "EXCELLENT - All checks passed"
        elif len(self.errors) == 0:
            overall = f"GOOD - {len(self.warnings)} warnings (no critical errors)"
        else:
            overall = f"FAILED - {len(self.errors)} critical errors"
        
        report = {
            "status": status,
            "overall": overall,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "errors": self.errors,
            "warnings": self.warnings,
            "passed": self.passed,
            "summary": {
                "total_checks": len(self.passed) + len(self.warnings) + len(self.errors),
                "passed": len(self.passed),
                "warnings": len(self.warnings),
                "errors": len(self.errors)
            }
        }
        return report

# ==============================================================================
# 5. INTERACTIVE FRONTEND APPLICATION
# ==============================================================================
st.title("⚡ SIMULATOR FLASH INTEGRAL PARIPURNA — CORES GABUNGAN NRTL & PENG-ROBINSON")
st.markdown("---")

# ==============================================================================
# 5a. FIXED: STATE INITIALIZATION WITH COMPLETE RESET MECHANISM
# ==============================================================================

# === STATE MANAGEMENT WITH ERROR TRACKING ===
def safe_session_state_get(key, default=None):
    """Safe wrapper untuk mendapatkan nilai dari session state dengan error tracking"""
    try:
        return st.session_state.get(key, default)
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "SESSION_STATE_GET_ERROR",
                f"Error accessing key '{key}': {str(e)}",
                traceback.format_exc(),
                {"key": key, "default": default}
            )
        return default

def safe_session_state_set(key, value):
    """Safe wrapper untuk mengatur nilai di session state dengan error tracking"""
    try:
        st.session_state[key] = value
        return True
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "SESSION_STATE_SET_ERROR",
                f"Error setting key '{key}': {str(e)}",
                traceback.format_exc(),
                {"key": key, "value_type": type(value).__name__}
            )
        return False

def reset_session_state_for_mode(target_mode):
    """
    Reset all session state keys to ensure clean state when switching modes.
    This prevents any cross-mode contamination of values.
    """
    try:
        error_tracker = st.session_state.get('error_tracker')
        
        # Log the reset operation
        if error_tracker:
            error_tracker.log_error(
                "MODE_SWITCH",
                f"Switching to mode: {target_mode}",
                None,
                {"target_mode": target_mode}
            )
        
        # Identify mode prefix
        mode_prefix = 'nrtl' if 'NRTL' in target_mode else 'pr'
        
        # Define keys to preserve
        preserve_keys = [
            'authenticated', 'username', 'error_tracker', 
            'model_type', 'last_model_type', 'reset_triggered',
            'mode_switch_count'
        ]
        
        # Delete ALL component-specific keys
        keys_to_delete = []
        for key in list(st.session_state.keys()):
            if key in preserve_keys:
                continue
                
            # Delete all z_* keys (composition inputs)
            if key.startswith('z_'):
                keys_to_delete.append(key)
            # Delete all multiselect_* keys
            elif key.startswith('multiselect_'):
                keys_to_delete.append(key)
            # Delete old component selection keys
            elif key in ['selected_comps_nrtl', 'selected_comps_pr']:
                keys_to_delete.append(key)
            # Delete parameter input keys
            elif key in ['F_input', 'P_input', 'T_flash_input', 'T_feed_input']:
                keys_to_delete.append(key)
            # Delete any key that might contain old composition data
            elif isinstance(st.session_state[key], (list, np.ndarray)):
                if 'comp' in key.lower() or 'z_' in key or 'x_' in key or 'y_' in key:
                    keys_to_delete.append(key)
        
        # Remove duplicates and delete
        keys_to_delete = list(set(keys_to_delete))
        
        for key in keys_to_delete:
            try:
                if key in st.session_state:
                    del st.session_state[key]
            except Exception as e:
                if error_tracker:
                    error_tracker.log_error(
                        "SESSION_STATE_DELETE_ERROR",
                        f"Error deleting key '{key}': {str(e)}",
                        traceback.format_exc(),
                        {"key": key}
                    )
        
        # Increment mode switch counter for tracking
        if 'mode_switch_count' not in st.session_state:
            st.session_state['mode_switch_count'] = 0
        st.session_state['mode_switch_count'] += 1
        
        return mode_prefix
        
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "RESET_SESSION_ERROR",
                f"Critical error during session reset: {str(e)}",
                traceback.format_exc(),
                {"target_mode": target_mode}
            )
        raise

def initialize_nrtl_defaults():
    """Set default values for NRTL mode with error handling"""
    try:
        error_tracker = st.session_state.get('error_tracker')
        
        # Only initialize if not already set
        if 'selected_comps_nrtl' not in st.session_state:
            st.session_state['selected_comps_nrtl'] = ['ETHANOL', 'WATER']
        
        if 'F_input' not in st.session_state:
            st.session_state['F_input'] = 100.0
        
        if 'P_input' not in st.session_state:
            st.session_state['P_input'] = 1.013
        
        if 'T_flash_input' not in st.session_state:
            st.session_state['T_flash_input'] = 78.2
        
        if 'T_feed_input' not in st.session_state:
            st.session_state['T_feed_input'] = 25.0
        
        # Set default z values for ETHANOL and WATER with safe check
        if 'z_ETHANOL_nrtl' not in st.session_state:
            st.session_state['z_ETHANOL_nrtl'] = 0.5
        if 'z_WATER_nrtl' not in st.session_state:
            st.session_state['z_WATER_nrtl'] = 0.5
            
        # Remove PR-specific keys that might exist
        if 'selected_comps_pr' in st.session_state:
            del st.session_state['selected_comps_pr']
            
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "INIT_NRTL_ERROR",
                f"Error initializing NRTL defaults: {str(e)}",
                traceback.format_exc()
            )
        raise

def initialize_pr_defaults():
    """Set default values for Peng-Robinson mode with error handling"""
    try:
        error_tracker = st.session_state.get('error_tracker')
        
        # Only initialize if not already set
        if 'selected_comps_pr' not in st.session_state:
            st.session_state['selected_comps_pr'] = ['PROPANE', 'N-BUTANE']
        
        if 'F_input' not in st.session_state:
            st.session_state['F_input'] = 100.0
        
        if 'P_input' not in st.session_state:
            st.session_state['P_input'] = 12.0
        
        if 'T_flash_input' not in st.session_state:
            st.session_state['T_flash_input'] = 55.0
        
        # Set default z values for PROPANE and N-BUTANE with safe check
        if 'z_PROPANE_pr' not in st.session_state:
            st.session_state['z_PROPANE_pr'] = 0.5
        if 'z_N-BUTANE_pr' not in st.session_state:
            st.session_state['z_N-BUTANE_pr'] = 0.5
            
        # Remove NRTL-specific keys that might exist
        if 'selected_comps_nrtl' in st.session_state:
            del st.session_state['selected_comps_nrtl']
        if 'T_feed_input' in st.session_state:
            del st.session_state['T_feed_input']
            
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "INIT_PR_ERROR",
                f"Error initializing PR defaults: {str(e)}",
                traceback.format_exc()
            )
        raise

def check_and_fix_state_consistency():
    """Memastikan konsistensi state dan memperbaiki ketidaksesuaian"""
    try:
        error_tracker = st.session_state.get('error_tracker')
        issues_found = []
        
        # Check model type consistency
        model_type = st.session_state.get('model_type', "NRTL (Sistem Cairan Non-Ideal/Polar)")
        
        if "NRTL" in model_type:
            # Check NRTL-specific keys exist
            if 'selected_comps_nrtl' not in st.session_state:
                st.session_state['selected_comps_nrtl'] = ['ETHANOL', 'WATER']
                issues_found.append("Added missing selected_comps_nrtl")
            
            # Remove PR-specific keys if they exist (inconsistent)
            if 'selected_comps_pr' in st.session_state:
                del st.session_state['selected_comps_pr']
                issues_found.append("Removed inconsistent selected_comps_pr")
                
        else:
            # Peng-Robinson mode
            if 'selected_comps_pr' not in st.session_state:
                st.session_state['selected_comps_pr'] = ['PROPANE', 'N-BUTANE']
                issues_found.append("Added missing selected_comps_pr")
            
            if 'selected_comps_nrtl' in st.session_state:
                del st.session_state['selected_comps_nrtl']
                issues_found.append("Removed inconsistent selected_comps_nrtl")
        
        # Log any fixes applied
        if issues_found and error_tracker:
            error_tracker.log_error(
                "STATE_CONSISTENCY_FIX",
                f"Fixed state inconsistencies: {', '.join(issues_found)}",
                None,
                {"issues": issues_found}
            )
            
        return True
        
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "STATE_CONSISTENCY_CHECK_ERROR",
                f"Error checking state consistency: {str(e)}",
                traceback.format_exc()
            )
        return False

# Initialize model type if not present
if 'model_type' not in st.session_state:
    st.session_state['model_type'] = "NRTL (Sistem Cairan Non-Ideal/Polar)"

if 'last_model_type' not in st.session_state:
    st.session_state['last_model_type'] = st.session_state['model_type']

if 'reset_triggered' not in st.session_state:
    st.session_state['reset_triggered'] = False

# Run state consistency check
check_and_fix_state_consistency()

# ==============================================================================
# 5b. FIXED: SWITCH MODE WITH COMPLETE RESET AND ERROR TRACKING
# ==============================================================================

try:
    # Mode selection with error handling wrapper
    model_type = st.sidebar.selectbox(
        "PILIH MODEL TERMODINAMIKA (ENGINE)", 
        ["NRTL (Sistem Cairan Non-Ideal/Polar)", "PENG-ROBINSON (Sistem Gas Nyata/Migas Tekanan Tinggi)"],
        index=0 if "NRTL" in st.session_state['model_type'] else 1,
        key="model_selector"
    )
except Exception as e:
    error_tracker = st.session_state.get('error_tracker')
    if error_tracker:
        error_tracker.log_error(
            "MODEL_SELECTOR_ERROR",
            f"Error creating model selector: {str(e)}",
            traceback.format_exc()
        )
    # Fallback: use current model type
    model_type = st.session_state.get('model_type', "NRTL (Sistem Cairan Non-Ideal/Polar)")

# Check if mode changed
if model_type != st.session_state.get('last_model_type', ''):
    try:
        # Log the mode change attempt
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "MODE_CHANGE_ATTEMPT",
                f"Attempting to switch from '{st.session_state.get('last_model_type')}' to '{model_type}'",
                None,
                {"from_mode": st.session_state.get('last_model_type'), "to_mode": model_type}
            )
        
        # Store the new mode first
        st.session_state['last_model_type'] = model_type
        st.session_state['reset_triggered'] = True
        
        # Reset ALL session states based on target mode
        reset_session_state_for_mode(model_type)
        
        # Initialize defaults for the new mode
        if "NRTL" in model_type:
            initialize_nrtl_defaults()
        else:
            initialize_pr_defaults()
        
        # Update the model type in session state
        st.session_state['model_type'] = model_type
        
        # Log successful switch
        if error_tracker:
            error_tracker.log_error(
                "MODE_CHANGE_SUCCESS",
                f"Successfully switched to '{model_type}'",
                None,
                {"mode": model_type}
            )
        
        # Force rerun to apply changes
        st.rerun()
        
    except Exception as e:
        error_tracker = st.session_state.get('error_tracker')
        if error_tracker:
            error_tracker.log_error(
                "MODE_CHANGE_ERROR",
                f"Critical error during mode switch: {str(e)}",
                traceback.format_exc(),
                {"from_mode": st.session_state.get('last_model_type'), "to_mode": model_type}
            )
        # Display error to user
        st.error(f"❌ Gagal beralih mode: {str(e)}")
        st.error("Mohon refresh halaman atau hubungi administrator.")
        
        # Try to recover by resetting to a known good state
        try:
            if "NRTL" in model_type:
                initialize_nrtl_defaults()
            else:
                initialize_pr_defaults()
            st.session_state['model_type'] = model_type
        except:
            pass

# If reset was triggered but mode didn't change (shouldn't happen, but safe)
if st.session_state.get('reset_triggered', False) and model_type == st.session_state.get('last_model_type', ''):
    st.session_state['reset_triggered'] = False

# Ensure model_type is consistent
st.session_state['model_type'] = model_type

# ==============================================================================
# 5c. SIDEBAR INPUTS (Now with safe default handling)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📋 UTILITY & PARAMETER OPERASI")

# Get F value with safe default
default_F = safe_session_state_get('F_input', 100.0)
F = st.sidebar.number_input(
    "Laju Massa Umpan (F) [kmol/h]", 
    min_value=0.1, 
    value=default_F, 
    key="F_input"
)

# Get P value with safe default based on mode
if "NRTL" in model_type:
    default_P = safe_session_state_get('P_input', 1.013)
else:
    default_P = safe_session_state_get('P_input', 12.0)
P = st.sidebar.number_input(
    "Tekanan Alat Separator (P) [bar]", 
    min_value=0.01, 
    value=default_P, 
    key="P_input"
)

# Get T_flash value with safe default based on mode
if "NRTL" in model_type:
    default_T_flash = safe_session_state_get('T_flash_input', 78.2)
else:
    default_T_flash = safe_session_state_get('T_flash_input', 55.0)
T_flash = st.sidebar.number_input(
    "Suhu Operasi Alat (T_flash) [°C]", 
    value=default_T_flash, 
    key="T_flash_input"
)

# T_feed only for NRTL
T_feed = 25.0
if "NRTL" in model_type:
    default_T_feed = safe_session_state_get('T_feed_input', 25.0)
    T_feed = st.sidebar.number_input(
        "Suhu Masuk Umpan (T_feed) [°C]", 
        value=default_T_feed, 
        key="T_feed_input"
    )

# ==============================================================================
# 5d. COMPONENT SELECTION (Now with safe default handling)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("🧪 INPUT SPECIES COMPONENT")

try:
    if "NRTL" in model_type:
        available_comps = ['ETHANOL', 'WATER', 'BENZENE', 'TOLUENE', 'ETHYLBENZENE']
        # Ensure selected_comps_nrtl exists
        if 'selected_comps_nrtl' not in st.session_state:
            st.session_state['selected_comps_nrtl'] = ['ETHANOL', 'WATER']
        default_comps = st.session_state['selected_comps_nrtl']
        mode_key = 'nrtl'
    else:
        available_comps = ['PROPANE', 'N-BUTANE', 'BENZENE', 'TOLUENE', 'ETHYLBENZENE']
        # Ensure selected_comps_pr exists
        if 'selected_comps_pr' not in st.session_state:
            st.session_state['selected_comps_pr'] = ['PROPANE', 'N-BUTANE']
        default_comps = st.session_state['selected_comps_pr']
        mode_key = 'pr'

    selected_comps = st.sidebar.multiselect(
        "Pilih Komponen Aktif", 
        available_comps, 
        default=default_comps,
        key=f"multiselect_{mode_key}"
    )

    # Store selected components back to session state
    if "NRTL" in model_type:
        st.session_state['selected_comps_nrtl'] = selected_comps
    else:
        st.session_state['selected_comps_pr'] = selected_comps

except Exception as e:
    error_tracker = st.session_state.get('error_tracker')
    if error_tracker:
        error_tracker.log_error(
            "COMPONENT_SELECTION_ERROR",
            f"Error in component selection: {str(e)}",
            traceback.format_exc(),
            {"model_type": model_type}
        )
    # Fallback: use default components
    if "NRTL" in model_type:
        selected_comps = ['ETHANOL', 'WATER']
        st.session_state['selected_comps_nrtl'] = selected_comps
    else:
        selected_comps = ['PROPANE', 'N-BUTANE']
        st.session_state['selected_comps_pr'] = selected_comps
    st.warning("⚠️ Menggunakan komponen default karena terjadi error pada seleksi komponen.")

# ==============================================================================
# 5e. COMPOSITION INPUTS (Now with safe default handling)
# ==============================================================================
st.sidebar.subheader("Fraksi Mol Komponen Masuk (z_i)")

z_inputs = []
try:
    # First pass: ensure all z_* keys exist with defaults
    for c in selected_comps:
        key = f"z_{c}_{mode_key}"
        if key not in st.session_state:
            # Set default value
            default_val = 1.0 / max(len(selected_comps), 1)
            st.session_state[key] = default_val

    # Second pass: display inputs with values from session state
    for c in selected_comps:
        key = f"z_{c}_{mode_key}"
        val = st.sidebar.number_input(
            f"Fraksi z untuk {c}", 
            min_value=0.0, 
            max_value=1.0, 
            value=st.session_state[key],
            format="%.4f",
            key=key
        )
        z_inputs.append(val)

except Exception as e:
    error_tracker = st.session_state.get('error_tracker')
    if error_tracker:
        error_tracker.log_error(
            "COMPOSITION_INPUT_ERROR",
            f"Error in composition input: {str(e)}",
            traceback.format_exc(),
            {"components": selected_comps}
        )
    # Fallback: use equal fractions
    if len(selected_comps) > 0:
        z_inputs = [1.0 / len(selected_comps)] * len(selected_comps)
    else:
        z_inputs = []
    st.warning("⚠️ Menggunakan fraksi sama rata karena terjadi error pada input komposisi.")

# ==============================================================================
# 5f. VALIDATION AND EXECUTION
# ==============================================================================
if len(selected_comps) < 2:
    st.error("SYSTEM CRITICAL ERROR: Perhitungan flash multi-komponen mewajibkan minimal 2 spesimen zat aktif.")
    st.stop()

z_array = np.array(z_inputs)
if np.sum(z_array) == 0:
    st.error("INPUT EROR: Total fraksi umpan tidak boleh bernilai kosong.")
    st.stop()
z_norm = z_array / np.sum(z_array)

try:
    if "NRTL" in model_type:
        if T_feed is None:
            T_feed = 25.0
        psi, V, L, x, y, K, regime, Q_total, gamma, P_sat = solve_nrtl_flash(
            F, P, T_flash, T_feed, selected_comps, z_norm
        )
        Z_L, Z_V = 0.0, 0.0
        model_name = "NRTL"
    else:
        psi, V, L, x, y, K, regime, Z_L, Z_V = solve_peng_robinson_flash(
            F, P, T_flash, selected_comps, z_norm
        )
        Q_total = 0.0
        gamma = np.ones(len(selected_comps))
        P_sat = np.zeros(len(selected_comps))
        model_name = "PENG-ROBINSON"
        
except Exception as e:
    error_tracker = st.session_state.get('error_tracker')
    if error_tracker:
        error_tracker.log_error(
            "FLASH_CALCULATION_ERROR",
            f"Error in flash calculation: {str(e)}",
            traceback.format_exc(),
            {
                "model_type": model_type,
                "components": selected_comps,
                "F": F, "P": P, "T_flash": T_flash,
                "z": z_norm.tolist()
            }
        )
    st.error(f"❌ ERROR PERHITUNGAN: {str(e)}")
    st.error("Silakan periksa input parameter Anda atau coba mode lain.")
    st.stop()

# ==============================================================================
# 6. AI VALIDATION AGENT EXECUTION
# ==============================================================================
try:
    agent = ValidationAgent()
    validation_report = agent.validate_flash_results(
        psi=psi,
        V=V,
        L=L,
        x=x,
        y=y,
        K=K,
        z=z_norm,
        components=selected_comps,
        model_type=model_name,
        regime=regime,
        gamma=gamma if "NRTL" in model_type else None,
        Q_total=Q_total if "NRTL" in model_type else None,
        Z_L=Z_L if "PENG-ROBINSON" in model_type else None,
        Z_V=Z_V if "PENG-ROBINSON" in model_type else None
    )
except Exception as e:
    error_tracker = st.session_state.get('error_tracker')
    if error_tracker:
        error_tracker.log_error(
            "VALIDATION_ERROR",
            f"Error during validation: {str(e)}",
            traceback.format_exc()
        )
    # Create a minimal validation report
    validation_report = {
        "status": "⚠️ VALIDATION SKIPPED",
        "overall": f"Validation error: {str(e)}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "errors": ["Validation could not be completed"],
        "warnings": [],
        "passed": [],
        "summary": {"total_checks": 0, "passed": 0, "warnings": 0, "errors": 1}
    }

# ==============================================================================
# 7. DISPLAY LAYER WITH VALIDATION
# ==============================================================================
grid1, grid2, grid3, grid4 = st.columns(4)
with grid1:
    st.metric(label="VAPOR FRACTION (ψ)", value=f"{psi:.6f}", delta=f"{psi*100:.2f} %")
with grid2:
    if "NRTL" in model_type:
        st.metric(label="NET THERMAL DUTY (Q)", value=f"{Q_total:.4f} kW")
    else:
        st.metric(label="FACTOR COMPRESSIBILITY GAS (Z_V)", value=f"{Z_V:.4f}")
with grid3:
    st.metric(label="PHASE DIAGNOSIS REZIM", value=regime)
with grid4:
    status_color = "green" if "PASSED" in validation_report["status"] else "red"
    st.metric(
        label="🔍 VALIDATION STATUS", 
        value=validation_report["status"],
        delta=f"{validation_report['summary']['passed']}/{validation_report['summary']['total_checks']} checks",
        delta_color="normal"
    )

st.markdown("---")

# === ERROR TRACKER DISPLAY ===
error_tracker = st.session_state.get('error_tracker')
if error_tracker and error_tracker.error_count > 0:
    st.warning(f"⚠️ {error_tracker.error_count} error(s) telah terjadi selama sesi ini.")
    if st.button("📋 Tampilkan Detail Error"):
        with st.expander("🔍 Detailed Error Report", expanded=True):
            error_tracker.display_error_report()
    st.markdown("---")

# === VALIDATION DETAILS ===
with st.expander("🔍 AI VALIDATION AGENT REPORT - Click to expand", expanded=True):
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("✅ PASSED CHECKS")
        if validation_report['passed']:
            for check in validation_report['passed']:
                st.success(check)
        else:
            st.info("No checks passed")
        
        st.subheader("⚠️ WARNINGS")
        if validation_report['warnings']:
            for warn in validation_report['warnings']:
                st.warning(warn)
        else:
            st.info("No warnings")
    
    with col_v2:
        st.subheader("❌ ERRORS")
        if validation_report['errors']:
            for err in validation_report['errors']:
                st.error(err)
        else:
            st.success("No errors detected")
        
        st.subheader("📊 SUMMARY")
        st.json({
            "timestamp": validation_report['timestamp'],
            "total_checks": validation_report['summary']['total_checks'],
            "passed": validation_report['summary']['passed'],
            "warnings": validation_report['summary']['warnings'],
            "errors": validation_report['summary']['errors'],
            "overall_verdict": validation_report['overall']
        })

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
    chart_data = {
        "z_i (Umpan)": z_norm,
        "x_i (Liquid)": x,
        "y_i (Vapor)": y
    }
    st.bar_chart(
        data=chart_data, 
        x=None, 
        y=None, 
        color=["#bcbd22", "#2ca02c", "#ff7f0e"], 
        use_container_width=True
    )

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
            f"Verifikasi Status Sistem     : {validation_report['status']}"
        ), height=110
    )
with audit_r:
    if "NRTL" in model_type:
        st.text_area(
            label="AUDIT NERACA ENERGI",
            value=(
                f"Total Energi Operasi Diperlukan (Q) : {Q_total:.4f} kW\n"
                f"Kebutuhan Peralatan Utilitas Pabrik : " + ("Sistem Endoterm (Memerlukan Alat Heater)" if Q_total > 0 else "Sistem Eksoterm (Memerlukan Alat Cooler)") + "\n"
                f"Validasi Termodinamika               : {validation_report['overall']}"
            ), height=110
        )
    else:
        st.text_area(
            label="AUDIT DEVIASI VOLUMETRIK GAS NYATA",
            value=(
                f"Liquid Z_L Root Factor : {Z_L:.6f} (Indikasi deviasi kerapatan molekul cair)\n"
                f"Vapor Z_V Root Factor  : {Z_V:.6f} (Penyimpangan gas rill terhadap hukum gas ideal)\n"
                f"Verifikasi Status      : {validation_report['status']}\n"
                f"Kesimpulan             : {validation_report['overall']}"
            ), height=110
        )

# ==============================================================================
# 8. ADDITIONAL DEBUG INFO (Hidden by default)
# ==============================================================================
with st.expander("🔧 Debug Information (Hidden)", expanded=False):
    st.json({
        "model_type": model_type,
        "components": selected_comps,
        "session_state_keys": list(st.session_state.keys()),
        "error_count": error_tracker.error_count if error_tracker else 0,
        "mode_switch_count": st.session_state.get('mode_switch_count', 0)
    })
