from rest_framework import serializers
from .models import Vacancy , Candidate

class VacancySerializer(serializers.ModelSerializer):
    match_score = serializers.SerializerMethodField()

    def get_match_score(self, obj):
        request = self.context.get('request')
        candidate_id = request.query_params.get('candidate_id')

        if not candidate_id:
            return None


        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except:
            return None

        score = 0

        #  skill score
        vacancy_skills = [s.strip().lower() for s in obj.required_skills.split(',')]
        candidate_skills = [s.strip().lower() for s in candidate.skills.split(',')]

        matched = len(set(vacancy_skills) & set(candidate_skills))

        if vacancy_skills:
            skill_score = (matched / len(vacancy_skills)) * 50
            score += skill_score

        #  experience score
        if candidate.experience >= obj.min_experience:
            score += 50
        else:
            if obj.min_experience > 0:
                score += (candidate.experience / obj.min_experience) * 50

        return int(score)

    class Meta:
        model = Vacancy
        fields = '__all__'