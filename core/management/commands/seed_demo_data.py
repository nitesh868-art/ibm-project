"""
Management command: Populate database with comprehensive demo data.
Run: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with comprehensive demo data (students, companies, quizzes, etc.)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n[*] Seeding demo data...\n"))

        self._create_admin()
        self._create_students()
        self._create_faculty()
        self._create_companies()
        self._create_subjects_and_questions()
        self._create_notifications()

        self.stdout.write(self.style.SUCCESS("\n[*] Demo data seeded successfully!"))

    def _create_admin(self):
        # Admin Account 1: Standard admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", email="admin@placementpro.com",
                password="admin@123", first_name="System", last_name="Admin",
                role="admin", is_email_verified=True,
            )
            self.stdout.write(self.style.SUCCESS("  [OK] Admin: admin / admin@123"))

        # Admin Account: Requested Owner Admin (123@gmail.com)
        admin_email = "123@gmail.com"
        admin_pwd = "1109admin@"
        if not User.objects.filter(email=admin_email).exists() and not User.objects.filter(username=admin_email).exists():
            User.objects.create_superuser(
                username=admin_email, email=admin_email,
                password=admin_pwd, first_name="Owner", last_name="Admin",
                role="admin", is_email_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f"  [OK] Admin: {admin_email}"))

        if not User.objects.filter(username="123").exists():
            User.objects.create_superuser(
                username="123", email="123_alias@gmail.com",
                password=admin_pwd, first_name="Owner", last_name="Admin",
                role="admin", is_email_verified=True,
            )
            self.stdout.write(self.style.SUCCESS("  [OK] Admin Alias: 123"))

    def _create_students(self):
        from accounts.models import StudentProfile
        from studyplanner.models import StudySubject, Goal, DailyStudyLog, Semester

        students_data = [
            {"username": "student_yr1", "first_name": "Aarav", "last_name": "Patel",
             "email": "aarav@college.edu", "roll": "CS24001", "branch": "CSE",
             "year": 1, "cgpa": Decimal("8.0"), "skills": "C, Python basics, Problem solving",
             "streak": 5, "points": 150, "status": "not_placed"},
            {"username": "student_yr2", "first_name": "Sneha", "last_name": "Reddy",
             "email": "sneha@college.edu", "roll": "IT23001", "branch": "IT",
             "year": 2, "cgpa": Decimal("8.4"), "skills": "C++, Data Structures, OOP, SQL",
             "streak": 10, "points": 320, "status": "not_placed"},
            {"username": "student1", "first_name": "Rahul", "last_name": "Sharma",
             "email": "rahul@college.edu", "roll": "CS21001", "branch": "CSE",
             "year": 3, "cgpa": Decimal("8.5"), "skills": "Python, Django, React, SQL, DSA",
             "streak": 14, "points": 450, "status": "not_placed"},
            {"username": "student2", "first_name": "Priya", "last_name": "Verma",
             "email": "priya@college.edu", "roll": "CS21002", "branch": "CSE",
             "year": 3, "cgpa": Decimal("9.1"), "skills": "Java, Spring Boot, DSA, ML, Python",
             "streak": 21, "points": 720, "status": "placed"},
            {"username": "student3", "first_name": "Karthik", "last_name": "Rajan",
             "email": "karthik@college.edu", "roll": "IT21003", "branch": "IT",
             "year": 4, "cgpa": Decimal("7.8"), "skills": "C++, Data Structures, OS, DBMS",
             "streak": 7, "points": 280, "status": "not_placed"},
            {"username": "student4", "first_name": "Anjali", "last_name": "Gupta",
             "email": "anjali@college.edu", "roll": "AIDS21004", "branch": "AIDS",
             "year": 3, "cgpa": Decimal("8.9"), "skills": "Python, TensorFlow, SQL, Statistics, Pandas",
             "streak": 30, "points": 980, "status": "placed"},
            {"username": "student5", "first_name": "Sanjay", "last_name": "Kumar",
             "email": "sanjay@college.edu", "roll": "ECE21005", "branch": "ECE",
             "year": 2, "cgpa": Decimal("7.2"), "skills": "C, Python, Embedded Systems",
             "streak": 3, "points": 120, "status": "not_placed"},
        ]

        for sdata in students_data:
            if User.objects.filter(username=sdata["username"]).exists():
                continue
            user = User.objects.create_user(
                username=sdata["username"], email=sdata["email"],
                password="student@123", first_name=sdata["first_name"],
                last_name=sdata["last_name"], role="student", is_email_verified=True,
            )
            profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={
                "roll_number": sdata["roll"], "branch": sdata["branch"],
                "year": sdata["year"], "semester": sdata["year"] * 2 - 1,
                "cgpa": sdata["cgpa"], "skills": sdata["skills"],
                "study_streak": sdata["streak"], "total_points": sdata["points"],
                "placement_status": sdata["status"], "profile_completion": random.randint(60, 90),
                "last_study_date": date.today(),
            })

            # Create semester
            sem, _ = Semester.objects.get_or_create(student=user, number=sdata["year"] * 2 - 1, defaults={"is_current": True})

            # Add study subjects
            subjects_list = [
                ("Data Structures & Algorithms", "CS301", "#6366f1", 4),
                ("Database Management Systems", "CS302", "#10b981", 3),
                ("Operating Systems", "CS303", "#f59e0b", 4),
                ("Computer Networks", "CS304", "#ef4444", 3),
                ("Software Engineering", "CS305", "#8b5cf6", 3),
            ]
            for sname, scode, scolor, priority in subjects_list:
                StudySubject.objects.get_or_create(
                    student=user, name=sname,
                    defaults={"code": scode, "color": scolor, "priority": priority,
                              "completion_percentage": random.randint(20, 85),
                              "semester": sem, "credits": 4}
                )

            # Study logs for last 14 days
            for i in range(14):
                day = date.today() - timedelta(days=i)
                if random.random() > 0.3:
                    DailyStudyLog.objects.get_or_create(
                        student=user, date=day,
                        defaults={"duration_minutes": random.randint(60, 240)}
                    )

            # Goals
            goals = ["Solve 3 LeetCode problems", "Revise DBMS normalization", "Complete OS process chapter"]
            for g in goals:
                Goal.objects.get_or_create(
                    student=user, title=g,
                    defaults={"goal_type": "daily", "is_completed": False}
                )

            self.stdout.write(self.style.SUCCESS(f"  [OK] Student: {sdata['username']} / student@123"))

    def _create_faculty(self):
        from accounts.models import FacultyProfile
        faculty_data = [
            {"username": "faculty1", "first_name": "Dr. Meera", "last_name": "Nair",
             "email": "meera@college.edu", "emp_id": "FAC001", "dept": "Computer Science",
             "designation": "Associate Professor", "exp": 8},
            {"username": "faculty2", "first_name": "Prof. Arun", "last_name": "Sharma",
             "email": "arun@college.edu", "emp_id": "FAC002", "dept": "Information Technology",
             "designation": "Assistant Professor", "exp": 5},
        ]
        for fdata in faculty_data:
            if User.objects.filter(username=fdata["username"]).exists():
                continue
            user = User.objects.create_user(
                username=fdata["username"], email=fdata["email"],
                password="faculty@123", first_name=fdata["first_name"],
                last_name=fdata["last_name"], role="faculty", is_email_verified=True,
            )
            FacultyProfile.objects.get_or_create(user=user, defaults={
                "employee_id": fdata["emp_id"], "department": fdata["dept"],
                "designation": fdata["designation"], "experience_years": fdata["exp"],
            })
            self.stdout.write(self.style.SUCCESS(f"  [OK] Faculty: {fdata['username']} / faculty@123"))

    def _create_companies(self):
        try:
            from companies.models import Company
        except Exception:
            return

        companies = [
            ("Google", "google.com", "product", 15, 30, "Bangalore"),
            ("Microsoft", "microsoft.com", "product", 20, 45, "Hyderabad"),
            ("Amazon", "amazon.com", "product", 18, 35, "Bangalore"),
            ("TCS", "tcs.com", "service", 3.5, 7.0, "Pan India"),
            ("Infosys", "infosys.com", "service", 3.6, 6.5, "Pan India"),
            ("Wipro", "wipro.com", "service", 3.5, 6.5, "Pan India"),
            ("Accenture", "accenture.com", "mnc", 4.5, 9.0, "Pan India"),
            ("Flipkart", "flipkart.com", "product", 25, 40, "Bangalore"),
            ("Paytm", "paytm.com", "product", 10, 18, "Noida"),
            ("Zomato", "zomato.com", "product", 12, 22, "Gurgaon"),
        ]
        for name, domain, ctype, min_p, max_p, loc in companies:
            Company.objects.get_or_create(
                name=name,
                defaults={"website": f"https://www.{domain}", "company_type": ctype,
                          "min_package": Decimal(str(min_p)), "max_package": Decimal(str(max_p)),
                          "headquarters": loc, "min_cgpa": Decimal("6.0"), "is_active": True}
            )
        self.stdout.write(self.style.SUCCESS(f"  [OK] {len(companies)} companies created"))

    def _create_subjects_and_questions(self):
        try:
            from quiz.models import Subject, Question, MockTest
        except Exception:
            return

        subjects = [
            ("Data Structures", "DSA"), ("Algorithms", "ALGO"),
            ("DBMS", "DBMS"), ("Operating Systems", "OS"),
            ("Computer Networks", "CN"), ("Aptitude", "APT"),
            ("Python Programming", "PY"), ("Object Oriented Programming", "OOP"),
        ]
        q_count = 0
        for sname, scode in subjects:
            subj, _ = Subject.objects.get_or_create(name=sname, defaults={"code": scode})
            questions = self._get_questions(sname)
            for q in questions:
                _, created = Question.objects.get_or_create(
                    subject=subj, question_text=q["q"],
                    defaults={"option_a": q["a"], "option_b": q["b"],
                              "option_c": q["c"], "option_d": q["d"],
                              "correct_answer": q["ans"], "difficulty": q["diff"],
                              "explanation": q.get("exp", "")}
                )
                if created:
                    q_count += 1

        self.stdout.write(self.style.SUCCESS(f"  [OK] {q_count} questions added"))

        # Create demo mock tests
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            tests = [
                ("DSA Fundamentals Test", "placement", 60),
                ("Aptitude Assessment", "aptitude", 45),
                ("Python Basics Quiz", "practice", 30),
                ("DBMS Mock Test", "mock", 40),
            ]
            for title, ttype, duration in tests:
                MockTest.objects.get_or_create(
                    title=title,
                    defaults={"description": f"Practice {title} for placement preparation.",
                              "duration_minutes": duration, "test_type": ttype,
                              "total_marks": 20, "passing_marks": 10,
                              "is_active": True, "is_published": True,
                              "created_by": admin_user,
                              "start_time": timezone.now() - timedelta(days=1),
                              "end_time": timezone.now() + timedelta(days=30)}
                )
            self.stdout.write(self.style.SUCCESS(f"  [OK] {len(tests)} mock tests created"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ! Mock tests: {e}"))

    def _get_questions(self, subject_name):
        questions = {
            "Data Structures": [
                {"q": "What is the time complexity of binary search?", "a": "O(n)", "b": "O(log n)", "c": "O(n log n)", "d": "O(1)", "ans": "B", "diff": "easy", "exp": "Binary search divides the array in half each step, giving O(log n)."},
                {"q": "Which data structure uses LIFO principle?", "a": "Queue", "b": "Array", "c": "Stack", "d": "LinkedList", "ans": "C", "diff": "easy"},
                {"q": "What is the worst-case time complexity of QuickSort?", "a": "O(n log n)", "b": "O(n)", "c": "O(n^2)", "d": "O(log n)", "ans": "C", "diff": "medium"},
                {"q": "A complete binary tree with n nodes has height:", "a": "log n", "b": "n", "c": "n/2", "d": "floor(log2 n)", "ans": "D", "diff": "medium"},
            ],
            "Algorithms": [
                {"q": "Which algorithm is NOT a greedy algorithm?", "a": "Dijkstra's", "b": "Kruskal's", "c": "Merge Sort", "d": "Prim's", "ans": "C", "diff": "medium"},
                {"q": "Dynamic Programming is based on:", "a": "Greedy choice", "b": "Divide and conquer", "c": "Overlapping subproblems", "d": "Backtracking", "ans": "C", "diff": "easy"},
                {"q": "Time complexity of merge sort in all cases:", "a": "O(n^2)", "b": "O(n log n)", "c": "O(log n)", "d": "O(n)", "ans": "B", "diff": "easy"},
            ],
            "DBMS": [
                {"q": "Which normal form removes transitive dependency?", "a": "1NF", "b": "2NF", "c": "3NF", "d": "BCNF", "ans": "C", "diff": "medium"},
                {"q": "ACID stands for:", "a": "Atomicity, Consistency, Isolation, Durability", "b": "Asynchronous, Concurrent, Indexed, Distributed", "c": "Abstract, Consistent, Isolated, Defined", "d": "None", "ans": "A", "diff": "easy"},
                {"q": "A foreign key references:", "a": "Primary key in same table", "b": "Primary key in another table", "c": "Any column", "d": "Index column", "ans": "B", "diff": "easy"},
            ],
            "Operating Systems": [
                {"q": "Which scheduling algorithm can cause starvation?", "a": "FCFS", "b": "Round Robin", "c": "Priority", "d": "SRTF", "ans": "C", "diff": "medium"},
                {"q": "Deadlock cannot occur if which condition is prevented?", "a": "Mutual Exclusion", "b": "Hold and Wait", "c": "No Preemption", "d": "Circular Wait", "ans": "D", "diff": "medium"},
                {"q": "Virtual memory is implemented using:", "a": "Cache", "b": "Registers", "c": "Paging/Segmentation", "d": "ROM", "ans": "C", "diff": "easy"},
            ],
            "Aptitude": [
                {"q": "A train 150m long passes a pole in 15 seconds. Speed in km/h?", "a": "36", "b": "40", "c": "45", "d": "54", "ans": "A", "diff": "medium", "exp": "Speed = 150/15 = 10 m/s = 36 km/h"},
                {"q": "If 6 men can do a work in 8 days, 4 men can do it in:", "a": "10", "b": "12", "c": "14", "d": "16", "ans": "B", "diff": "easy"},
                {"q": "What is 15% of 500?", "a": "65", "b": "70", "c": "75", "d": "80", "ans": "C", "diff": "easy"},
            ],
        }
        return questions.get(subject_name, [
            {"q": f"Sample question for {subject_name}?", "a": "A", "b": "B", "c": "C", "d": "D", "ans": "A", "diff": "easy"}
        ])

    def _create_notifications(self):
        try:
            from notifications.models import Notification
            students = User.objects.filter(role="student")
            msgs = [
                ("New Mock Test Available", "A new DSA mock test has been published. Attempt it now!", "info"),
                ("Profile Incomplete", "Complete your profile to get better AI recommendations.", "warning"),
                ("Study Streak!", "You're on a 7-day study streak! Keep it up!", "success"),
                ("AI Study Plan Ready", "Your personalized study plan has been generated by AI.", "info"),
            ]
            count = 0
            for student in students:
                for title, body, ntype in msgs:
                    Notification.objects.get_or_create(
                        user=student, title=title,
                        defaults={"message": body, "notification_type": ntype, "is_read": False}
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count} notifications created"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ! Notifications: {e}"))

        self._create_curriculum_and_materials()

    def _create_curriculum_and_materials(self):
        try:
            from quiz.models import Subject
            from core.models import CurriculumUnit, CurriculumTopic, StudyMaterial, log_activity

            subj_dsa, _ = Subject.objects.get_or_create(name="Data Structures", defaults={"code": "DSA", "category": "core"})
            subj_dbms, _ = Subject.objects.get_or_create(name="DBMS", defaults={"code": "DBMS", "category": "database"})

            # Units
            u1, _ = CurriculumUnit.objects.get_or_create(subject=subj_dsa, unit_number=1, defaults={"title": "Linear Data Structures & Analysis"})
            u2, _ = CurriculumUnit.objects.get_or_create(subject=subj_dsa, unit_number=2, defaults={"title": "Trees, Graphs & Advanced DSA"})
            u3, _ = CurriculumUnit.objects.get_or_create(subject=subj_dbms, unit_number=3, defaults={"title": "Relational Database Design & Normalization"})

            # Topics
            t1, _ = CurriculumTopic.objects.get_or_create(unit=u1, title="Arrays, Stacks and Queues", defaults={"summary": "Basic operations, LIFO/FIFO principles, applications.", "target_year": 1})
            t2, _ = CurriculumTopic.objects.get_or_create(unit=u2, title="Binary Search Trees and Heap", defaults={"summary": "Tree traversals, BST insertion/deletion, Heap sort.", "target_year": 2})
            t3, _ = CurriculumTopic.objects.get_or_create(unit=u3, title="1NF, 2NF, 3NF and BCNF Normalization", defaults={"summary": "Eliminating anomalies, functional dependencies, 3NF vs BCNF.", "target_year": 3})

            # Materials
            admin_user = User.objects.filter(is_superuser=True).first()
            m1, _ = StudyMaterial.objects.get_or_create(
                title="Comprehensive DBMS Normalization Notes (3NF & BCNF)",
                defaults={
                    "unit": u3, "topic": t3, "material_type": "notes",
                    "description": "Curated lecture notes explaining functional dependency and normalization algorithms.",
                    "extracted_text": "Functional Dependency: X -> Y means X uniquely determines Y. 1NF removes repeating groups. 2NF removes partial dependency on composite key. 3NF removes transitive dependency. BCNF ensures every determinant is a candidate key.",
                    "is_demo": True, "uploaded_by": admin_user
                }
            )

            # Log seeding activity
            log_activity(admin_user, "Database Seed Completed", module="System", details="Curriculum & Multi-Persona Students Populated")
            self.stdout.write(self.style.SUCCESS("  [OK] Curriculum units, topics, materials & audit log seeded"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ! Curriculum seeding: {e}"))
