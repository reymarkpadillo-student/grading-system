"""
Realistic demo data seed for the MC Portal Grading System.
Student usernames = ID numbers (e.g. 222701)
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
    Department, YearLevel,
    UserProfile, Semester, SchoolYear, SchoolYearSemester,
    Subject, Section, Period, Schedule, Record, GradePeriod,
    GradePart, Attendance, AssessmentTypeWeight, Assessment, AssessmentScore
)

print("=" * 55)
print("  MC Portal — Realistic Demo Data Seeder")
print("=" * 55)

# ─── Clear existing data (fresh seed) ────────────────────────────────────────
print("\n[1/8] Clearing old sample records...")
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
Department.objects.all().delete()
Subject.objects.all().delete()
# Remove non-admin user profiles first, then users
from django.contrib.auth.models import User as _User
UserProfile.objects.exclude(user__is_superuser=True).delete()
_User.objects.exclude(is_superuser=True).delete()
print("  Done.")


# ─── Admin ────────────────────────────────────────────────────────────────────
admin = User.objects.get(username='admin')

# ─── Departments ─────────────────────────────────────────────────────────────
print("\n[2/8] Creating departments...")
DEPTS = [
    ("College of Computer Studies",                    "CCS",  "01"),
    ("College of Education",                           "CED",  "02"),
    ("College of Business Administration and Accountancy", "CBAA", "03"),
    ("College of Nursing",                             "CN",   "04"),
    ("College of Criminal Justice Education",          "CCJE", "05"),
    ("College of Liberal Arts",                        "CLA",  "06"),
    ("Technical Education and Training Department",    "TETD", "07"),
    ("Graduate School",                                "GS",   "08"),
    ("High School Department",                         "HSD",  "09"),
]
dept_objs = {}
for name, short, code in DEPTS:
    d, _ = Department.objects.get_or_create(name=name, defaults={"short_name": short})
    dept_objs[short] = (d, code)
    print(f"  {short}: {name}")

# ─── Year Levels (custom per department type) ────────────────────────────────
print("\n[3/8] Creating year levels...")

# Define year level names per department short name
YEAR_LEVELS_MAP = {
    'CCS':  ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'CED':  ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'CBAA': ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'CN':   ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'CCJE': ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'CLA':  ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'TETD': ['1st Year', '2nd Year', '3rd Year', '4th Year'],
    'GS':   ['1st Year', '2nd Year'],                          # Graduate School: 2 years
    'HSD':  ['Grade 7', 'Grade 8', 'Grade 9',                 # High School: Grade 7-12
              'Grade 10', 'Grade 11', 'Grade 12'],
}

yl_objs = {}   # (dept_short, yr_name) -> YearLevel
for short, (dept, code) in dept_objs.items():
    yr_names = YEAR_LEVELS_MAP.get(short, ['1st Year', '2nd Year', '3rd Year', '4th Year'])
    for i, yr in enumerate(yr_names, 1):
        yl, _ = YearLevel.objects.get_or_create(
            department=dept, name=yr,
            defaults={'order': i}
        )
        yl_objs[(short, yr)] = yl
        print(f"  [{short}] {yr}")
print(f"  {len(yl_objs)} year levels total.")


# ─── Blocks ───────────────────────────────────────────────────────────────────
print("\n[4/8] Creating blocks...")
BLOCKS = ["Block A", "Block B", "Block C"]
block_objs = {}  # (short, year, block) -> Section
for (short, yr), yl in yl_objs.items():
    # CCS and CBAA get 3 blocks, others 2
    n_blocks = 3 if short in ("CCS", "CBAA") else 2
    for bname in BLOCKS[:n_blocks]:
        sec, _ = Section.objects.get_or_create(name=bname, year_level=yl)
        block_objs[(short, yr, bname)] = sec
print(f"  {len(block_objs)} blocks created.")

# ─── Academic Terms ───────────────────────────────────────────────────────────
print("\n[5/8] Setting up academic terms...")
sem1, _ = Semester.objects.get_or_create(user=admin, name="1st Semester")
sem2, _ = Semester.objects.get_or_create(user=admin, name="2nd Semester")
sy1,  _ = SchoolYear.objects.get_or_create(user=admin, name="2023-2024")
sy2,  _ = SchoolYear.objects.get_or_create(user=admin, name="2024-2025")
SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy1, semester=sem1, defaults={"is_active": False})
SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy1, semester=sem2, defaults={"is_active": False})
active_term, _ = SchoolYearSemester.objects.get_or_create(user=admin, school_year=sy2, semester=sem1, defaults={"is_active": True})
print("  Active term: 2024-2025, 1st Semester")

# ─── Subjects ─────────────────────────────────────────────────────────────────
print("\n[6/8] Creating subjects & periods...")
SUBJECTS = {
    "CCS":  ["Programming 1", "Data Structures & Algorithms", "Database Management Systems",
              "Web Development", "Object-Oriented Programming", "Discrete Mathematics"],
    "CED":  ["Child & Adolescent Development", "Curriculum Design & Development",
              "Educational Psychology", "Teaching Strategies", "Assessment in Learning"],
    "CBAA": ["Fundamentals of Accounting", "Business Law & Regulation",
              "Financial Management", "Business Ethics", "Principles of Marketing",
              "Managerial Economics"],
    "CN":   ["Anatomy & Physiology", "Nursing Fundamentals", "Pharmacology",
              "Community Health Nursing", "Medical-Surgical Nursing"],
    "CCJE": ["Criminal Law 1", "Criminology", "Forensic Science",
              "Police Administration", "Criminal Procedure"],
    "CLA":  ["Philippine Literature", "Introduction to Philosophy",
              "Political Science 1", "Sociology", "Creative Writing"],
    "TETD": ["Technical Drawing", "Automotive Technology", "Electrical Installation",
              "Welding Technology"],
    "GS":   ["Research Methods", "Advanced Statistics", "Thesis Writing 1"],
    "HSD":  ["English", "Mathematics", "Science", "Filipino",
              "Araling Panlipunan", "MAPEH", "TLE"],
}
subj_objs = {}
for short, names in SUBJECTS.items():
    subj_objs[short] = []
    for name in names:
        s, _ = Subject.objects.get_or_create(user=admin, name=name)
        subj_objs[short].append(s)

# Periods
periods = []
for name, pos in [("Prelim", 1), ("Midterm", 2), ("Semi-Final", 3), ("Final", 4)]:
    p, _ = Period.objects.get_or_create(user=admin, name=name, defaults={"position": pos, "is_active": True})
    periods.append(p)
print(f"  Subjects and 4 periods ready.")

# ─── Teachers ─────────────────────────────────────────────────────────────────
FACULTY = [
    ("FAC001", "Dr. Ricardo",  "Aquino",     "CCS"),
    ("FAC002", "Prof. Maricel","Buenaventura","CCS"),
    ("FAC003", "Dr. Elena",    "Castillo",   "CED"),
    ("FAC004", "Prof. Roberto","Domingo",    "CBAA"),
    ("FAC005", "Dr. Analiza",  "Espiritu",   "CN"),
    ("FAC006", "Prof. Nestor", "Ferrer",     "CCJE"),
    ("FAC007", "Dr. Cristina", "Garcia",     "CLA"),
    ("FAC008", "Prof. Eduardo","Hernandez",  "TETD"),
    ("FAC009", "Dr. Jovelyn",  "Ilagan",     "GS"),
]
for uid, first, last, dept in FACULTY:
    t, created = User.objects.get_or_create(username=uid, defaults={
        "first_name": first, "last_name": last,
        "email": f"{uid.lower()}@mabini.edu.ph", "is_staff": True,
    })
    if created:
        t.set_password("faculty2024")
        t.save()
    UserProfile.objects.get_or_create(user=t, defaults={"is_teacher": True})

# ─── Students ─────────────────────────────────────────────────────────────────
print("\n[7/8] Creating students...")

# Format: {yr_enrolled}{dept_code}{seq:02d}
# e.g. CCS 2022 enrolled, dept code 01 → 220101, 220102 ...
STUDENT_NAMES = {
    # CCS — 3 blocks × 4 years × 5 = 60 needed
    "CCS": [
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
    ],
    # CBAA — 3 blocks × 4 years × 5 = 60 needed
    "CBAA": [
        ("Jerico",        "Dizon"),      ("Charmaine",      "Lacson"),
        ("Aldrin",        "Perez"),      ("Ma. Theresa",    "Castillo"),
        ("Ryan Dale",     "Espino"),     ("Jennifer",       "Luna"),
        ("Raphael",       "Ocampo"),     ("Kristel",        "Aquino"),
        ("Emmanuel",      "Padilla"),    ("Sheila Mae",     "Tolentino"),
        ("Vincent",       "Macapagal"),  ("Lorna",          "Salazar"),
        ("Bernard",       "Alcantara"),  ("Roselyn",        "Blas"),
        ("Crisanto",      "Cabanero"),   ("Diana",          "Dacumos"),
        ("Edwin",         "Echevarria"), ("Fatima",         "Fontanilla"),
        ("Gilbert",       "Generoso"),   ("Herminia",       "Hermoso"),
        ("Isidro",        "Ilagan"),     ("Jasmin",         "Julian"),
        ("Kristopher",    "Kalaw"),      ("Leonora",        "Lacuesta"),
        ("Melvin",        "Macalintal"), ("Nancy",          "Nacpil"),
        ("Oliver",        "Oñate"),      ("Pamela",         "Panlasigui"),
        ("Quincy",        "Quimson"),    ("Rowena",         "Robredo"),
        ("Salvador",      "Songco"),     ("Thelma",         "Tablante"),
        ("Ulysses",       "Umali"),      ("Vivien",         "Valderama"),
        ("Willy",         "Waga"),       ("Ximena",         "Xu"),
        ("Yolanda",       "Yabut"),      ("Zenith",         "Zamora"),
        ("Armando",       "Araneta"),    ("Bella",          "Benitez"),
        ("Carlos",        "Candelaria"), ("Dalisay",        "Dimalanta"),
        ("Ernesto",       "Enriquez"),   ("Felicidad",      "Fajardo"),
        ("Gonzalo",       "Gamboa"),     ("Honorata",       "Hilario"),
        ("Ignacio",       "Imperial"),   ("Josefina",       "Jimenez"),
        ("Karlo",         "Katigbak"),   ("Luz",            "Ligsay"),
        ("Mario",         "Macario"),    ("Nenita",         "Nicolas"),
        ("Orlando",       "Oblena"),     ("Pilita",         "Ponce"),
        ("Ramon",         "Recto"),      ("Soledad",        "Salvacion"),
        ("Teodoro",       "Teotico"),    ("Ursula",         "Unabia"),
        ("Virgilio",      "Ventura"),    ("Wenifreda",      "Wenceslao"),
        ("Xander",        "Xerez"),      ("Yancy",          "Yarcia"),
    ],
    # CED — 2 blocks × 4 years × 4 = 32 needed
    "CED": [
        ("Rosario",       "Dela Pena"),  ("Jason",          "Evangelista"),
        ("Mary Ann",      "Flores"),     ("Eduardo Jr.",    "Galvez"),
        ("Cynthia",       "Herrera"),    ("Jonathan",       "Ibarra"),
        ("Glenda",        "Javier"),     ("Michael",        "Kapunan"),
        ("Analiza",       "Lagrimas"),   ("Benedict",       "Manding"),
        ("Clara",         "Naparate"),   ("Domingo",        "Oabel"),
        ("Elena",         "Paguio"),     ("Fernando",       "Quito"),
        ("Gloria",        "Ramos"),      ("Henry",          "Sagun"),
        ("Imelda",        "Tingzon"),    ("Jessie",         "Urbano"),
        ("Karen",         "Vergara"),    ("Lorenzo",        "Welgas"),
        ("Miriam",        "Ximenes"),    ("Nathaniel",      "Yap"),
        ("Ofelia",        "Zabala"),     ("Precioso",       "Abuan"),
        ("Quirino",       "Baluyut"),    ("Rebecca",        "Cabrera"),
        ("Sergio",        "Dagdagan"),   ("Teresita",       "Evangelio"),
        ("Urbano",        "Fabro"),      ("Violeta",        "Gallardo"),
        ("Wilson",        "Hamtig"),     ("Yvette",         "Ingco"),
    ],
    # CN — 2 blocks × 4 years × 4 = 32 needed
    "CN": [
        ("Patricia",      "Legaspi"),    ("Noel",           "Macabenta"),
        ("Rowena",        "Narciso"),    ("Dennis",         "Oliva"),
        ("Gina",          "Pimentel"),   ("Roger",          "Quiambao"),
        ("Aiza",          "Rebuelta"),   ("Ericson",        "Santiago"),
        ("Aileen",        "Tabuena"),    ("Bruno",          "Ubaldo"),
        ("Cecelia",       "Valenzuela"), ("Dindo",          "Wata"),
        ("Eva",           "Ximeno"),     ("Francisco",      "Yambao"),
        ("Grace",         "Zamudio"),    ("Hector",         "Ablaza"),
        ("Irene",         "Balagtas"),   ("Jorge",          "Cabuhat"),
        ("Kathleen",      "Dalisay"),    ("Loreto",         "Ebarle"),
        ("Maribel",       "Fuentes"),    ("Nelson",         "Guiab"),
        ("Ophelia",       "Habana"),     ("Pablo",          "Inojales"),
        ("Querida",       "Javellana"),  ("Ricardo",        "Kalaw"),
        ("Stella",        "Lacambra"),   ("Teodora",        "Manalo"),
        ("Ulrico",        "Nacion"),     ("Virgie",         "Opeña"),
        ("Walden",        "Paglinawan"), ("Xyza",           "Quijano"),
    ],
    # CCJE — 2 blocks × 4 years × 4 = 32 needed
    "CCJE": [
        ("Danilo Jr.",    "Tiongco"),    ("Maricel",        "Umali"),
        ("Richard",       "Valdez"),     ("Josephine",      "Wenceslao"),
        ("Arnel",         "Ybañez"),     ("Clarissa",       "Zobel"),
        ("Bonifacio",     "Acuna"),      ("Corazon",        "Bacani"),
        ("Dionisio",      "Calanda"),    ("Esperanza",      "Dalida"),
        ("Fidel",         "Emilio"),     ("Gertrude",       "Feria"),
        ("Hermenegildo",  "Galang"),     ("Iluminada",      "Holgado"),
        ("Jacinto",       "Ibanez"),     ("Katrina",        "Jocson"),
        ("Leandro",       "Katigbak"),   ("Milagros",       "Lacson"),
        ("Narciso",       "Magpayo"),    ("Olivia",         "Nalapo"),
        ("Porfirio",      "Occeña"),     ("Quirita",        "Padua"),
        ("Rogelio",       "Quiao"),      ("Salome",         "Rañola"),
        ("Timoteo",       "Sarreal"),    ("Ursula",         "Tamayo"),
        ("Valeriana",     "Ucol"),       ("Wilfredo",       "Vidad"),
        ("Xenia",         "Wijangco"),   ("Yolanda",        "Xenos"),
        ("Zacarias",      "Yumang"),     ("Anita",          "Zuñiga"),
    ],
    # HSD — 2 blocks × 6 grade levels × 4 = 48 needed
    "HSD": [
        ("Liam",          "Ramos"),      ("Sofia",          "Cruz"),
        ("Ethan",         "Santos"),     ("Isabella",       "Reyes"),
        ("Noah",          "Bautista"),   ("Olivia",         "Garcia"),
        ("Lucas",         "Mendoza"),    ("Mia",            "Torres"),
        ("James",         "Aquino"),     ("Ella",           "Dela Rosa"),
        ("Oliver",        "Pascual"),    ("Ava",            "Navarro"),
        ("Benjamin",      "Abad"),       ("Emma",           "Bernal"),
        ("William",       "Cortez"),     ("Charlotte",      "Dimaculangan"),
        ("Elijah",        "Esguerra"),   ("Amelia",         "Flores"),
        ("Henry",         "Guillermo"),  ("Harper",         "Hernandez"),
        ("Sebastian",     "Ibarra"),     ("Evelyn",         "Jimenez"),
        ("Jack",          "Kalaw"),      ("Abigail",        "Lacuesta"),
        ("Michael",       "Macaraig"),   ("Emily",          "Narvasa"),
        ("Owen",          "Obligacion"), ("Elizabeth",      "Paras"),
        ("Daniel",        "Quibuyen"),   ("Mila",           "Roxas"),
        ("Matthew",       "Salonga"),    ("Camila",         "Tirona"),
        ("Logan",         "Ureta"),      ("Penelope",       "Virata"),
        ("Alexander",     "Wenceslao"),  ("Riley",          "Xu"),
        ("Jayden",        "Yaptinchay"), ("Zoey",           "Zafra"),
        ("Aiden",         "Abaya"),      ("Nora",           "Batino"),
        ("Caleb",         "Cuevas"),     ("Luna",           "Diokno"),
        ("Ryan",          "Estanislao"), ("Aria",           "Fonacier"),
        ("Isaac",         "Guanzon"),    ("Lillian",        "Hidalgo"),
        ("Dylan",         "Ilustrisimo"),("Hazel",          "Javier"),
    ],
}


PROGRAMS = {
    "CCS":  "BSCS",
    "CBAA": "BSBA",
    "CED":  "BSED",
    "CN":   "BSN",
    "CCJE": "BSCrim",
    "CLA":  "AB",
    "TETD": "BTVTED",
    "GS":   "MIT",
    "HSD":  "SHS",
}

# Enrollment years per year level
ENROLL_YEAR = {
    "1st Year": "24", "2nd Year": "23", "3rd Year": "22", "4th Year": "21",
    "Grade 7":  "24", "Grade 8":  "23", "Grade 9":  "22",
    "Grade 10": "21", "Grade 11": "20", "Grade 12": "19",
}

students_by_block = {}   # (short, yr, block) -> [User]

for short, names in STUDENT_NAMES.items():
    _, dept_code = dept_objs[short]
    program = PROGRAMS.get(short, "BS")
    year_levels_for_dept = YEAR_LEVELS_MAP.get(short, ["1st Year", "2nd Year", "3rd Year", "4th Year"])
    n_blocks = 3 if short in ("CCS", "CBAA") else 2
    block_list = BLOCKS[:n_blocks]

    # Distribute students across year levels and blocks
    idx = 0
    for yr in year_levels_for_dept:
        enroll_yr = ENROLL_YEAR.get(yr, "24")
        if (short, yr) not in yl_objs:
            continue

        seq_counter = 1   # simple running number per dept+year — no block/year digits embedded
        for blk in block_list:
            key = (short, yr, blk)
            students_by_block[key] = []
            per_block = 5 if short in ("CCS", "CBAA") else 4
            for _ in range(per_block):
                if idx >= len(names):
                    # Generate a generic name if we run out
                    first = f"Student"
                    last  = f"{seq_counter:02d}"
                else:
                    first, last = names[idx]
                    idx += 1

                # Clean 6-digit ID: year(2) + dept(2) + seq(2)
                student_id = f"{enroll_yr}{dept_code}{seq_counter:02d}"

                email = f"{student_id}@student.mabini.edu.ph"
                full_last = f"{last} ({program})"

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
                if created:
                    print(f"  [{student_id}] {first} {last} — {program} {yr} {blk}")
                
                seq_counter += 1

print(f"  Students created.")

# ─── Schedules, Records, Grades ───────────────────────────────────────────────
print("\n[8/8] Building schedules, grades & assessments...")

total_records = 0
for (short, yr, blk), section in block_objs.items():
    subjects = subj_objs.get(short, [])
    if not subjects:
        continue
    students = students_by_block.get((short, yr, blk), [])
    if not students:
        continue

    for subj in subjects:
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
            # Assessment type weights (preserve original logic)
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
                # Compute grade from assessments (Quiz 30%, Activity 30%, Exam 40%)
                quiz_scores    = [round(random.uniform(70, 100), 2) for _ in range(3)]
                activity_scores= [round(random.uniform(72, 100), 2) for _ in range(3)]
                exam_score     = round(random.uniform(68, 98), 2)

                quiz_avg    = sum(quiz_scores)    / len(quiz_scores)
                activity_avg= sum(activity_scores)/ len(activity_scores)

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
                    defaults={"score": Decimal(str(exam_score))}
                )

                base_date += timedelta(weeks=5)

            # Final average: sum(period_grade * 25%) for all 4 periods
            avg = sum(g * Decimal("0.25") for g in period_grades)
            record.average = avg.quantize(Decimal("0.01"))
            record.save()
            total_records += 1

            # Attendance — 10 days (2 weeks)
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

print()
print("=" * 55)
print("  DONE! Database seeded successfully.")
print("=" * 55)
print()
print("Login credentials:")
print("  Admin    -> admin / admin123")
print("  Faculty  -> FAC001-FAC009 / faculty2024")
print("  Students -> (6-digit ID) / student2024")
print()
print("Sample student IDs:")
for (short, yr, blk), studs in list(students_by_block.items())[:3]:
    program = PROGRAMS.get(short, "BS")
    print(f"  {short} {yr} {blk}:")
    for s in studs[:3]:
        print(f"    [{s.username}] {s.get_full_name()} ({program})")
    print()
