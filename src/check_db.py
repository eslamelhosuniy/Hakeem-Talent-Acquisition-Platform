import sqlite3
import os

# تحديد مسار قاعدة البيانات (داخل فولدر src)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "database.db")

def print_table(rows):
    """دالة مساعدة لطباعة البيانات بشكل منظم"""
    if not rows:
        print("\n📭 No records found.")
        return
    
    print(f"\n✅ Found ({len(rows)}) records:")
    header = f"{'ID':<4} | {'Job Title':<20} | {'Candidate Name':<20} | {'Email':<25} | {'Skills Preview'}"
    print(header)
    print("-" * len(header))
    
    for row in rows:
        r = [str(i) if i else "N/A" for i in row]
        skills_preview = (r[5][:30] + "..") if len(r[5]) > 30 else r[5]
        print(f"{r[0]:<4} | {r[1]:<20} | {r[2]:<20} | {r[3]:<25} | {skills_preview}")

def search_db():
    if not os.path.exists(db_path):
        print(f"❌ Error: Database file NOT FOUND at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        while True:
            print("\n--- 📊 Database Inspector Menu ---")
            print("1. View All CVs")
            print("2. Search by Candidate Name")
            print("3. Search by Job Title")
            print("4. Exit")
            
            choice = input("\nChoose an option (1-4): ")

            if choice == '1':
                cursor.execute("SELECT id, job_title, candidate_name, email, phone, skills FROM cvs")
                print_table(cursor.fetchall())

            elif choice == '2':
                name = input("Enter candidate name to search for: ")
                cursor.execute("SELECT id, job_title, candidate_name, email, phone, skills FROM cvs WHERE candidate_name LIKE ?", (f"%{name}%",))
                print_table(cursor.fetchall())

            elif choice == '3':
                job = input("Enter job title to search for: ")
                cursor.execute("SELECT id, job_title, candidate_name, email, phone, skills FROM cvs WHERE job_title LIKE ?", (f"%{job}%",))
                print_table(cursor.fetchall())

            elif choice == '4':
                print("👋 Exiting database inspector. Goodbye!")
                break
            else:
                print("⚠️ Invalid choice, please try again.")

        conn.close()
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    search_db()