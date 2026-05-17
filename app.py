from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from flask_bcrypt import Bcrypt
import mysql.connector
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
bcrypt = Bcrypt(app)

# Upload config
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'image', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- FUNGSI KONEKSI DATABASE ---
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Kosongkan jika XAMPP default
        database='sipmas_db'
    )

# Pastikan ada kategori default untuk foreign key complaint.id_category
def get_default_category_id():
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute('SELECT id_category FROM category ORDER BY id_category ASC LIMIT 1')
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute('INSERT INTO category (nama_category) VALUES (%s)', (1,))
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()

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
        
        cursor.execute('SELECT * FROM users WHERE nama = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        # Menggunakan user['password'] sesuai nama kolom di database
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id_user']
            session['username'] = user['nama']
            session['role'] = user.get('role', 'masyarakat')
            flash(f'Selamat datang, {user["nama"]}!', 'success')
            if session['role'] == 'petugas':
                return redirect(url_for('dashboard_petugas'))
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

        if not nama or not password or not nik or not hp:
            flash('Semua kolom wajib diisi!', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            # Kolom di database Anda bernama 'password'
            cursor.execute('''s
                INSERT INTO users (nama, password, nik, no_hp) 
                VALUES (%s, %s, %s, %s)
            ''', (nama, hashed_password, nik, hp))
            db.commit() 
            flash('Pendaftaran berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.IntegrityError:
            flash('NIK atau Nomor HP sudah terdaftar!', 'error')
            return redirect(url_for('register'))
            
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')


@app.route('/register-petugas', methods=['GET', 'POST'])
def register_petugas():
    if request.method == 'POST':
        nama = request.form.get('nama')
        nik = request.form.get('nik')
        hp = request.form.get('hp')
        password = request.form.get('password')
        setuju = request.form.get('setuju')

        if not setuju:
            flash('Anda harus menyetujui Syarat & Ketentuan!', 'error')
            return redirect(url_for('register_petugas'))

        if not nama or not password or not nik or not hp:
            flash('Semua kolom wajib diisi!', 'error')
            return redirect(url_for('register_petugas'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db = get_db_connection()
        cursor = db.cursor()
        try:
            # Cek apakah kolom `role` ada di tabel users
            cursor.execute(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
                ('sipmas_db', 'users', 'role')
            )
            has_role = cursor.fetchone()[0] > 0

            if has_role:
                cursor.execute(
                    'INSERT INTO users (nama, password, nik, no_hp, role) VALUES (%s, %s, %s, %s, %s)',
                    (nama, hashed_password, nik, hp, 'petugas')
                )
            else:
                cursor.execute(
                    'INSERT INTO users (nama, password, nik, no_hp) VALUES (%s, %s, %s, %s)',
                    (nama, hashed_password, nik, hp)
                )
            db.commit()
            flash('Akun petugas berhasil dibuat. Silakan login.', 'success')
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError:
            flash('NIK atau Nomor HP sudah terdaftar!', 'error')
            return redirect(url_for('register_petugas'))

        except Exception as e:
            db.rollback()
            flash(f'Gagal membuat akun petugas: {e}', 'error')
            return redirect(url_for('register_petugas'))

        finally:
            cursor.close()
            db.close()

    # Reuse the same register template; you can create a separate template later if needed
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
        cursor.execute('SELECT COUNT(*) as total FROM complaint WHERE id_user = %s', (user_id,))
        total_complaint = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as dalam_proses FROM complaint WHERE id_user = %s AND status = %s', (user_id, 'Sedang Diproses'))
        dalam_proses = cursor.fetchone()['dalam_proses']
        
        cursor.execute('SELECT COUNT(*) as selesai FROM complaint WHERE id_user = %s AND status = %s', (user_id, 'Selesai'))
        selesai = cursor.fetchone()['selesai']
        
        # Ambil data pengaduan terbaru
        cursor.execute('SELECT id_complaint, title, status, created_at FROM complaint WHERE id_user = %s ORDER BY created_at DESC LIMIT 5', (user_id,))
        pengaduan_list = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        stats = {'total_complaint': total_complaint, 'dalam_proses': dalam_proses, 'selesai': selesai}
        return render_template('dashboard.html', stats=stats, pengaduan_list=pengaduan_list, user_nama=session.get('nama', session['username']))
    except Exception as e:
        # Jika tabel belum dibuat, tampilkan pesan ini
        return f"<h2>Dashboard Error</h2><p>Pastikan tabel 'complaint' sudah dibuat di database. Error: {str(e)}</p>"

@app.route('/dashboard-petugas')
@login_required
def dashboard_petugas():
    if session.get('role') != 'petugas':
        flash('Akses ditolak. Hanya untuk petugas.', 'error')
        return redirect(url_for('dashboard'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['id']

        cursor.execute('SELECT COUNT(*) AS total FROM complaint', ())
        total_complaint = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) AS pending FROM complaint WHERE status = %s', ('pending',))
        pending = cursor.fetchone()['pending']

        cursor.execute('SELECT COUNT(*) AS in_progress FROM complaint WHERE status = %s', ('Sedang Diproses',))
        in_progress = cursor.fetchone()['in_progress']

        cursor.execute('SELECT COUNT(*) AS selesai FROM complaint WHERE status = %s', ('Selesai',))
        selesai = cursor.fetchone()['selesai']

        cursor.close()
        db.close()

        stats = {
            'total_complaint': total_complaint,
            'pending': pending,
            'in_progress': in_progress,
            'selesai': selesai,
            'user_nama': session.get('username')
        }
        return render_template('dashboard_petugas.html', stats=stats)
    except Exception as e:
        return f"<h2>Dashboard Petugas Error</h2><p>{str(e)}</p>"

# --- ROUTE PENGADUAN SAYA ---
@app.route('/pengaduan-saya')
@login_required
def pengaduan_saya():
    try:
        search_query = request.args.get('q', '').strip()
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        if search_query:
            like_query = f"%{search_query}%"
            cursor.execute('''
                SELECT id_complaint, title, status, deskripsi, created_at
                FROM complaint
                WHERE id_user = %s AND (title LIKE %s OR deskripsi LIKE %s)
                ORDER BY created_at DESC
            ''', (session['id'], like_query, like_query))
        else:
            cursor.execute('SELECT id_complaint, title, status, deskripsi, created_at FROM complaint WHERE id_user = %s ORDER BY created_at DESC', (session['id'],))

        data_pengaduan = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('pengaduan_saya.html', pengaduan_list=data_pengaduan, search_query=search_query)
    except Exception as e:
        return f"<h2>Error</h2><p>{str(e)}</p>"

# --- ROUTE HAPUS PENGADUAN ---
@app.route('/pengaduan/hapus/<int:id>')
@login_required
def hapus_pengaduan(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('DELETE FROM complaint WHERE id_complaint = %s AND id_user = %s', (id, session['id']))
        db.commit()
        cursor.close()
        db.close()
        flash('Pengaduan berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Gagal menghapus: {str(e)}', 'error')
    return redirect(url_for('pengaduan_saya'))

@app.route('/pengaduan/<int:id>')
@login_required
def detail_pengaduan(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute('''
            SELECT c.id_complaint AS id, c.id_user, c.title AS judul, c.deskripsi, c.lokasi,
                   c.status, c.attachment, c.anonim, c.created_at, c.updated_at,
                   u.nama AS nama_lengkap, u.nama AS username, u.no_hp AS no_hp
            FROM complaint c
            JOIN users u ON c.id_user = u.id_user
            WHERE c.id_complaint = %s AND c.id_user = %s
        ''', (id, session['id']))
        pengaduan = cursor.fetchone()
        cursor.close()
        db.close()
        if not pengaduan:
            flash('Pengaduan tidak ditemukan atau bukan milik Anda.', 'error')
            return redirect(url_for('pengaduan_saya'))
        return render_template('detail_pengaduan.html', pengaduan=pengaduan)
    except Exception as e:
        print('Error loading detail_pengaduan:', e)
        flash('Terjadi kesalahan saat memuat detail pengaduan.', 'error')
        return redirect(url_for('pengaduan_saya'))

@app.route('/pengaduan/edit/<int:id>')
@login_required
def edit_pengaduan(id):
    flash('Fitur edit pengaduan sedang dalam pengembangan.', 'info')
    return redirect(url_for('pengaduan_saya'))

# --- ROUTE FORM PENGADUAN (Simpan ke DB) ---
@app.route('/form-pengaduan', methods=['GET', 'POST'])
@login_required
def form_pengaduan():
    if request.method == 'POST':
        judul = request.form.get('title')
        deskripsi = request.form.get('deskripsi')
        lokasi = request.form.get('lokasi')

        # File handling
        uploaded_file = request.files.get('file')
        saved_filename = ''

        db = get_db_connection()
        cursor = db.cursor()
        try:
            category_id = get_default_category_id()
            cursor.execute('''
                INSERT INTO complaint (id_user, title, deskripsi, lokasi, status, attachment, id_category)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s)
            ''', (session['id'], judul, deskripsi, lokasi, saved_filename, category_id))
            db.commit()
            inserted_id = cursor.lastrowid

            # Save uploaded file if present
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                name, ext = os.path.splitext(filename)
                new_filename = f"{inserted_id}_{int(time.time())}{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                uploaded_file.save(file_path)
                saved_filename = os.path.join('image', 'uploads', new_filename)

                # update attachment path in DB
                try:
                    cursor.execute('UPDATE complaint SET attachment = %s WHERE id_complaint = %s', (saved_filename, inserted_id))
                    db.commit()
                except Exception as e_up:
                    print('Warning: failed to update attachment in DB:', e_up)

            flash('Pengaduan berhasil dikirim!', 'success')
            return redirect(url_for('pengaduan_saya'))

        except Exception as e:
            db.rollback()
            print('Error inserting pengaduan:', e)
            flash(f'Gagal mengirim pengaduan: {e}', 'error')
            return redirect(url_for('form_pengaduan'))

        finally:
            cursor.close()
            db.close()
    
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

# login admin/petugas (internal)
@app.route('/register-internal-petugas', methods=['GET', 'POST'])
def register_internal_petugas():
    if request.method == 'POST':
        nama = request.form.get('nama')
        password = request.form.get('password')

        # Validasi kolom wajib untuk petugas
        if not nama or not password:
            flash('Semua kolom wajib diisi!', 'error')
            return redirect(url_for('register_internal_petugas'))

        # Enkripsi password menggunakan bcrypt sesuai kode warga kamu
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db = get_db_connection()
        cursor = db.cursor()

        try:
            # Cek apakah nama petugas sudah ada (cek eksplisit untuk diagnosa)
            cursor.execute('SELECT COUNT(*) FROM users WHERE nama = %s', (nama,))
            exists = cursor.fetchone()[0]
            if exists:
                flash('Nama petugas sudah terdaftar!', 'error')
                return redirect(url_for('register_internal_petugas'))

            # Menyimpan data dengan role 'petugas'
            # Jika kolom tidak boleh NULL, simpan string kosong sebagai fallback
            print('Inserting petugas:', nama)
            cursor.execute('''
                INSERT INTO users (nama, password, role, nik, no_hp) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (nama, hashed_password, 'petugas', '', ''))
            db.commit()
            flash('Pendaftaran Petugas berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError as ie:
            # Tampilkan pesan error di konsol untuk diagnosa
            print('IntegrityError on insert petugas:', ie)
            flash('Nama petugas sudah terdaftar atau constraint lain dilanggar.', 'error')
            return redirect(url_for('register_internal_petugas'))

        except Exception as e:
            print('Error saat mendaftar petugas:', e)
            flash(f'Gagal membuat akun petugas: {e}', 'error')
            return redirect(url_for('register_internal_petugas'))

        finally:
            cursor.close()
            db.close()

    return render_template('register_petugas.html')

@app.route('/riwayat')
@login_required
def riwayat():
    db = None
    try:
        # 1. Koneksi Database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['id']
        
        # 2. Ambil Data Pengaduan
        cursor.execute('''
            SELECT id_complaint AS id, title AS judul, deskripsi, status, created_at, updated_at
            FROM complaint 
            WHERE id_user = %s 
            ORDER BY created_at DESC
        ''', (user_id,))
        riwayat_data = cursor.fetchall()
        
        # 3. Hitung Statistik
        cursor.execute('SELECT COUNT(*) as total FROM complaint WHERE id_user = %s', (user_id,))
        total_complaint = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as selesai FROM complaint WHERE id_user = %s AND status = %s', 
                      (user_id, 'Selesai'))
        selesai_count = cursor.fetchone()['selesai']
        
        cursor.execute('SELECT COUNT(*) as belum_selesai FROM complaint WHERE id_user = %s AND status != %s', 
                      (user_id, 'Selesai'))
        belum_selesai_count = cursor.fetchone()['belum_selesai']
        
        stats = {
            'total': total_complaint,
            'selesai': selesai_count,
            'belum_selesai': belum_selesai_count,
            'avg_time': "20:5" 
        }
    
        return render_template('riwayat.html', riwayat_list=riwayat_data, stats=stats)

    except Exception as e:
        # Menangkap error jika ada masalah query atau database
        print(f"Error pada fungsi riwayat: {e}")
        return f"Terjadi kesalahan sistem: {e}", 500

    finally:
        # Menutup database dengan aman, baik sukses maupun error
        if db:
            cursor.close()
            db.close()
            


if __name__ == '__main__':
    app.run(debug=True)