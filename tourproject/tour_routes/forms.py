from django import forms
from models import TourRoute

class TourRouteForm(forms.ModelForm):
    class Meta:
        model = TourRoute
        fields = ['name', 'description', 'length_km', 'difficulty']

    def clean_length_km(self):
        length = self.cleaned_data.get('length_km')
        if length <= 0:
            raise forms.ValidationError("Длина маршрута должна быть больше 0.")
        return length
