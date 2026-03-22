import re
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response

from jobs.models import Vacancy, Freelance, Project
from users.models import UserProfile, Skill

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

top_cities_ru = data["top_cities_ru"] 
job_filters = data["job_filters"]     
top_universities_ru = data["top_universities_ru"] 


class Search:
    def __init__(self, user):
        self.user = user
        self.user_tokens = self._user_tokens()  # токены пользователя

    def tokenize(self, text: str):
        if not text:
            return set()
        text = text.lower()
        words = re.findall(r"\w+", text)  # токены из текста
        return set(words)

    def _user_tokens(self):
        if not self.user.is_authenticated:
            return set()
        try:
            profile = self.user.userprofile
        except UserProfile.DoesNotExist:
            return set()
        skills = " ".join([s.name for s in profile.skills.all()])
        text = f"{profile.bio} {skills}"
        return self.tokenize(text)

    def obj_tokens(self, obj):
        skills = " ".join([s.name for s in getattr(obj, "skills", []).all()]) if hasattr(obj, "skills") else ""
        title = getattr(obj, "title", "")
        description = getattr(obj, "description", "")
        text = f"{title} {skills} {description}"
        return self.tokenize(text)

    def similarity(self, set1, set2):
        if not set1 or not set2:
            return 0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def apply_filters(self, queryset, direction=None, profession=None, city=None):
        if direction and direction in job_filters:
            professions = job_filters[direction]
            queryset = queryset.filter(title__in=professions)  # фильтр по направлениям
        if profession:
            queryset = queryset.filter(title__icontains=profession)  # фильтр по профессии
        if city and city in top_cities_ru:
            queryset = queryset.filter(city=city)  # фильтр по городу
        return queryset

    def search_vacancies(self, direction=None, profession=None, city=None,
                          schedule=None, experience=None, work_format=None, limit=20):
        qs = Vacancy.objects.prefetch_related("skills").all()  # все вакансии
        qs = self.apply_filters(qs, direction, profession, city)
        if schedule:
            qs = qs.filter(schedule=schedule)
        if experience:
            qs = qs.filter(experience=experience)
        if work_format:
            qs = qs.filter(work_format=work_format)
        scored = [(v, self.similarity(self.user_tokens, self.obj_tokens(v))) for v in qs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [v[0] for v in scored[:limit]]

    def search_freelance(self, direction=None, profession=None, city=None, limit=20):
        qs = Freelance.objects.prefetch_related("skills").all()  # все фриланс проекты
        qs = self.apply_filters(qs, direction, profession, city)
        scored = [(f, self.similarity(self.user_tokens, self.obj_tokens(f))) for f in qs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in scored[:limit]]

    def search_projects(self, direction=None, profession=None, city=None, limit=20):
        qs = Project.objects.prefetch_related("skills").all()  # все проекты
        qs = self.apply_filters(qs, direction, profession, city)
        scored = [(p, self.similarity(self.user_tokens, self.obj_tokens(p))) for p in qs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in scored[:limit]]

    def search_resumes(self, direction=None, profession=None, city=None, university=None, limit=20):
        qs = UserProfile.objects.prefetch_related("skills").all()  # все резюме
        if direction and direction in job_filters:
            professions = job_filters[direction]
            qs = qs.filter(user__vacancies__title__in=professions).distinct()
        if profession:
            qs = qs.filter(user__vacancies__title__icontains=profession).distinct()
        if city and city in top_cities_ru:
            qs = qs.filter(city=city)
        if university and university in top_universities_ru:
            qs = qs.filter(university__icontains=university)
        scored = [(r, self.similarity(self.user_tokens, self.obj_tokens(r))) for r in qs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in scored[:limit]]


@api_view(["GET"])
def search(request):
    user = request.user
    tab = request.GET.get("tab")  # выбор поиска: vacancies/freelance/projects/resumes

    direction = request.GET.get("direction")
    profession = request.GET.get("profession")
    city = request.GET.get("city")
    schedule = request.GET.get("schedule")
    experience = request.GET.get("experience")
    work_format = request.GET.get("work_format")
    university = request.GET.get("university")

    engine = Search(user)

    if tab == "freelance":
        results = engine.search_freelance(direction, profession, city)
    elif tab == "projects":
        results = engine.search_projects(direction, profession, city)
    elif tab == "resumes":
        results = engine.search_resumes(direction, profession, city, university)
    else:
        results = engine.search_vacancies(direction, profession, city,
                                          schedule, experience, work_format)

    data = []
    for obj in results:
        obj_data = {
            "id": getattr(obj, "id", None),
            "title": getattr(obj, "title", None),
            "city": getattr(obj, "city", None),
            "schedule": getattr(obj, "schedule", None),
            "experience": getattr(obj, "experience", None),
            "work_format": getattr(obj, "work_format", None),
        }
        if isinstance(obj, UserProfile):
            obj_data.update({
                "user_id": obj.user.id,
                "bio": obj.bio,
                "skills": [s.name for s in obj.skills.all()],
                "university": getattr(obj, "university", None),
                "city": getattr(obj, "city", None),
            })
        data.append(obj_data)

    return Response(data)