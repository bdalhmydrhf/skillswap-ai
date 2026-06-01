import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Q, Avg
from django.core.cache import cache
from django.db import transaction
from core.models import UserProfile, Skill, Contract, ContractRating
from django.contrib.auth.models import User
from django.utils import timezone
import math
import logging

logger = logging.getLogger(__name__)

# أوزان المعايير
WEIGHTS = {
    'skills': 0.5,
    'description': 0.2,
    'trust': 0.15,
    'rating': 0.1,
    'completion': 0.05
}

def calculate_trust_score(user_profile):
    """دالة موحدة لحساب الثقة"""
    try:
        user = user_profile.user
        
        # إحصائيات العقود
        total_contracts = Contract.objects.filter(
            Q(client=user) | Q(freelancer=user)
        ).count()

        completed_contracts = Contract.objects.filter(
            (Q(client=user) | Q(freelancer=user)) & 
            Q(status='completed')
        ).count()

        completion_rate = (completed_contracts / total_contracts * 100) if total_contracts > 0 else 0

        # التقييمات المتوسطة
        avg_rating_result = ContractRating.objects.filter(
            rated_user=user
        ).aggregate(avg_rating=Avg('rating'))
        avg_rating = avg_rating_result['avg_rating'] or 0

        # سرعة الرد
        response_score = max(0, 100 - (user_profile.avg_response_time or 0))

        # خوارزمية الثقة النهائية
        trust = (
            completion_rate * 0.4 +
            avg_rating * 20 * 0.3 +
            response_score * 0.2 +
            math.log1p(total_contracts) * 5 * 0.1
        )

        trust = min(100, max(0, round(trust, 2)))
        
        # تحديث الحقول
        user_profile.trust_score = trust
        user_profile.completion_rate = completion_rate / 100.0
        user_profile.contracts_count = total_contracts
        user_profile.avg_rating = avg_rating
        
        # منع الاستدعاء التكراري
        if not getattr(user_profile, '_updating', False):
            user_profile._updating = True
            user_profile.save()
            user_profile.update_reputation()
        
        return trust
        
    except Exception as e:
        logger.error(f"Error calculating trust score for user {user_profile.user.username}: {e}")
        user_profile.trust_score = 50.0
        user_profile.save()
        return 50.0

def update_all_trust_scores():
    """نسخة محسنة للأداء"""
    profiles = UserProfile.objects.select_related('user').only(
        'id', 'trust_score', 'completion_rate', 'contracts_count', 
        'avg_rating', 'avg_response_time'
    )
    
    with transaction.atomic():
        for profile in profiles:
            calculate_trust_score(profile)

def generate_user_profile_vector(user_profile):
    """
    يحوّل معلومات المستخدم إلى نص لتحليل TF-IDF.
    """
    try:
        skill_names = [skill.name for skill in user_profile.skills.all()]
        description = getattr(user_profile, 'bio', '') or ""
        trust = f"trust_{getattr(user_profile, 'trust_score', 0)}"
        rating = f"rating_{getattr(user_profile, 'avg_rating', 0)}"
        completion = f"completion_{getattr(user_profile, 'completion_rate', 0)}"

        # دمج المعلومات مع مراعاة الوزن لكل معيار
        weighted_text = (
            f"{' '.join(skill_names) * int(WEIGHTS['skills']*10)} "
            f"{description * int(WEIGHTS['description']*10)} "
            f"{trust * int(WEIGHTS['trust']*10)} "
            f"{rating * int(WEIGHTS['rating']*10)} "
            f"{completion * int(WEIGHTS['completion']*10)}"
        )
        return weighted_text
    except Exception as e:
        logger.error(f"Error generating profile vector: {e}")
        return ""

def recommend_users(target_user, top_n=5):
    """
    توصية بالمستخدمين الأكثر تشابهًا مع وزن لكل معيار.
    """
    try:
        users_profiles = UserProfile.objects.exclude(id=target_user.id)
        if not users_profiles.exists():
            return []

        target_text = generate_user_profile_vector(target_user)
        other_texts = [generate_user_profile_vector(u) for u in users_profiles]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([target_text] + other_texts)
        similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

        ranked_profiles = sorted(zip(users_profiles, similarities), key=lambda x: x[1], reverse=True)
        recommended = [u for u, score in ranked_profiles[:top_n] if score > 0.05]
        return recommended
    except Exception as e:
        logger.error(f"Error recommending users: {e}")
        return []

def recommend_skills(target_user, top_n=5):
    """
    يقترح مهارات جديدة بناءً على المستخدمين المشابهين.
    """
    try:
        similar_profiles = recommend_users(target_user, top_n=5)
        recommended_skills = Skill.objects.none()

        for profile in similar_profiles:
            recommended_skills |= profile.skills.exclude(id__in=target_user.skills.all())

        # إذا لم يكن هناك توصيات كافية، نضيف مهارات من كل المستخدمين
        if recommended_skills.count() < top_n:
            extra_skills = Skill.objects.exclude(id__in=target_user.skills.all())
            recommended_skills |= extra_skills

        return recommended_skills.distinct()[:top_n]
    except Exception as e:
        logger.error(f"Error recommending skills: {e}")
        return Skill.objects.none()

def recommend_contracts(target_user, top_n=5):
    """مصحح - خطأ __in"""
    try:
        similar_profiles = recommend_users(target_user)
        similar_users = [profile.user for profile in similar_profiles if hasattr(profile, 'user')]

        contracts = Contract.objects.filter(
            Q(client__in=similar_users) | Q(freelancer__in=similar_users),  # ✅ __in
            status__in=['active', 'pending']
        ).distinct()[:top_n]
        
        return contracts
    except Exception as e:
        logger.error(f"Error recommending contracts: {e}")
        return []

def get_user_recommendations(user_id):
    """مع تحسين cache"""
    cache_key = f"user_recommendations_{user_id}"
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
        
    try:
        target_user = UserProfile.objects.get(id=user_id)
        
        result = {
            "recommended_users": recommend_users(target_user),
            "recommended_skills": recommend_skills(target_user),
            "recommended_contracts": recommend_contracts(target_user)
        }
        
        # تخزين في cache لمدة 30 دقيقة
        cache.set(cache_key, result, 60 * 30)
        return result
        
    except UserProfile.DoesNotExist:
        return {"error": "User not found"}

# دوال إضافية مساعدة
def update_recommendations_after_contract(contract):
    """تحديث التوصيات بعد إكمال عقد"""
    try:
        if contract.status == 'completed':
            # تحديث الثقة للطرفين
            calculate_trust_score(contract.client.profile)
            calculate_trust_score(contract.freelancer.profile)
            
            # مسح cache للتوصيات
            cache.delete_pattern("user_recommendations_*")
            
            logger.info(f"✅ Recommendations updated after contract {contract.id}")
    except Exception as e:
        logger.error(f"Error updating recommendations after contract: {e}")

def get_skill_based_recommendations(user_profile, top_n=5):
    """توصيات بناءً على المهارات المشتركة"""
    try:
        user_skills = user_profile.skills.all()
        
        # مستخدمون لديهم مهارات مشتركة
        similar_users = UserProfile.objects.filter(
            skills__in=user_skills
        ).exclude(id=user_profile.id).distinct()
        
        # ترتيب حسب عدد المهارات المشتركة
        ranked_users = []
        for profile in similar_users:
            common_skills = profile.skills.filter(id__in=user_skills).count()
            total_skills = profile.skills.count()
            similarity_score = common_skills / max(total_skills, 1)
            ranked_users.append((profile, similarity_score))
        
        ranked_users.sort(key=lambda x: x[1], reverse=True)
        return [user for user, score in ranked_users[:top_n]]
    except Exception as e:
        logger.error(f"Error getting skill-based recommendations: {e}")
        return []

def update_user_reputation(user):
    """تحديث سمعة المستخدم - دالة شاملة"""
    try:
        profile = user.profile
        calculate_trust_score(profile)
        profile.update_reputation()
        return profile.trust_score
    except Exception as e:
        logger.error(f"Error updating user reputation: {e}")
        return 50.0

def get_user_contract_stats(user):
    """
    إحصائيات العقود للمستخدم.
    """
    try:
        contracts_as_client = Contract.objects.filter(client=user)
        contracts_as_freelancer = Contract.objects.filter(freelancer=user)
        
        total_contracts = contracts_as_client.count() + contracts_as_freelancer.count()
        
        completed_as_client = contracts_as_client.filter(status='completed').count()
        completed_as_freelancer = contracts_as_freelancer.filter(status='completed').count()
        total_completed = completed_as_client + completed_as_freelancer
        
        return {
            'total_contracts': total_contracts,
            'completed_contracts': total_completed,
            'completion_rate': (total_completed / total_contracts * 100) if total_contracts > 0 else 0,
            'contracts_as_client': contracts_as_client.count(),
            'contracts_as_freelancer': contracts_as_freelancer.count(),
            'completed_as_client': completed_as_client,
            'completed_as_freelancer': completed_as_freelancer,
        }
    except Exception as e:
        logger.error(f"Error getting user contract stats: {e}")
        return {}