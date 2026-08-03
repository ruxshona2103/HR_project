from rest_framework import permissions


class IsVacancyOwnerOrReadOnly(permissions.BasePermission):
    """
    - GET, HEAD, OPTIONS: hammaga ruxsat (o'qish, autentifikatsiyasiz ham).
    - POST (Create): faqat autentifikatsiyadan o'tgan va 'organization'
      turidagi foydalanuvchilarga ruxsat.
    - PUT, PATCH, DELETE (Update/Delete): faqat o'z kompaniyasining
      vakansiyasiga egalik qiladigan autentifikatsiyadan o'tgan
      foydalanuvchiga ruxsat.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == 'POST':
            return getattr(request.user, 'user_type', None) == 'organization'

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user_company = getattr(request.user, 'company_profile', None)
        if user_company is None:
            return False

        return obj.company_id == user_company.id