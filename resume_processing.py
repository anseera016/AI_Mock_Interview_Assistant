import os

import spacy
import pytesseract

from pdf2image import convert_from_path
from google import genai


# =========================================================
# CONFIGURATION
# =========================================================

# Poppler location on Windows
POPPLER_PATH = (
    r"C:\Users\user\Downloads\Release-26.09.0-0"
    r"\poppler-26.09.0\Library\bin"
)

# Tesseract OCR location on Windows
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Tell pytesseract where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# =========================================================
# LOAD SPACY
# =========================================================

nlp = spacy.load("en_core_web_sm")


# =========================================================
# GEMINI CLIENT
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Set it in the PowerShell terminal before running the app."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# SECTION EXTRACTION
# =========================================================

def extract_section_from_lines(lines, section_names):
    """
    Extract resume sections based on section headings.
    """

    sections = {}

    current_section = None

    for line in lines:

        line_clean = line.strip()

        matched_section = None

        for name in section_names:

            if line_clean.lower() == name.lower():
                matched_section = name
                break

        if matched_section:

            current_section = matched_section
            sections[current_section] = []

            continue

        if current_section:

            sections[current_section].append(line)

    return sections


# =========================================================
# RESUME PROCESSING
# =========================================================

def process_uploaded_resume(file_path):
    """
    Convert the uploaded PDF into images,
    perform OCR, and extract resume information.
    """

    # -----------------------------------------------------
    # Convert PDF pages to images
    # -----------------------------------------------------

    pages = convert_from_path(
        file_path,
        poppler_path=POPPLER_PATH
    )

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    resume_text = ""

    for page_image in pages:

        page_text = pytesseract.image_to_string(
            page_image
        )

        resume_text += page_text + "\n"

    # -----------------------------------------------------
    # spaCy processing
    # -----------------------------------------------------

    doc = nlp(resume_text)

    # Clean lines
    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    # -----------------------------------------------------
    # Resume sections
    # -----------------------------------------------------

    section_names = [
        "Education",
        "Experience",
        "Work Experience",
        "Employment History",
        "Skills",
        "Technical Skills",
        "Projects",
        "Certifications",
        "Courses",
        "Languages",
        "Achievements",
        "Personal Information",
        "Profile",
        "Summary",
        "Objective",
    ]

    sections = extract_section_from_lines(
        lines,
        section_names
    )

    # -----------------------------------------------------
    # Employment history
    # -----------------------------------------------------

    employment_history = []

    for section_name in [
        "Experience",
        "Work Experience",
        "Employment History",
    ]:

        if section_name in sections:

            employment_history.extend(
                sections[section_name]
            )

    # -----------------------------------------------------
    # Certifications
    # -----------------------------------------------------

    certifications = sections.get(
        "Certifications",
        []
    )

    # -----------------------------------------------------
    # Courses
    # -----------------------------------------------------

    courses = sections.get(
        "Courses",
        []
    )

    # -----------------------------------------------------
    # Skills
    # -----------------------------------------------------

    skills = []

    for section_name in [
        "Skills",
        "Technical Skills",
    ]:

        if section_name in sections:

            skills.extend(
                sections[section_name]
            )

    # -----------------------------------------------------
    # Languages
    # -----------------------------------------------------

    languages = sections.get(
        "Languages",
        []
    )

    # -----------------------------------------------------
    # Personal information
    # -----------------------------------------------------

    personal_info = {}

    for entity in doc.ents:

        if entity.label_ in [
            "PERSON",
            "EMAIL",
            "PHONE",
            "GPE",
            "ORG",
        ]:

            personal_info[
                entity.label_
            ] = entity.text

    # -----------------------------------------------------
    # Final profile
    # -----------------------------------------------------

    profile = {
        "personal_info": personal_info,
        "employment_history": employment_history,
        "certifications": certifications,
        "courses": courses,
        "skills": skills,
        "languages": languages,
        "sections": sections,
        "resume_text": resume_text,
    }

    return profile


# =========================================================
# GENERATE INTERVIEW QUESTIONS
# =========================================================

def generate_questions(resume_profile):
    """
    Generate exactly 8 personalized interview questions
    using Gemini.
    """

    # Don't send unnecessary raw personal information
    profile_for_questions = {
        section: content
        for section, content in resume_profile.items()
        if section != "personal_info"
    }

    question_prompt = f"""
You are an AI mock interview assistant.

Your purpose is interview practice and self-improvement.

Analyze the candidate's resume information below and generate
exactly 8 personalized interview questions.

The questions should be appropriate for a mock interview.

Requirements:

1. Generate exactly 8 questions.
2. Questions must be based on the resume.
3. Include a mixture of:
   - introduction/background
   - education or experience
   - projects
   - technical skills
   - problem solving
   - teamwork
   - behavioral questions
   - learning/adaptability
4. Avoid questions that cannot reasonably be connected to the resume.
5. Do not provide answers.
6. Do not number the questions.
7. Return only the 8 questions.
8. Each question must be on a separate line.

Resume information:

{profile_for_questions}
"""

    # -----------------------------------------------------
    # Gemini request
    # -----------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=question_prompt
    )

    return response.text


# =========================================================
# CREATE INTERVIEW QUESTIONS
# =========================================================

def create_interview_questions(resume_profile):
    """
    Convert Gemini output into a clean list of questions.
    """

    questions_text = generate_questions(
        resume_profile
    )

    questions = []

    for line in questions_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove common numbering formats
        if len(line) > 2:

            if line[0].isdigit() and line[1] in [".", ")"]:
                line = line[2:].strip()

            elif (
                len(line) > 3
                and line[0].isdigit()
                and line[1].isdigit()
                and line[2] in [".", ")"]
            ):
                line = line[3:].strip()

        if line:
            questions.append(line)

    # Return maximum 8 questions
    return questions[:8]