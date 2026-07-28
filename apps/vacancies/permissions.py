from rest_framework import permissions


class IsVacancyOwnerOrReadOnly(permissions.BasePermission):
    """
    - GET, HEAD, OPTIONS: Hammaga ruxsat (o'qish).
    - POST (Create): Faqat 'organization' turidagi foydalanuvchilarga ruxsat.
    - PUT, PATCH, DELETE (Update/Delete): Faqat o'z kompaniyasining vakansiyasiga ruxsat.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method == 'POST':
            return (
                    request.user
                    and request.user.is_authenticated
                    and getattr(request.user, 'user_type', None) == 'organization'
            )

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user_company = getattr(request.user, 'company_profile', None)
        if user_company and hasattr(obj, 'company'):
            return obj.company == user_company

        return False