from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

# ================= LOGIN =================
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user[3], password):
            session['login'] = True
            session['id_user'] = user[0]
            session['role'] = user[5]

            if user[5] == 'petugas':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_user'))
        else:
            flash('Email / Password salah')

    return render_template('login.html')


# ================= REGISTER =================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        no_hp = request.form['no_hp']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('Password tidak sama!')
            return redirect(url_for('register'))

        hash_password = generate_password_hash(password)

        cur = mysql.connection.cursor()

        # CEK EMAIL
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            flash('Email sudah terdaftar!')
            return redirect(url_for('register'))

        # INSERT
        cur.execute("""
            INSERT INTO users(nama,email,no_hp,password)
            VALUES(%s,%s,%s,%s)
        """, (nama,email,no_hp,hash_password))

        mysql.connection.commit()

        flash('Registrasi berhasil!')
        return redirect(url_for('login'))

    return render_template('register.html')


# ================= DASHBOARD USER =================
@app.route('/dashboard_user')
def dashboard_user():
    if 'login' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM complaint WHERE id_user=%s", (session['id_user'],))
    data = cur.fetchall()

    return render_template('dashboard_user.html', data=data)


# ================= DASHBOARD ADMIN =================
@app.route('/dashboard_admin')
def dashboard_admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM complaint")
    data = cur.fetchall()

    return render_template('dashboard_admin.html', data=data)


# ================= TAMBAH PENGADUAN =================
@app.route('/tambah', methods=['GET','POST'])
def tambah():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categories")
    kategori = cur.fetchall()

    if request.method == 'POST':
        title = request.form['title']
        deskripsi = request.form['deskripsi']
        address = request.form['address']
        priority = request.form['priority']
        category_id = request.form['category_id']

        file = request.files['file']
        filename = file.filename
        file.save(os.path.join('static/uploads', filename))

        cur.execute("""
            INSERT INTO complaint(id_user, category_id, title, deskripsi, address, priority, attachment)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (session['id_user'], category_id, title, deskripsi, address, priority, filename))

        mysql.connection.commit()
        return redirect(url_for('dashboard_user'))

    return render_template('tambah_pengaduan.html', kategori=kategori)


# ================= UPDATE STATUS =================
@app.route('/update/<id>')
def update(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE complaint SET status='selesai' WHERE complaint_id=%s", (id,))
    mysql.connection.commit()
    return redirect(url_for('dashboard_admin'))


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)