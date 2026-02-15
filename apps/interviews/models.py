from django.db import models
from django.conf import settings


class Position(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    required_skills = models.JSONField(default=list)
    experience_required = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    expected_keywords = models.JSONField(default=list, blank=True)
    ai_evaluation_criteria = models.JSONField(default=dict, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position.name} - {self.get_question_type_display()} ({self.get_difficulty_level_display()})"

class Interview(models.Model):
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    total_score = models.FloatField(blank=True, null=True)
    ai_feedback = models.TextField(blank=True)
    final_recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, blank=True)
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.candidate.get_full_name()} - {self.position.name} ({self.get_status_display()})"

    def get_duration(self):
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return duration
        return None

class Answer(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    audio_file = models.FileField(blank=True, null=True)
    video_file = models.FileField(blank=True, null=True)
    ai_score = models.FloatField(blank=True, null=True)
    ai_feedback = models.TextField(blank=True)
    ai_analysis = models.JSONField(default=dict, blank=True)
    time_taken_seconds = models.IntegerField(blank=True, null=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.interview.candidate.get_full_name()} - Q{self.question.id}"

class InterviewFeedback(models.Model):
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE)
    overall_assessment = models.TextField()
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    technical_skills_rating = models.IntegerField(blank=True, null=True)
    communication_rating = models.IntegerField(blank=True, null=True)
    problem_solving_rating = models.IntegerField(blank=True, null=True)
    cultural_fit_rating = models.IntegerField(blank=True, null=True)
    next_steps = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback: {self.interview}"


class AIPromptTemplate(models.Model):
    name = models.CharField(max_length=200, unique=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


