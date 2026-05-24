from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Fungsi koneksi database
def get_db_connection():
    conn = sqlite3.connect('tjkt_assessment.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inisialisasi Database (Jalankan sekali)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buat tabel jika belum ada
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class_level TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS elements 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class_level TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, element_id INTEGER, score REAL, feedback TEXT)''')
    
    # Insert elemen jika kosong
    if cursor.execute("SELECT count(*) FROM elements").fetchone()[0] == 0:
        elements_x = [
            ("Proses bisnis di bidang TJKT", "X"),
            ("Perkembangan teknologi di bidang TJKT", "X"),
            ("Profesi dan Kewirausahaan di bidang TJKT", "X")
        ]
        elements_xi = [
            ("Teknologi Kabel dan Nirkabel", "XI"),
            ("Keamanan Jaringan", "XI"),
            ("Perencanaan dan Pengalamatan Jaringan", "XI")
        ]
        cursor.executemany("INSERT INTO elements (name, class_level) VALUES (?, ?)", elements_x + elements_xi)
    
    conn.commit()
    conn.close()

# API: Input Nilai Praktik
@app.route('/api/score', methods=['POST'])
def add_score():
    data = request.json
    student_id = data.get('student_id')
    element_name = data.get('element_name') # Misal: "Keamanan Jaringan"
    score = data.get('score')
    feedback = data.get('feedback', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Cari ID elemen berdasarkan nama
    element = cursor.execute("SELECT id, class_level FROM elements WHERE name = ?", (element_name,)).fetchone()
    
    if not element:
        return jsonify({"error": "Elemen tidak ditemukan"}), 404

    # Cek apakah siswa sesuai dengan kelas elemen
    student = cursor.execute("SELECT class_level FROM students WHERE id = ?", (student_id,)).fetchone()
    
    if not student:
        return jsonify({"error": "Siswa tidak ditemukan"}), 404
        
    if student['class_level'] != element['class_level']:
        return jsonify({"error": f"Siswa kelas {student['class_level']} tidak bisa dinilai untuk elemen kelas {element['class_level']}"}), 400

    # Simpan nilai
    cursor.execute("INSERT INTO scores (student_id, element_id, score, feedback) VALUES (?, ?, ?, ?)",
                   (student_id, element['id'], score, feedback))
    conn.commit()
    conn.close()

    return jsonify({"message": "Nilai berhasil disimpan"}), 201

# API: Rekap Nilai Siswa
@app.route('/api/student/<int:student_id>/report', methods=['GET'])
def get_report(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT e.name, s.score, s.feedback, e.class_level
        FROM scores s
        JOIN elements e ON s.element_id = e.id
        WHERE s.student_id = ?
    '''
    results = cursor.execute(query, (student_id,)).fetchall()
    conn.close()
    
    report = [{"element": row['name'], "score": row['score'], "feedback": row['feedback'], "kelas": row['class_level']} for row in results]
    return jsonify(report)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)