from rest_framework import permissions


class IsProfileOwner(permissions.BasePermission):
    """
    Faqat profil egasiga object darajasidagi (obyekt bo'yicha) ruxsat beradi.

    Diqqat: `UserProfileViewSet.get_queryset()` allaqachon boshqa
    foydalanuvchilarning profillarini natijalardan chetlab o'tadi (shu
    sababli ular uchun aslida 404 qaytadi). Bu permission klassi ikkinchi
    himoya qatlami (defense in depth) sifatida qo'shilgan — kelajakda
    kimdir get_queryset()ni o'zgartirib, filtrni unutib qo'ysa ham,
    IDOR qayta ochilib qolmaydi.
    """

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.user_id == request.user.id
        )