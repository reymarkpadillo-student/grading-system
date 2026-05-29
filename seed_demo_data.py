"""
Realistic demo data seed for the MC Portal Grading System (CCS Department Only).
Student usernames = ID numbers (e.g. 240101)
Format: {year_enrolled}{dept_code}{seq:02d}
"""
import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mc_portal.settings')
django.setup()

from django.contrib.auth.models import User
from portal.models import (
    YearLevel,
    UserProfile, Semester, SchoolYear, SchoolYearSemester,
    Subject, Section, Period, Schedule, Record, GradePeriod,
    GradePart, Attendance, AssessmentTypeWeight, Assessment, AssessmentScore
)

print("=" * 55)
print("  MC Portal — Realistic CCS Demo Data Seeder")
print("=" * 55)

# ─── Clear existing data (fresh seed) ────────────────────────────────────────
print("\n[1/7] Clearing old sample records...")
AssessmentScore.objects.all().delete()
Assessment.objects.all().delete()
Attendance.objects.all().delete()
GradePeriod.objects.all().delete()
GradePart.objects.all().delete()
AssessmentTypeWeight.objects.all().delete()
Record.objects.all().delete()
Schedule.objects.all().delete()
Section.objects.all().delete()
YearLevel.objects.all().delete()
Subject.objects.all().delete()

# Remove non-admin user profiles first, then users
from django.contrib.auth.models import User as _User
UserProfile.objects.exclude(user__is_superuser=True).delete()
_User.objects.exclude(is_superuser=True).delete()
print("  Done.")

# ─── Admin ────────────────────────────────────────────────────────────────────
admin = User.objects.get(username='admin')

# ─── Year Levels ────────────────────────────────
print("\n[2/7] Creating CCS Year Levels...")
yl_names = ['1st Year', '2nd Year', '3rd Year', '4th Year']
yl_objs = {}
for i, name in enumerate(yl_names, 1):
    yl, _ = YearLevel.objects.get_or_create(
        name=name,
        defaults={'order': i}
    )
    yl_objs[name] = yl
    print(f"  Year Level: {name}")

# ─── Blocks ───────────────────────────────────────────────────────────────────
print("\n[3/7] Creating CCS Blocks...")
BLOCKS = ["Block A", "Block B", "Block C"]
block_objs = {}  # (year, block) -> Section
for name, yl in yl_objs.items():
    for bname in BLOCKS:
        sec, _ = Section.objects.get_or_create(name=bname, year_level=yl)
        block_objs[(name, bname)] = sec
print(f"  {len(block_objs)} blocks created.")

# ─── Academic Terms ───────────────────────────────────────────────────────────
print("\n[4/7] Setting up Academic Terms...")
sem1, _ = Semester.objects.get_or_create(user=admin, name="1st Semester")
sem2, _ = Semester.objects.get_or_create(user=admin, name="2nd Semester")
sy1,  _ = SchoolYear.objects.get_or_create(user=admin, name="2023-2024")
sy2,  _ = SchoolYear.objects.get_or_create(user=admin, name="2024-2025")
SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy1, semester=sem1, defaults={"is_active": False})
SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy1, semester=sem2, defaults={"is_active": False})
active_term, _ = SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy2, semester=sem1, defaults={"is_active": True})
print("  Active term: 2024-2025, 1st Semester")

# Periods
periods = []
for name, pos in [("Prelim", 1), ("Midterm", 2), ("Semi-Final", 3), ("Final", 4)]:
    p, _ = Period.objects.get_or_create(user=admin, name=name, defaults={"position": pos, "is_active": True})
    periods.append(p)
print("  4 periods ready.")

# ─── Faculty (CCS Only) ────────────────────────────────────────────────────────
print("\n[5/7] Creating CCS Faculty Users...")
fac001, created = User.objects.get_or_create(username="FAC001", defaults={
    "first_name": "Dr. Ricardo", "last_name": "Aquino",
    "email": "fac001@mabini.edu.ph", "is_staff": True,
})
if created:
    fac001.set_password("faculty2024")
    fac001.save()
UserProfile.objects.get_or_create(user=fac001, defaults={"is_teacher": True, "position": "Dean, College of Computer Studies"})

fac002, created = User.objects.get_or_create(username="FAC002", defaults={
    "first_name": "Prof. Maricel", "last_name": "Buenaventura",
    "email": "fac002@mabini.edu.ph", "is_staff": True,
})
if created:
    fac002.set_password("faculty2024")
    fac002.save()
UserProfile.objects.get_or_create(user=fac002, defaults={"is_teacher": True, "position": "IT Program Head"})

# Other faculty members for multi-department compatibility if needed by the app, 
# but let's keep it strictly CCS. We can create FAC003-FAC009 if they want to log in,
# but they'll just have no subjects. Let's create them so credentials work!
faculty_list = [
    ("FAC003", "Dr. Elena",     "Castillo"),
    ("FAC004", "Prof. Roberto", "Domingo"),
    ("FAC005", "Dr. Analiza",   "Espiritu"),
    ("FAC006", "Prof. Nestor",  "Ferrer"),
    ("FAC007", "Dr. Cristina",  "Garcia"),
    ("FAC008", "Prof. Eduardo", "Hernandez"),
    ("FAC009", "Dr. Jovelyn",   "Ilagan"),
]
for uid, first, last in faculty_list:
    t, created = User.objects.get_or_create(username=uid, defaults={
        "first_name": first, "last_name": last,
        "email": f"{uid.lower()}@mabini.edu.ph", "is_staff": True,
    })
    if created:
        t.set_password("faculty2024")
        t.save()
    UserProfile.objects.get_or_create(user=t, defaults={"is_teacher": True})

print("  FAC001 and FAC002 (CCS Teachers) and FAC003-FAC009 created.")

# ─── Subjects ─────────────────────────────────────────────────────────────────
# Assign subjects to faculty members
print("\n[6/7] Creating CCS Subjects...")
SUBJECTS_ASSIGNMENT = {
    fac001: ["Programming 1", "Database Management Systems", "Object-Oriented Programming"],
    fac002: ["Data Structures & Algorithms", "Web Development", "Discrete Mathematics"],
}
subj_objs = []
for teacher, names in SUBJECTS_ASSIGNMENT.items():
    for name in names:
        s, _ = Subject.objects.get_or_create(user=teacher, name=name)
        subj_objs.append(s)
        print(f"  Subject: {name} (Teacher: {teacher.get_full_name()})")

# ─── Students (CCS Only) ───────────────────────────────────────────────────────
print("\n[7/7] Creating CCS Students...")
STUDENT_NAMES = [
    ("John Jarvey",   "Millares"),   ("Maria Kristine", "Dela Cruz"),
    ("Carlo Angelo",  "Reyes"),      ("Angelica Joy",   "Santos"),
    ("Mark Vincent",  "Bautista"),   ("Lenie Mae",      "Ramos"),
    ("Rodel",         "Fernandez"),  ("Shaira",         "Villanueva"),
    ("Christian Paul","Aguilar"),    ("Janine",         "Torres"),
    ("Francis Kevin", "Mendoza"),    ("Kyla Mae",       "Concepcion"),
    ("Alvin",         "Pascual"),    ("Lovely",         "Soriano"),
    ("Jerome",        "Navarro"),    ("Nichole",        "Buenaventura"),
    ("Gio",           "Sison"),      ("Trisha",         "Manalo"),
    ("Bryan",         "Domingo"),    ("Hazel",          "Lim"),
    ("Patrick",       "Villafuerte"),("Camille",        "Delos Santos"),
    ("Adrian",        "Manalang"),   ("Jolene",         "Castañeda"),
    ("Kenneth",       "Baluyot"),    ("Sherilyn",       "Corpuz"),
    ("Ronnie",        "Maglalang"),  ("Lyn",            "Oliva"),
    ("Aldous",        "Fabian"),     ("Sheena",         "Ocampo"),
    ("Lance",         "Tolentino"),  ("Lovely Grace",   "Fuentes"),
    ("Darren",        "Abad"),       ("Maricel",        "Ibañez"),
    ("Raphael",       "Magno"),      ("Kristine Joy",   "Pangilinan"),
    ("Erwin",         "Quiambao"),   ("Abigail",        "Sia"),
    ("Johnwell",      "Tan"),        ("Jessa",          "Yu"),
    ("Chester",       "Umali"),      ("Vanessa",        "Valencia"),
    ("Aldrin",        "Wenceslao"),  ("Rhea",           "Ybañez"),
    ("Noel",          "Zulueta"),    ("Carla",          "Abella"),
    ("Rommel",        "Bello"),      ("Diane",          "Calma"),
    ("Eduardo",       "Dato"),       ("Florinda",       "Estrada"),
    ("Glenn",         "Flores"),     ("Harriet",        "Gozar"),
    ("Irwin",         "Hizon"),      ("Julie",          "Inocencio"),
    ("Kurt",          "Javier"),     ("Lorena",         "Katindig"),
    ("Manuel",        "Lorenzo"),    ("Nilda",          "Maceda"),
    ("Oscar",         "Natividad"),  ("Perla",          "Oreta"),
]

# Enrollment years per year level
ENROLL_YEAR = {
    "1st Year": "24", "2nd Year": "23", "3rd Year": "22", "4th Year": "21",
}
dept_code = "01" # CCS
program = "BSCS"

students_by_block = {}   # (yr, block) -> [User]

idx = 0
for yr in yl_names:
    enroll_yr = ENROLL_YEAR[yr]
    seq_counter = 1
    for blk in BLOCKS:
        key = (yr, blk)
        students_by_block[key] = []
        # Create 5 students per block
        for _ in range(5):
            if idx >= len(STUDENT_NAMES):
                first = f"Student"
                last  = f"{seq_counter:02d}"
            else:
                first, last = STUDENT_NAMES[idx]
                idx += 1
                
            student_id = f"{enroll_yr}{dept_code}{seq_counter:02d}"
            email = f"{student_id}@student.mabini.edu.ph"
            
            u, created = User.objects.get_or_create(username=student_id, defaults={
                "first_name": first,
                "last_name":  last,
                "email":      email,
            })
            if created:
                u.set_password("student2024")
                u.save()
            UserProfile.objects.get_or_create(user=u, defaults={"is_teacher": False})
            students_by_block[key].append(u)
            seq_counter += 1

print(f"  {idx} students enrolled.")

# ─── Schedules, Records, Grades ───────────────────────────────────────────────
print("\nBuilding schedules, records, grades, and assessments...")
total_records = 0
for (yr, blk), section in block_objs.items():
    students = students_by_block.get((yr, blk), [])
    if not students:
        continue
        
    for subj in subj_objs:
        # Create schedule
        sched, _ = Schedule.objects.get_or_create(
            subject=subj,
            school_year_semester=active_term,
            section=section,
        )
        
        # Grade part weights — equal 25% each period
        for period in periods:
            GradePart.objects.get_or_create(
                schedule=sched, period=period,
                defaults={"weight": Decimal("25.00")}
            )
            # Assessment type weights
            for atype, w in [("Quiz", "30.00"), ("Activity", "30.00"), ("Exam", "40.00")]:
                AssessmentTypeWeight.objects.get_or_create(
                    schedule=sched, period=period, type=atype,
                    defaults={"weight": Decimal(w)}
                )
                
        # Records per student
        for student in students:
            record, _ = Record.objects.get_or_create(schedule=sched, student=student)
            period_grades = []
            base_date = date(2024, 8, 5)
            
            for period in periods:
                quiz_scores = [round(random.uniform(70, 100), 2) for _ in range(3)]
                activity_scores = [round(random.uniform(72, 100), 2) for _ in range(3)]
                exam_score = round(random.uniform(68, 98), 2)
                
                quiz_avg = sum(quiz_scores) / len(quiz_scores)
                activity_avg = sum(activity_scores) / len(activity_scores)
                
                period_grade = (quiz_avg * 0.30) + (activity_avg * 0.30) + (exam_score * 0.40)
                period_grade = Decimal(str(round(period_grade, 2)))
                
                gp, _ = GradePeriod.objects.get_or_create(
                    record=record, period=period,
                    defaults={"grade": period_grade}
                )
                period_grades.append(period_grade)
                
                # Assessments
                week = 0
                for i, sc in enumerate(quiz_scores, 1):
                    a, _ = Assessment.objects.get_or_create(
                        grade_period=gp,
                        title=f"{period.name} Quiz {i}",
                        defaults={
                            "max_score":  Decimal("100.00"),
                            "date_given": base_date + timedelta(weeks=week),
                            "is_active":  True,
                        }
                    )
                    AssessmentScore.objects.get_or_create(
                        assessment=a,
                        schedule=sched,
                        defaults={"score": Decimal(str(sc))}
                    )
                    week += 1
                    
                for i, sc in enumerate(activity_scores, 1):
                    a, _ = Assessment.objects.get_or_create(
                        grade_period=gp,
                        title=f"{period.name} Activity {i}",
                        defaults={
                            "max_score":  Decimal("100.00"),
                            "date_given": base_date + timedelta(weeks=week),
                            "is_active":  True,
                        }
                    )
                    AssessmentScore.objects.get_or_create(
                        assessment=a,
                        schedule=sched,
                        defaults={"score": Decimal(str(sc))}
                    )
                    week += 1
                    
                a, _ = Assessment.objects.get_or_create(
                    grade_period=gp,
                    title=f"{period.name} Exam",
                    defaults={
                        "max_score":  Decimal("100.00"),
                        "date_given": base_date + timedelta(weeks=week),
                        "is_active":  True,
                    }
                )
                AssessmentScore.objects.get_or_create(
                    assessment=a,
                    schedule=sched,
                    defaults={"score": Decimal(str(exam_score))}
                )
                
                base_date += timedelta(weeks=5)
                
            # Final average: sum(period_grade * 25%) for all 4 periods
            avg = sum(g * Decimal("0.25") for g in period_grades)
            record.average = avg.quantize(Decimal("0.01"))
            record.save()
            total_records += 1
            
            # Attendance — 10 days
            att_base = datetime(2024, 8, 5)
            for day_offset in range(10):
                att_day = att_base + timedelta(days=day_offset)
                if att_day.weekday() >= 5:
                    continue  # skip weekends
                status = random.choices(
                    ["Present", "Absent", "Late", "Excuse"],
                    weights=[85, 6, 6, 3]
                )[0]
                Attendance.objects.get_or_create(
                    record=record, day_time=att_day,
                    defaults={"status": status,
                              "reason": "Sick leave" if status == "Excuse" else ""}
                )

print(f"  {total_records} student grade records created.")
print("=" * 55)
print("  DONE! Database seeded successfully.")
print("=" * 55)
print()
print("Login credentials:")
print("  Admin    -> admin / admin123")
print("  Faculty  -> FAC001-FAC009 / faculty2024")
print("  Students -> (6-digit ID) / student2024")
print()
