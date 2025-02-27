from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import UserProfile
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import bcrypt
import jwt
import datetime
from utils.utils import extract_responsibilities, extract_text_from_file, extract_skills, extract_education, extract_experience

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
                responsibilities = extract_responsibilities(resume_text)
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
                "responsibilities": responsibilities,
            }
            UserProfile.create(user_data)
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Fetch user from MongoDB
        user = UserProfile.get_by_email(email)
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Manually create JWT token for MongoDB user
        payload = {
            "user_id": str(user["_id"]),  # Ensure we use the correct field for user id
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return Response({
            "access_token": token,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "skills": user.get("skills", []),
                "education": user.get("education", "Not specified"),
                "experience": user.get("experience", "Not specified"),
                "responsibilities": user.get("responsibilities", "Not specified")
            }
        }, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, user_id=None):
        try:
            # Access user from request (after JWT authentication)
            user = request.user

            # If user ID is provided in the URL, fetch that user's profile
            if user_id:
                if str(user.id) != str(user_id):
                    error_message = "You are not authorized to view this profile."
                    print(f"ERROR: {error_message}")  # Print error to terminal
                    return Response({"error": error_message}, status=status.HTTP_403_FORBIDDEN)
            else:
                # Fetch user by email or ID from query params
                email = request.query_params.get("email")
                if not email:
                    error_message = "Email or User ID is required to fetch profile"
                    print(f"ERROR: {error_message}")  # Print error to terminal
                    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
                if user.email != email:
                    error_message = "You are not authorized to view this profile."
                    print(f"ERROR: {error_message}")  # Print error to terminal
                    return Response({"error": error_message}, status=status.HTTP_403_FORBIDDEN)

            # Build the user profile data
            user_profile = {
                "email": user.email,
                "name": user.get("name", ""),
                "skills": user.get("skills", []),
                "education": user.get("education", "Not specified"),
                "experience": user.get("experience", "Not specified"),
                "responsibilities": user.get("responsibilities", "Not specified")
            }

            return Response({"user_profile": user_profile}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Print the error details directly to the terminal
            print(f"ERROR: An unexpected error occurred while fetching user profile: {str(e)}")  # Print error to terminal
            return Response({"error": "An unexpected error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
