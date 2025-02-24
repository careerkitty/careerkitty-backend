import fitz  # PyMuPDF for PDF file processing
import textract
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from bson import ObjectId
from django.conf import settings
from .serializers import JobDescriptionSerializer, ResumeSerializer, MatchSerializer
from utils.utils import analyze_match, extract_skills, extract_education, extract_experience, extract_title, extract_text_from_file, extract_responsibilities

# Access MongoDB
db = settings.MONGO_DB


class JobDescriptionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # Extract job description text
        job_desc_file = request.FILES.get('file', None)
        if job_desc_file:
            # Extract text from the file
            job_desc_text = extract_text_from_file(job_desc_file)

            # Extract structured data from the text
            title = extract_title(job_desc_text)
            required_skills = extract_skills(job_desc_text)
            education = extract_education(job_desc_text)
            responsibilities = extract_experience(job_desc_text)
            years_of_experience = extract_experience(job_desc_text) 
            responsibilities = extract_responsibilities(job_desc_text)

            # Save the job description to MongoDB
            job_data = {
                "title": title,
                "description": job_desc_text,
                "required_skills": required_skills,
                "education": education,
                "responsibilities": responsibilities,
                "years_of_experience": years_of_experience, 
                "file": job_desc_file.name
            }

            job_id = db.job_descriptions.insert_one(job_data).inserted_id
            job_data["_id"] = str(job_id)  # Convert ObjectId to string for response
            return Response(job_data, status=status.HTTP_201_CREATED)
        
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)


class ResumeView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # Check if file is uploaded
        resume_file = request.FILES.get('file', None)
        if resume_file:
            # Extract text from the uploaded file
            resume_text = extract_text_from_file(resume_file)

            # Automatically extract information from the text
            skills = extract_skills(resume_text)
            education = extract_education(resume_text)
            responsibilities = extract_responsibilities(resume_text)
            experience = extract_experience(resume_text)
            
            # Build the resume data dictionary
            resume_data = {
                "skills": skills,
                "education": education,
                "responsibilities": responsibilities,
                "experience": experience,
                "file": resume_file.name
            }
            
            # Save the resume data to MongoDB
            resume_id = db.resumes.insert_one(resume_data).inserted_id
            resume_data["_id"] = str(resume_id)  # Convert ObjectId to string for response
            return Response(resume_data, status=status.HTTP_201_CREATED)
        
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)


class MatchView(APIView):
    def post(self, request):
        job_desc_id = request.data.get('job_desc_id')
        resume_id = request.data.get('resume_id')

        try:
            job_desc = db.job_descriptions.find_one({"_id": ObjectId(job_desc_id)})
            resume = db.resumes.find_one({"_id": ObjectId(resume_id)})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not job_desc or not resume:
            return Response({"error": "Invalid job description or resume ID"}, status=status.HTTP_404_NOT_FOUND)

        # Call analyze_match with responsibilities as additional parameters.
        # The analyze_match function should be updated to accept 6 parameters.
        match_score = analyze_match(
            job_desc.get("description", ""),
            resume.get("experience", ""),
            job_desc.get("required_skills", []),
            resume.get("skills", []),
            job_desc.get("responsibilities", ""),
            resume.get("responsibilities", "")
        )
        match_score = float(match_score)  # Ensure native float

        # Skills comparison
        job_skills = job_desc.get("required_skills", [])
        resume_skills = resume.get("skills", [])
        matched_skills = list(set(job_skills) & set(resume_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))

        # Responsibilities comparison.
        # Assuming responsibilities are stored as a comma-separated string.
        job_resp_str = job_desc.get("responsibilities", "Not specified")
        resume_resp_str = resume.get("responsibilities", "Not specified")
        if job_resp_str != "Not specified":
            job_resp_list = [x.strip().lower() for x in job_resp_str.split(",") if x.strip()]
        else:
            job_resp_list = []
        if resume_resp_str != "Not specified":
            resume_resp_list = [x.strip().lower() for x in resume_resp_str.split(",") if x.strip()]
        else:
            resume_resp_list = []
        matched_responsibilities = list(set(job_resp_list) & set(resume_resp_list))
        missing_responsibilities = list(set(job_resp_list) - set(resume_resp_list))

        # Education comparison
        job_education = job_desc.get("education", "Not specified")
        resume_education = resume.get("education", "Not specified")
        # Simple comparison: True if they match (ignoring case), otherwise False.
        education_match = (job_education.lower() == resume_education.lower())

        # Create match record including extra details.
        match_data = {
            "job_desc_id": job_desc_id,
            "resume_id": resume_id,
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_responsibilities": matched_responsibilities,
            "missing_responsibilities": missing_responsibilities,
            "job_education": job_education,
            "resume_education": resume_education,
            "education_match": education_match,
            "feedback": "Feedback will be generated based on missing skills, responsibilities, and education"
        }
        match_id = db.matches.insert_one(match_data).inserted_id
        match_data["_id"] = str(match_id)

        return Response(match_data, status=status.HTTP_200_OK)
