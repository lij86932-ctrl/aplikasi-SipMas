from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- FUNGSI KONEKSI DATABASE ---
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Kosongkan jika XAMPP default
        database='sipmas_db'
    )

# Decorator untuk proteksi halaman
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Silakan login terlebih dahulu', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTE LOGIN (MEMBACA DATA) ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            session['nama'] = user['nama_lengkap']
            flash(f'Selamat datang, {user["nama_lengkap"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau Password salah!', 'error')
    
    return render_template('login.html')

# --- ROUTE REGISTER (MENYIMPAN DATA) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama = request.form.get('nama')
        nik = request.form.get('nik')
        hp = request.form.get('hp')
        password = request.form.get('password')
        setuju = request.form.get('setuju')

        if not setuju:
            flash('Anda harus menyetujui Syarat & Ketentuan!', 'error')
            return redirect(url_for('register'))

        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, nama_lengkap, nik, no_hp) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (nama, password, nama, nik, hp))
            db.commit() 
            flash('Pendaftaran berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username sudah terdaftar!', 'error')
            return redirect(url_for('register'))
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')

# --- ROUTE DASHBOARD (MENAMPILKAN DATA DARI DB) ---
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['id']
        
        # Hitung statistik
        cursor.execute('SELECT COUNT(*) as total FROM pengaduan WHERE user_id = %s', (user_id,))
        total_pengaduan = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as dalam_proses FROM pengaduan WHERE user_id = %s AND status = %s', (user_id, 'Sedang Diproses'))
        dalam_proses = cursor.fetchone()['dalam_proses']
        
        cursor.execute('SELECT COUNT(*) as selesai FROM pengaduan WHERE user_id = %s AND status = %s', (user_id, 'Selesai'))
        selesai = cursor.fetchone()['selesai']
        
        # Ambil data pengaduan terbaru
        cursor.execute('SELECT id, judul, status, created_at FROM pengaduan WHERE user_id = %s ORDER BY created_at DESC LIMIT 5', (user_id,))
        pengaduan_list = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        stats = {'total_pengaduan': total_pengaduan, 'dalam_proses': dalam_proses, 'selesai': selesai}
        return render_template('dashboard.html', stats=stats, pengaduan_list=pengaduan_list, user_nama=session.get('nama', session['username']))
    except Exception as e:
        # Jika tabel belum dibuat, tampilkan pesan ini
        return f"<h2>Dashboard Error</h2><p>Pastikan tabel 'pengaduan' sudah dibuat di database. Error: {str(e)}</p>"

# --- ROUTE PENGADUAN SAYA ---
@app.route('/pengaduan-saya')
@login_required
def pengaduan_saya():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT id, judul, status, keterangan, created_at FROM pengaduan WHERE user_id = %s ORDER BY created_at DESC', (session['id'],))
        data_pengaduan = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('pengaduan_saya.html', pengaduan_list=data_pengaduan)
    except Exception as e:
        return f"<h2>Error</h2><p>{str(e)}</p>"

# --- ROUTE HAPUS PENGADUAN ---
@app.route('/pengaduan/hapus/<int:id>')
@login_required
def hapus_pengaduan(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('DELETE FROM pengaduan WHERE id = %s AND user_id = %s', (id, session['id']))
        db.commit()
        cursor.close()
        db.close()
        flash('Pengaduan berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Gagal menghapus: {str(e)}', 'error')
    return redirect(url_for('pengaduan_saya'))

# --- ROUTE FORM PENGADUAN (Simpan ke DB) ---
@app.route('/form-pengaduan', methods=['GET', 'POST'])
@login_required
def form_pengaduan():
    if request.method == 'POST':
        judul = request.form.get('judul')
        deskripsi = request.form.get('deskripsi')
        lokasi = request.form.get('lokasi')
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO pengaduan (user_id, judul, deskripsi, lokasi, status)
            VALUES (%s, %s, %s, %s, 'Menunggu Verification')
        ''', (session['id'], judul, deskripsi, lokasi))
        db.commit()
        cursor.close()
        db.close()
        
        flash('Pengaduan berhasil dikirim!', 'success')
        return redirect(url_for('pengaduan_saya'))
    
    return render_template('form_pengaduan.html')

# --- ROUTE TAMBAHAN (Fix Error Sebelumnya) ---
@app.route('/forgot-password')
def forgot_password():
    return "Fitur Lupa Password sedang dalam pengembangan"

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

@app.route('/login-petugas')
def login_petugas():
    # Sementara tampilkan pesan atau buat template login_petugas.html nanti
    return render_template('login_petugas.html') 

@app.route('/riwayat')
@login_required
def riwayat():
    try:
        # 1. Koneksi Database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['id']
        
        # 2. Ambil Data Pengaduan
        cursor.execute('''
            SELECT id, judul, deskripsi, status, keterangan, created_at, updated_at
            FROM pengaduan 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (user_id,))
        riwayat_data = cursor.fetchall()
        
        # 3. Hitung Statistik
        cursor.execute('SELECT COUNT(*) as total FROM pengaduan WHERE user_id = %s', (user_id,))
        total_pengaduan = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as selesai FROM pengaduan WHERE user_id = %s AND status = %s', 
                      (user_id, 'Selesai'))
        selesai_count = cursor.fetchone()['selesai']
        
        cursor.execute('SELECT COUNT(*) as belum_selesai FROM pengaduan WHERE user_id = %s AND status != %s', 
                      (user_id, 'Selesai'))
        belum_selesai_count = cursor.fetchone()['belum_selesai']
        
        cursor.close()
        db.close()
        
        stats = {
            'total': total_pengaduan,
            'selesai': selesai_count,
            'belum_selesai': belum_selesai_count,
            'avg_time': "20:5" 
        }
    
        return render_template('riwayat.html', riwayat_list=riwayat_data, stats=stats)

if __name__ == '__main__':
    app.run(debug=True)