from django import forms
from django.utils.translation import gettext_lazy as _
from . import models

class RentalForm(forms.ModelForm):
    class Meta:
        model = models.Reservation
        fields = ['last_name', 'first_name', 'last_name_kana', 'last_name_kana', 'zip_code1', 'zip_code2', 'prefecture', 'city', 'address', 'email', 'gender', 'age_range']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for fieldname in ['address_name', 'address_name_kana', 'zip_code', 'prefecture', 'city', 'address', 'email']:
            self.fields[fieldname].required = True
        for fieldname in ['address_name', 'address_name_kana', 'zip_code', 'city', 'address', 'email']:
            self.fields[fieldname].widget.attrs['class'] = 'in1'
        self.fields['email'].widget.attrs['placeholder'] = ' '
