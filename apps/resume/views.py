from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import json
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.parsers import FormParser


from .models import (
    Resume, Aloqa, Konikma, Til,
    IshTajribasi, Talim, Sertifikat,
    Maqola, Qiziqish, Yutuq
)
from .serializers import (
    ResumeSerializer, AloqaSerializer, KonikmaSerializer,
    TilSerializer, IshTajribasiSerializer, TalimSerializer,
    SertifikatSerializer, MaqolaSerializer, QiziqishSerializer,
    YutuqSerializer, RoyxatdanOtishSerializer
)


SECTION_REGISTRY = {
    'konikmalar':    (Konikma,      KonikmaSerializer),
    'tillar':        (Til,           TilSerializer),
    'ish-tajribasi': (IshTajribasi,  IshTajribasiSerializer),
    'talim':         (Talim,         TalimSerializer),
    'sertifikatlar': (Sertifikat,    SertifikatSerializer),
    'maqolalar':     (Maqola,        MaqolaSerializer),
    'qiziqishlar':   (Qiziqish,      QiziqishSerializer),
    'yutuqlar':      (Yutuq,         YutuqSerializer),
}

SECTION_EXAMPLES = {
    'konikmalar': {
        'nom': 'Python',
        'daraja': 'yuqori',
        'kategoriya': 'Dasturlash tillari',
    },
    'tillar': {
        'til_nomi': 'Ingliz tili',
        'daraja': 'b2',
    },
    'ish-tajribasi': {
        'kompaniya_nomi': 'ABC Company',
        'lavozim': 'Backend Developer',
        'ish_turi': 'tolik',
        'boshlanish_sanasi': '2022-01-01',
        'hozir_ishlayapman': True,
        'tavsif': 'Django, DRF bilan backend ishlab chiqdim',
        'shahar': 'Toshkent',
    },
    'talim': {
        'muassasa_nomi': 'TATU',
        'daraja': 'bakalavr',
        'mutaxassislik': 'Dasturiy injiniring',
        'boshlanish_yili': 2019,
        'hozir_oqiyapman': True,
    },
    'sertifikatlar': {
        'nomi': 'AWS Solutions Architect',
        'tashkilot': 'Amazon',
        'berilgan_sana': '2023-06-01',
        'muddatsiz': False,
        'amal_qilish_muddati': '2026-06-01',
        'sertifikat_id': 'AWS-12345',
        'havola': 'https://aws.amazon.com/verify',
    },
    'maqolalar': {
        'sarlavha': 'Django da REST API yaratish',
        'nashriyot': 'Medium',
        'nashr_sanasi': '2024-01-15',
        'havola': 'https://medium.com/maqola',
        'tavsif': 'DRF yordamida API yaratish haqida',
    },
    'qiziqishlar': {
        'nom': 'Kitob o\'qish',
    },
    'yutuqlar': {
        'nomi': 'Xakaton 1-o\'rin',
        'tashkilot': 'IT Park',
        'sana': '2023-05-01',
        'tavsif': 'Milliy xakatonda birinchi o\'rin egallash',
    },
}




@extend_schema(tags=["Resume"])
class ResumeView(APIView):
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]


    def get(self, request):
        resume = get_object_or_404(Resume, foydalanuvchi=request.user)
        return Response(ResumeSerializer(resume).data)

    # def post(self, request):
    #     if Resume.objects.filter(foydalanuvchi=request.user).exists():
    #         return Response(
    #             {'xato': 'Resume allaqachon mavjud. PUT orqali yangilang.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #     resume_data = {k: v for k, v in request.data.items() if k != 'aloqa'}
    #     resume_serializer = ResumeSerializer(data=resume_data)
    #     if not resume_serializer.is_valid():
    #         return Response(resume_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     resume = resume_serializer.save(foydalanuvchi=request.user)
    #
    #     aloqa_data = request.data.get('aloqa')
    #     if aloqa_data:
    #         aloqa_serializer = AloqaSerializer(data=aloqa_data)
    #         if aloqa_serializer.is_valid():
    #             aloqa_serializer.save(resume=resume)
    #
    #     return Response(ResumeSerializer(resume).data, status=status.HTTP_201_CREATED)
    #
    # def put(self, request):
    #     resume = get_object_or_404(Resume, foydalanuvchi=request.user)
    #     resume_data = {k: v for k, v in request.data.items() if k != 'aloqa'}
    #     if resume_data:
    #         resume_serializer = ResumeSerializer(resume, data=resume_data, partial=True)
    #         if not resume_serializer.is_valid():
    #             return Response(resume_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #         resume_serializer.save()
    #
    #     aloqa_data = request.data.get('aloqa')
    #     if aloqa_data:
    #         aloqa, _ = Aloqa.objects.get_or_create(resume=resume)
    #         aloqa_serializer = AloqaSerializer(aloqa, data=aloqa_data, partial=True)
    #         if aloqa_serializer.is_valid():
    #             aloqa_serializer.save()
    #
    #     return Response(ResumeSerializer(resume).data)
    def post(self, request):
        if Resume.objects.filter(foydalanuvchi=request.user).exists():
            return Response(
                {'xato': 'Resume allaqachon mavjud. PUT orqali yangilang.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # request.data dan xavfsiz nusxa olamiz (FormData kelganda ham to'g'ri ishlashi uchun)
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        aloqa_data = data.get('aloqa')

        # Agar aloqa ma'lumoti frontenddan obyekt emas, string (matn) bo'lib kelib qolsa, uni dict-ga o'giramiz
        if isinstance(aloqa_data, str):
            try:
                aloqa_data = json.loads(aloqa_data)
            except json.JSONDecodeError:
                aloqa_data = None

        resume_data = {k: v for k, v in data.items() if k != 'aloqa'}
        resume_serializer = ResumeSerializer(data=resume_data)

        if not resume_serializer.is_valid():
            return Response(resume_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        resume = resume_serializer.save(foydalanuvchi=request.user)

        if aloqa_data:
            aloqa_serializer = AloqaSerializer(data=aloqa_data)
            if aloqa_serializer.is_valid():
                aloqa_serializer.save(resume=resume)

        return Response(ResumeSerializer(resume).data, status=status.HTTP_201_CREATED)

    def put(self, request):
        resume = get_object_or_404(Resume, foydalanuvchi=request.user)

        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        resume_data = {k: v for k, v in data.items() if k != 'aloqa'}

        if resume_data:
            resume_serializer = ResumeSerializer(resume, data=resume_data, partial=True)
            if not resume_serializer.is_valid():
                return Response(resume_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            resume_serializer.save()

        aloqa_data = data.get('aloqa')
        # Bu yerda ham string bo'lib kelsa dict-ga o'giramiz
        if isinstance(aloqa_data, str):
            try:
                aloqa_data = json.loads(aloqa_data)
            except json.JSONDecodeError:
                aloqa_data = None

        if aloqa_data:
            aloqa, _ = Aloqa.objects.get_or_create(resume=resume)
            aloqa_serializer = AloqaSerializer(aloqa, data=aloqa_data, partial=True)
            if aloqa_serializer.is_valid():
                aloqa_serializer.save()

        return Response(ResumeSerializer(resume).data)



@extend_schema(tags=["Bo'limlar"])
class ResumeSectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_entry(self, section):
        return SECTION_REGISTRY.get(section, (None, None))

    def _resume(self, user):
        return get_object_or_404(Resume, foydalanuvchi=user)

    @extend_schema(
        summary="Bo'lim ro'yxatini olish",
        responses={200: OpenApiResponse(description="Ro'yxat")},
    )
    def get(self, request, section):
        model, serializer_class = self._get_entry(section)
        if not model:
            return Response(
                {'xato': f"'{section}' topilmadi. Mavjudlar: {', '.join(SECTION_REGISTRY)}"},
                status=status.HTTP_404_NOT_FOUND
            )
        resume = self._resume(request.user)
        return Response(serializer_class(model.objects.filter(resume=resume), many=True).data)

    @extend_schema(
        summary="Bo'limga yangi yozuv qo'shish",
        request={
            'application/json': {
                'type': 'object',
                'description': 'Har bir section uchun namunani "Examples" dan tanlang',
            }
        },
        responses={
            201: OpenApiResponse(description="Muvaffaqiyatli qo'shildi"),
            400: OpenApiResponse(description="Xato ma'lumotlar"),
        },
        examples=[
            OpenApiExample(
                'konikmalar',
                summary='konikmalar uchun',
                value=SECTION_EXAMPLES['konikmalar'],
                request_only=True,
            ),
            OpenApiExample(
                'tillar',
                summary='tillar uchun',
                value=SECTION_EXAMPLES['tillar'],
                request_only=True,
            ),
            OpenApiExample(
                'ish-tajribasi',
                summary='ish-tajribasi uchun',
                value=SECTION_EXAMPLES['ish-tajribasi'],
                request_only=True,
            ),
            OpenApiExample(
                'talim',
                summary='talim uchun',
                value=SECTION_EXAMPLES['talim'],
                request_only=True,
            ),
            OpenApiExample(
                'sertifikatlar',
                summary='sertifikatlar uchun',
                value=SECTION_EXAMPLES['sertifikatlar'],
                request_only=True,
            ),
            OpenApiExample(
                'maqolalar',
                summary='maqolalar uchun',
                value=SECTION_EXAMPLES['maqolalar'],
                request_only=True,
            ),
            OpenApiExample(
                'qiziqishlar',
                summary='qiziqishlar uchun',
                value=SECTION_EXAMPLES['qiziqishlar'],
                request_only=True,
            ),
            OpenApiExample(
                'yutuqlar',
                summary='yutuqlar uchun',
                value=SECTION_EXAMPLES['yutuqlar'],
                request_only=True,
            ),
        ]
    )
    def post(self, request, section):
        model, serializer_class = self._get_entry(section)
        if not model:
            return Response(
                {'xato': f"'{section}' topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(resume=self._resume(request.user))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Bo'limlar"])
class ResumeSectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, section, pk, user):
        entry = SECTION_REGISTRY.get(section)
        if not entry:
            return None, None
        model, serializer_class = entry
        resume = get_object_or_404(Resume, foydalanuvchi=user)
        return get_object_or_404(model, pk=pk, resume=resume), serializer_class

    @extend_schema(summary="Bitta yozuvni olish")
    def get(self, request, section, pk):
        obj, serializer_class = self._get_object(section, pk, request.user)
        if obj is None:
            return Response({'xato': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer_class(obj).data)

    @extend_schema(
        summary="Yozuvni yangilash",
        request={
            'application/json': {
                'type': 'object',
                'description': 'Yangilamoqchi bo\'lgan maydonlarni kiriting',
            }
        },
        responses={200: OpenApiResponse(description="Yangilandi")},
        examples=[
            OpenApiExample(
                'konikmalar', summary='konikmalar uchun',
                value=SECTION_EXAMPLES['konikmalar'], request_only=True,
            ),
            OpenApiExample(
                'tillar', summary='tillar uchun',
                value=SECTION_EXAMPLES['tillar'], request_only=True,
            ),
            OpenApiExample(
                'ish-tajribasi', summary='ish-tajribasi uchun',
                value=SECTION_EXAMPLES['ish-tajribasi'], request_only=True,
            ),
            OpenApiExample(
                'talim', summary='talim uchun',
                value=SECTION_EXAMPLES['talim'], request_only=True,
            ),
            OpenApiExample(
                'sertifikatlar', summary='sertifikatlar uchun',
                value=SECTION_EXAMPLES['sertifikatlar'], request_only=True,
            ),
            OpenApiExample(
                'maqolalar', summary='maqolalar uchun',
                value=SECTION_EXAMPLES['maqolalar'], request_only=True,
            ),
            OpenApiExample(
                'qiziqishlar', summary='qiziqishlar uchun',
                value=SECTION_EXAMPLES['qiziqishlar'], request_only=True,
            ),
            OpenApiExample(
                'yutuqlar', summary='yutuqlar uchun',
                value=SECTION_EXAMPLES['yutuqlar'], request_only=True,
            ),
        ]
    )
    def put(self, request, section, pk):
        obj, serializer_class = self._get_object(section, pk, request.user)
        if obj is None:
            return Response({'xato': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        serializer = serializer_class(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Yozuvni o'chirish", responses={204: None})
    def delete(self, request, section, pk):
        obj, _ = self._get_object(section, pk, request.user)
        if obj is None:
            return Response({'xato': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"xabar": "Muvaffaqiyatli o'chirildi."}, status=status.HTTP_204_NO_CONTENT)