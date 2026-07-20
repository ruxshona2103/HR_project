from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CandidateProfile
from .serializers import CandidateSerializer

@api_view(['GET'])
def get_my_profile(request):
    """Profilingizni ko'rish endpointi"""
    profile = CandidateProfile.objects.first()
    if profile:
        serializer = CandidateSerializer(profile)
        return Response(serializer.data)
    return Response({"error": "Profil topilmadi"}, status=404)

@api_view(['POST'])
def ai_resume_check(request):
    """Siz yozgan AI mantiqi (Hozircha simulyatsiya)"""
    return Response({
        "score": 92,
        "feedback": "Husan tomonidan yaratilgan AI tahlili: Rezyumeingiz juda sifatli!",
        "status": "Success"
    })