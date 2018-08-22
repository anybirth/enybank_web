from django import forms
from django.utils.translation import gettext_lazy as _
from . import models

class RentalForm(forms.ModelForm):
    class Meta:
        model = models.Reservation
        fields = ['last_name', 'first_name', 'last_name_kana', 'first_name_kana', 'zip_code1', 'zip_code2', 'prefecture', 'city', 'address', 'email', 'gender', 'age_range']
        widgets = {
            'gender': forms.RadioSelect(),
            'age_range': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs['placeholder'] = ' '
        self.fields['prefecture'].empty_label = '都道府県を選択してください'
        self.fields['zip_code1'].widget.attrs['pattern'] = '\d{3}'
        self.fields['zip_code2'].widget.attrs['pattern'] = '\d{4}'

        for fieldname in ['last_name', 'first_name', 'last_name_kana', 'first_name_kana', 'zip_code1', 'zip_code2', 'prefecture', 'city', 'address', 'email']:
            self.fields[fieldname].required = True
        for fieldname in ['last_name', 'first_name', 'last_name_kana', 'first_name_kana', 'zip_code1', 'zip_code2', 'city', 'address', 'email']:
            self.fields[fieldname].widget.attrs['class'] = 'in1'
