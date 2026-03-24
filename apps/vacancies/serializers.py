from rest_framework import serializers

from .models import Candidate, Vacancy


class VacancySerializer(serializers.ModelSerializer):
    match_score = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vacancy
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        """
        Maosh bilan bog'liq biznes qoidalarini tekshiradi.
        """
        salary_from = attrs.get("salary_from")
        salary_to = attrs.get("salary_to")
        currency = attrs.get("currency")

        if (salary_from or salary_to) and not currency:
            raise serializers.ValidationError(
                {"currency": "Maosh ko'rsatilsa, valyuta tanlash majburiy."}
            )

        if salary_from and salary_to and salary_from > salary_to:
            raise serializers.ValidationError(
                {"salary_to": "Maksimal maosh minimal maoshdan kichik bo'lishi mumkin emas."}
            )

        publish_start = attrs.get("publish_start")
        publish_end = attrs.get("publish_end")
        if publish_start and publish_end and publish_start > publish_end:
            raise serializers.ValidationError(
                {"publish_end": "Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas."}
            )

        return attrs

    def get_match_score(self, obj):
        """
        Candidate bilan moslik foizini hisoblaydi.
        """
        request = self.context.get("request")
        if not request:
            return None

        candidate_id = request.query_params.get("candidate_id")
        if not candidate_id:
            return None

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return None

        score = 0

        vacancy_skills = [
            s.strip().lower() for s in (obj.required_skills or "").split(",") if s.strip()
        ]
        candidate_skills = [
            s.strip().lower() for s in (candidate.skills or "").split(",") if s.strip()
        ]

        if vacancy_skills:
            matched = len(set(vacancy_skills) & set(candidate_skills))
            skill_score = (matched / len(vacancy_skills)) * 50
            score += skill_score

        if obj.min_experience is not None and obj.min_experience > 0:
            if candidate.experience >= obj.min_experience:
                score += 50
            else:
                score += (candidate.experience / obj.min_experience) * 50

        return int(score)