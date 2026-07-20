from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Resume, Aloqa, Konikma, Til,
    IshTajribasi, Talim, Sertifikat,
    Maqola, Qiziqish, Yutuq
)

class AloqaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aloqa
        exclude = ['resume']

class KonikmaSerializer(serializers.ModelSerializer):
    daraja_nomi = serializers.CharField(
        source='get_daraja_display',read_only=True
    )

    class Meta:
        model =  Konikma
        exclude = ['resume']


class TilSerializer(serializers.ModelSerializer):
    daraja_nomi = serializers.CharField(
        source='get_daraja_display',read_only=True

    )
    class Meta:
        model = Til
        exclude = ['resume']

class IshTajribasiSerializer(serializers.ModelSerializer):
    ish_turi_nomi = serializers.CharField(
        source='get_ish_turi_dispay',read_only=True
    )

    class Meta:
        model = IshTajribasi
        exclude = ['resume']

    def validate(self,data):
        if not data.get('hozir_ishlayapman') and not data.get('tugash_sanasi'):
            raise serializers.ValidationError(
                "Tugash sanasini kiriting yoki 'Hozir shu yerda ishlayapman' ni belgilang.  "

            )
        return data

class TalimSerializer(serializers.ModelSerializer):
    daraja_nomi = serializers.CharField(
        source='get_daraja_display', read_only=True
    )

    class Meta:
        model = Talim
        exclude = ['resume']

    def validate(self, data):
        if not data.get('hozir_oqiyapman') and not data.get('tugash_yili'):
            raise serializers.ValidationError(
                "Tugash yilini kiriting yoki 'Hozir o'qiyapman' ni belgilang."
            )
        return data



class SertifikatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sertifikat
        exclude = ['resume']

    def validate(self, data):
        if not data.get('muddatsiz') and not data.get('amal_qilish_muddati'):
            raise serializers.ValidationError(
                "Amal qilish muddatini kiriting yoki 'Muddatsiz' ni belgilang."
            )
        return data



class MaqolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maqola
        exclude = ['resume']



class QiziqishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qiziqish
        exclude = ['resume']



class YutuqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Yutuq
        exclude = ['resume']



class ResumeSerializer(serializers.ModelSerializer):
    mutaxassislik_nomi = serializers.CharField(
        source='get_mutaxasislik_display', read_only=True
    )
    aloqa = AloqaSerializer(read_only=True)
    konikmalar = KonikmaSerializer(many=True, read_only=True)
    tillar = TilSerializer(many=True, read_only=True)
    ish_tajribalari = IshTajribasiSerializer(many=True, read_only=True)
    talim_malumotlari = TalimSerializer(many=True, read_only=True)
    sertifikatlar = SertifikatSerializer(many=True, read_only=True)
    maqolalar = MaqolaSerializer(many=True, read_only=True)
    qiziqishlar = QiziqishSerializer(many=True, read_only=True)
    yutuqlar = YutuqSerializer(many=True, read_only=True)

    foydalanuvchi_ismi = serializers.SerializerMethodField()

    def get_foydalanuvchi_ismi(self, obj):
        return obj.foydalanuvchi.get_full_name()

    class Meta:
        model = Resume
        fields = [
            'id', 'foydalanuvchi_ismi',
            'mutaxasislik',
            'mutaxassislik_nomi',
            'lavozim', 'men_haqimda',
            'profil_rasm', 'yaratilgan', 'yangilangan',
            'aloqa', 'konikmalar', 'tillar', 'ish_tajribalari',
            'talim_malumotlari', 'sertifikatlar', 'maqolalar',
            'qiziqishlar', 'yutuqlar','resume_fayli'
        ]


class RoyxatdanOtishSerializer(serializers.ModelSerializer):
    parol = serializers.CharField(write_only=True, min_length=8)
    parol_tasdiqlash = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'parol', 'parol_tasdiqlash']

    def validate(self, data):
        if data['parol'] != data['parol_tasdiqlash']:
            raise serializers.ValidationError("Parollar mos kelmadi.")
        return data

    def create(self, validated_data):
        validated_data.pop('parol_tasdiqlash')
        parol = validated_data.pop('parol')
        user = User(**validated_data)
        user.set_password(parol)
        user.save()
        return user

