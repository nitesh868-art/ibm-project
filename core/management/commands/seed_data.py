"""
Management command to populate the database with sample data.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from companies.models import Company
from quiz.models import Subject, Question, MockTest
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('[*] Seeding database...\n')

        # 1. Create Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@placementpro.com',
                password='admin@123',
                first_name='Admin',
                last_name='User',
                role='admin',
                is_email_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(' Superuser created: admin / admin@123'))

        # 2. Create Demo Student
        if not User.objects.filter(username='student1').exists():
            student = User.objects.create_user(
                username='student1',
                email='student@placementpro.com',
                password='student@123',
                first_name='Rahul',
                last_name='Sharma',
                role='student',
                is_email_verified=True,
            )
            from accounts.models import StudentProfile
            StudentProfile.objects.get_or_create(
                user=student,
                defaults={
                    'roll_number': 'CS21001',
                    'branch': 'CSE',
                    'year': 3,
                    'semester': 6,
                    'cgpa': 8.5,
                    'skills': 'Python, Django, React, SQL, DSA',
                    'placement_status': 'not_placed',
                    'profile_completion': 75,
                    'study_streak': 7,
                    'total_points': 250,
                }
            )
            self.stdout.write(self.style.SUCCESS(' Demo student: student1 / student@123'))

        # 3. Create Demo Faculty
        if not User.objects.filter(username='faculty1').exists():
            faculty = User.objects.create_user(
                username='faculty1',
                email='faculty@placementpro.com',
                password='faculty@123',
                first_name='Dr. Priya',
                last_name='Mehta',
                role='faculty',
                is_email_verified=True,
            )
            from accounts.models import FacultyProfile
            FacultyProfile.objects.get_or_create(
                user=faculty,
                defaults={
                    'employee_id': 'FAC001',
                    'department': 'Computer Science',
                    'designation': 'Assistant Professor',
                    'specialization': 'Data Structures, Algorithms',
                }
            )
            self.stdout.write(self.style.SUCCESS(' Demo faculty: faculty1 / faculty@123'))

        # 4. Create Companies
        companies_data = [
            {'name': 'Google', 'company_type': 'product', 'min_package': 25, 'max_package': 45, 'min_cgpa': 7.5, 'eligible_branches': 'CSE,IT,ECE'},
            {'name': 'Microsoft', 'company_type': 'product', 'min_package': 20, 'max_package': 40, 'min_cgpa': 7.0, 'eligible_branches': 'CSE,IT,ECE,EEE'},
            {'name': 'Amazon', 'company_type': 'product', 'min_package': 18, 'max_package': 35, 'min_cgpa': 7.0, 'eligible_branches': 'CSE,IT,ECE'},
            {'name': 'TCS', 'company_type': 'service', 'min_package': 3.5, 'max_package': 7, 'min_cgpa': 6.0, 'eligible_branches': 'CSE,IT,ECE,ME,CE,EEE'},
            {'name': 'Infosys', 'company_type': 'service', 'min_package': 3.6, 'max_package': 8, 'min_cgpa': 6.0, 'eligible_branches': 'CSE,IT,ECE,ME,CE'},
            {'name': 'Wipro', 'company_type': 'service', 'min_package': 3.5, 'max_package': 7.5, 'min_cgpa': 6.0, 'eligible_branches': 'CSE,IT,ECE,ME'},
            {'name': 'Accenture', 'company_type': 'consulting', 'min_package': 4.5, 'max_package': 9, 'min_cgpa': 6.5, 'eligible_branches': 'CSE,IT,ECE,ME'},
            {'name': 'Flipkart', 'company_type': 'product', 'min_package': 15, 'max_package': 30, 'min_cgpa': 7.5, 'eligible_branches': 'CSE,IT'},
            {'name': 'Cognizant', 'company_type': 'service', 'min_package': 4, 'max_package': 8, 'min_cgpa': 6.0, 'eligible_branches': 'CSE,IT,ECE'},
            {'name': 'Deloitte', 'company_type': 'consulting', 'min_package': 6, 'max_package': 12, 'min_cgpa': 6.5, 'eligible_branches': 'CSE,IT,ECE,ME'},
            {'name': 'Razorpay', 'company_type': 'startup', 'min_package': 10, 'max_package': 25, 'min_cgpa': 7.0, 'eligible_branches': 'CSE,IT'},
            {'name': 'Zomato', 'company_type': 'startup', 'min_package': 8, 'max_package': 20, 'min_cgpa': 6.5, 'eligible_branches': 'CSE,IT'},
        ]
        for comp in companies_data:
            Company.objects.get_or_create(name=comp['name'], defaults=comp)
        self.stdout.write(self.style.SUCCESS(f' {len(companies_data)} companies seeded'))

        # 5. Create Subjects
        subjects_data = [
            ('Data Structures & Algorithms', 'DSA', 'core'),
            ('Database Management Systems', 'DBMS', 'database'),
            ('Operating Systems', 'OS', 'os'),
            ('Computer Networks', 'CN', 'networking'),
            ('Python Programming', 'PY', 'programming'),
            ('Java Programming', 'JAVA', 'programming'),
            ('Aptitude & Reasoning', 'APT', 'aptitude'),
            ('Verbal Ability', 'VER', 'verbal'),
            ('Logical Reasoning', 'LR', 'reasoning'),
            ('Object Oriented Programming', 'OOP', 'core'),
        ]
        subject_objs = {}
        for name, code, category in subjects_data:
            s, _ = Subject.objects.get_or_create(name=name, defaults={'code': code, 'category': category})
            subject_objs[code] = s
        self.stdout.write(self.style.SUCCESS(f' {len(subjects_data)} subjects seeded'))

        # 6. Create Sample Questions
        dsa_subj = subject_objs.get('DSA')
        apt_subj = subject_objs.get('APT')
        py_subj = subject_objs.get('PY')

        questions_to_create = []
        if dsa_subj:
            dsa_questions = [
                ('What is the time complexity of binary search?', 'O(n)', 'O(log n)', 'O(n)', 'O(1)', 'B', 'Binary search divides the search space in half each time, giving O(log n) complexity.', 'easy'),
                ('Which data structure uses FIFO principle?', 'Stack', 'Tree', 'Queue', 'Graph', 'C', 'Queue follows First In First Out (FIFO) principle.', 'easy'),
                ('What is the worst case time complexity of QuickSort?', 'O(n log n)', 'O(n)', 'O(n)', 'O(log n)', 'C', 'QuickSort has O(n) worst case when pivot is always min or max element.', 'medium'),
                ('Which traversal visits root first?', 'Inorder', 'Postorder', 'Preorder', 'Level order', 'C', 'Preorder = Root  Left  Right', 'easy'),
                ('What is the space complexity of merge sort?', 'O(1)', 'O(log n)', 'O(n)', 'O(n log n)', 'C', 'Merge sort requires O(n) extra space for the auxiliary array.', 'medium'),
            ]
            for q in dsa_questions:
                if not Question.objects.filter(question_text=q[0]).exists():
                    questions_to_create.append(Question(
                        subject=dsa_subj, question_text=q[0],
                        option_a=q[1], option_b=q[2], option_c=q[3], option_d=q[4],
                        correct_answer=q[5], explanation=q[6], difficulty=q[7],
                        language='general', is_active=True
                    ))

        if apt_subj:
            apt_questions = [
                ('If 2x + 3 = 11, find x.', '3', '4', '5', '6', 'B', '2x = 8, so x = 4', 'easy'),
                ('A train covers 360 km in 4 hours. What is its speed?', '80 km/h', '90 km/h', '100 km/h', '72 km/h', 'B', 'Speed = Distance/Time = 360/4 = 90 km/h', 'easy'),
                ('Find the odd one out: 2, 3, 5, 7, 9, 11', '9', '3', '5', '7', 'A', '9 is not a prime number. All others are prime.', 'medium'),
                ('If APPLE = 50, then MANGO = ?', '47', '56', '65', '52', 'A', 'A=1,P=16,P=16,L=12,E=5  50. M=13,A=1,N=14,G=7,O=15  50. Actually 47', 'medium'),
            ]
            for q in apt_questions:
                if not Question.objects.filter(question_text=q[0]).exists():
                    questions_to_create.append(Question(
                        subject=apt_subj, question_text=q[0],
                        option_a=q[1], option_b=q[2], option_c=q[3], option_d=q[4],
                        correct_answer=q[5], explanation=q[6], difficulty=q[7],
                        language='general', is_active=True
                    ))

        if py_subj:
            py_questions = [
                ('What does len([1,2,3]) return in Python?', '0', '1', '2', '3', 'D', 'len() returns the number of elements in the list.', 'easy'),
                ('Which keyword is used for anonymous functions in Python?', 'def', 'func', 'lambda', 'anon', 'C', 'lambda keyword creates anonymous (unnamed) functions in Python.', 'easy'),
                ('What is the output of: print(type([]))?', '<class list>', '<class dict>', '<class tuple>', '<class array>', 'A', 'An empty [] is a list object in Python.', 'easy'),
                ('What is list comprehension in Python?', 'A method to compress lists', 'A concise way to create lists', 'A way to delete lists', 'None', 'B', 'List comprehension provides a concise way to create lists: [expr for item in iterable]', 'medium'),
            ]
            for q in py_questions:
                if not Question.objects.filter(question_text=q[0]).exists():
                    questions_to_create.append(Question(
                        subject=py_subj, question_text=q[0],
                        option_a=q[1], option_b=q[2], option_c=q[3], option_d=q[4],
                        correct_answer=q[5], explanation=q[6], difficulty=q[7],
                        language='python', is_active=True
                    ))

        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f' Sample questions seeded'))

        # 7. Create a sample Mock Test
        if dsa_subj and not MockTest.objects.filter(title='DSA Basics Mock Test').exists():
            test = MockTest.objects.create(
                title='DSA Basics Mock Test',
                description='Test your knowledge of Data Structures and Algorithms',
                subject=dsa_subj,
                test_type='mock',
                duration_minutes=30,
                total_marks=50,
                passing_marks=20,
                is_active=True,
                is_published=True,
            )
            test.questions.set(Question.objects.filter(subject=dsa_subj))
            self.stdout.write(self.style.SUCCESS(' Mock test created'))

        # 8. Create welcome notifications for demo student
        student_user = User.objects.filter(username='student1').first()
        if student_user:
            Notification.objects.get_or_create(
                user=student_user,
                title=' Welcome to PlacementPro!',
                defaults={
                    'message': 'Start your placement journey! Complete your profile and take your first mock test.',
                    'notification_type': 'success',
                }
            )
            Notification.objects.get_or_create(
                user=student_user,
                title=' Generate Your AI Study Plan',
                defaults={
                    'message': 'Use our AI-powered study planner to create a personalized schedule for your exams.',
                    'notification_type': 'info',
                    'link': '/study-planner/plans/generate/',
                }
            )

        self.stdout.write('\n' + self.style.SUCCESS(' Database seeded successfully!'))
        self.stdout.write('\n Demo Credentials:')
        self.stdout.write('  Admin:   admin / admin@123')
        self.stdout.write('  Student: student1 / student@123')
        self.stdout.write('  Faculty: faculty1 / faculty@123')
        self.stdout.write('\n Run: python manage.py runserver')

