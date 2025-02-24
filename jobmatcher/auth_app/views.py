import uuid
import bcrypt
import jwt
import datetime
import fitz  # PyMuPDF for PDF extraction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserSerializer
from utils.utils import extract_text_from_file, extract_skills, extract_education, extract_experience

SECRET_KEY = "your-secret-key"  # Change this in production

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # Check if user already exists
            if UserProfile.get_by_email(email):
                return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Extract resume data if uploaded
            resume_file = request.FILES.get("resume_file")
            if resume_file:
                resume_text = extract_text_from_file(resume_file)
                skills = extract_skills(resume_text)
                education = extract_education(resume_text)
                experience = extract_experience(resume_text)
            else:
                skills, education, experience = [], "Not specified", "Not specified"

            # Store user data
            user_data = {
                "_id": str(uuid.uuid4()),
                "email": email,
                "password": hashed_password,
                "name": serializer.validated_data.get("name", ""),
                "skills": skills,
                "education": education,
                "experience": experience,
            }
            UserProfile.create(user_data)
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = UserProfile.get_by_email(email)
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = {
            "user_id": str(user["_id"]),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return Response({"token": token, "user": user}, status=status.HTTP_200_OK)
