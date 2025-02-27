import fitz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import jwt
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token has expired')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token')

# Load a pre-trained transformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def analyze_match(job_description, resume_text, job_skills, resume_skills, job_responsibilities, resume_responsibilities):
    """
    Analyze the match between a job description and a resume based on:
      1. Text similarity (between job description and resume text)
      2. Skill match percentage
      3. Responsibilities similarity (between job responsibilities and resume responsibilities)
    """
    # Compute text similarity between job description and resume text
    job_embedding = model.encode([job_description])
    resume_embedding = model.encode([resume_text])
    text_similarity = cosine_similarity(job_embedding, resume_embedding)[0][0] * 100

    # Compute skill match percentage
    skill_match_percentage = calculate_skill_match(job_skills, resume_skills)

    # Compute responsibilities similarity if both values are provided
    if job_responsibilities and resume_responsibilities:
        job_resp_embedding = model.encode([job_responsibilities])
        resume_resp_embedding = model.encode([resume_responsibilities])
        responsibilities_similarity = cosine_similarity(job_resp_embedding, resume_resp_embedding)[0][0] * 100
    else:
        responsibilities_similarity = 0

    # Combine the scores into a final match score.
    # For example, you might weight text similarity 50%, skills 30%, and responsibilities 20%.
    final_match_score = (text_similarity * 0.5) + (skill_match_percentage * 0.3) + (responsibilities_similarity * 0.2)
    
    return final_match_score


def calculate_skill_match(job_skills, resume_skills):
    """
    Calculate the percentage of skills matched between job description and resume.
    """
    if not job_skills:
        return 0  # If no skills are listed in job description, return 0 match

    matched_skills = set(job_skills).intersection(set(resume_skills))
    skill_match_percentage = (len(matched_skills) / len(job_skills)) * 100
    return skill_match_percentage

def extract_skills(text):
    """
    Extract skills from the text based on predefined keywords.
    A more advanced technique could use a large skill set or NLP methods for better results.
    """
    skills_keywords = [
        "python", "django", "aws", "javascript", "html", "css", "sql", "mongodb", "docker", "git", 
        "linux", "flask", "fastapi", "java", "typescript", "node.js", "react", "vue", "kubernetes", "cloud"
    ]
    skills = []
    
    # Find skills using regular expressions
    for skill in skills_keywords:
        if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
            skills.append(skill)
    
    # Optionally add more advanced parsing logic here
    return skills

def extract_education(text):
    """
    Extract education level from the text.
    Checks for degrees or specific education-related terms.
    """
    education_keywords = ["bachelor", "master", "phd", "degree", "graduation", "certification"]
    
    # Try to find a degree level from the text
    for keyword in education_keywords:
        if keyword in text.lower():
            if "bachelor" in text.lower():
                return "Bachelor's Degree"
            elif "master" in text.lower():
                return "Master's Degree"
            elif "phd" in text.lower():
                return "Ph.D."
            else:
                return "Degree/Certification"
    
    return "Not specified"

def extract_title(text):
    """
    Extract the job title from the job description text.
    This will look for common job title patterns in the text.
    """
    # You can enhance this with more sophisticated NLP methods if needed
    job_title_keywords = ["developer", "engineer", "designer", "manager", "lead", "specialist", "architect", "analyst"]

    # For simplicity, we'll look for a few key keywords that could indicate a job title
    for keyword in job_title_keywords:
        if keyword in text.lower():
            return keyword.title()  # Capitalize the first letter

    # If no common title found, return a default value
    return "Job Title Not Specified"

def extract_text_from_file(file):
    """
    Extract text from an uploaded file. It supports PDF files for now.
    """
    # Get the file name from the uploaded file object
    file_name = file.name  # This is the filename string
    
    if file_name.endswith('.pdf'):
        doc = fitz.open(stream=file.read(), filetype="pdf")  # Read PDF content
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    else:
        raise ValueError("Unsupported file type")
    

def extract_responsibilities(text):
    """
    Extract responsibilities from the text by looking for common responsibility-related keywords.
    You can adjust the keywords and patterns to fit your requirements.
    """
    # Define keywords/phrases that indicate responsibilities
    responsibility_keywords = [
        "responsible for", "design", "designing", "develop", "developing", "maintain", "maintaining", "manage", "managing", 
        "collaborate", "collaborating", "lead", "coordinate", "coordinating", "optimize", "ship", "write", "test", "debug"
    ] 
    
    found = []
    for keyword in responsibility_keywords:
        # Use a regex search to find if the keyword is present in the text
        if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
            found.append(keyword)
    
    # Return a comma-separated list of found responsibilities or a default message if none are found
    if found:
        return ", ".join(found)
    else:
        return "Not specified"


def extract_experience(text):
    """
    Extract experience-related information (e.g., years of experience, role titles) from the text.
    Uses keywords and phrases to extract relevant experience info.
    """
    experience_keywords = [
        "years of experience", "experience", "worked as", "worked in", "responsible for", 
        "developed", "managed", "led", "engineer", "developer"
    ]
    experience = []

    # Look for patterns related to years of experience or role details
    for keyword in experience_keywords:
        if keyword in text.lower():
            experience.append(keyword)
    
    if not experience:
        return "Not specified"
    
    # Assuming some basic patterns for experience like "3+ years"
    years_of_experience = re.search(r"(\d+[\+\d]*)\s*(?:year|yrs|experience)", text, re.IGNORECASE)
    if years_of_experience:
        return years_of_experience.group(1) + " years"

    return "Not specified"
