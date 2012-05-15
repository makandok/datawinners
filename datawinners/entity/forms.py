from django import forms
from django.contrib.auth.models import User
from django.forms import HiddenInput
from django.forms.fields import RegexField, CharField, FileField, MultipleChoiceField, EmailField
from django.forms.widgets import CheckboxSelectMultiple, TextInput
from django.utils.translation import ugettext_lazy as _
from django.forms.forms import Form
from mangrove.utils.types import is_empty
from registration.forms import RegistrationFormUniqueEmail
from datawinners.entity.fields import PhoneNumberField
import re

class EntityTypeForm(Form):
    error_css_class = 'error'
    required_css_class = 'required'

    entity_type_regex = RegexField(regex="^\s*([A-Za-z\d\s]+[A-Za-z\d]+)\s*$", max_length=20,
        error_message=_("Only letters and numbers are valid and you must provide more than just whitespaces."),
        required=True,
        label=_("New Subject(eg clinic, waterpoint etc)"))


class SubjectForm(Form):
    required_css_class = 'required'
    error_css_class = 'error'

    type = CharField(max_length=30, required=True, label=_("Type"))
    name = CharField(max_length=30, required=True, label=_("Name"))
    uniqueID = CharField(max_length=100, required=True, label=_("Unique Identification Number (ID)"))
    location = CharField(max_length=30, required=True, label=_("Location"))
    description = CharField(max_length=30, required=False, label=_("Description"))
    mobileNumber = CharField(max_length=30, required=False, label=_("Mobile Number"))


class ReporterRegistrationForm(Form):
    required_css_class = 'required'

    name = RegexField(regex="[^0-9.,\s@#$%&*~]*", max_length=20,
        error_message=_("Please enter a valid value containing only letters a-z or A-Z or symbols '`- "),
        label=_("Name"))
    telephone_number = PhoneNumberField(required=True, label=_("Mobile Number"))
    geo_code = CharField(max_length=30, required=False, label=_("GPS: Enter Lat Long"))
    location = CharField(max_length=100, required=False, label=_("Enter location"))
    project_id = CharField(required=False, widget=HiddenInput())
    DEVICE_CHOICES = (('sms', 'SMS'), ('web', _('WEB + SmartPhone')))
    devices = MultipleChoiceField(label=_('Device'), widget=CheckboxSelectMultiple, choices=DEVICE_CHOICES,
        initial=['sms'], required=False)
    email = EmailField(required=False, widget=TextInput(attrs=dict({'class': 'required'},
        maxlength=75)),
        label=_("Email address"),
        error_messages={
            'invalid': _('Enter a valid email address. Example:name@organization.com')})

    def __init__(self, *args, **kwargs):
        super(ReporterRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['watermark'] = _("Enter Data Sender's name")
        self.fields['telephone_number'].widget.attrs['watermark'] = _("Enter Data Sender's number")
        self.fields['location'].widget.attrs['watermark'] = _("Enter region, district or commune")
        self.fields['geo_code'].widget.attrs['watermark'] = _("Enter lat and long eg: 19.3,42.37")

    def _is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False


    def _geo_code_format_validations(self, lat_long, msg):
        if len(lat_long) != 2:
            self._errors['geo_code'] = self.error_class([msg])
        else:
            try:
                if not (-90 < float(lat_long[0]) < 90 and -180 < float(lat_long[1]) < 180):
                    self._errors['geo_code'] = self.error_class([msg])
            except Exception:
                self._errors['geo_code'] = self.error_class([msg])

    def _geo_code_validations(self, b):
        msg = _(
            "Incorrect GPS format. The GPS coordinates must be in the following format: xx.xxxx,yy.yyyy. Example -18.8665,47.5315")
        geo_code_string = b.strip()
        geo_code_string = (' ').join(geo_code_string.split())
        if not is_empty(geo_code_string):
            lat_long = re.split("[ ,]", geo_code_string)
            self._geo_code_format_validations(lat_long, msg)
            self.cleaned_data['geo_code'] = geo_code_string

    def clean(self):
        self.convert_email_to_lowercase()
        location = self.cleaned_data.get("location")
        geo_code = self.cleaned_data.get("geo_code")
        if not (bool(location) or bool(geo_code)):
            msg = _("Please fill out at least one location field correctly.")
            self._errors['location'] = self.error_class([msg])
            self._errors['geo_code'] = self.error_class([msg])
        if bool(geo_code):
            self._geo_code_validations(geo_code)
        return self.cleaned_data

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        devices = self.cleaned_data.get('devices')
        if not devices.__contains__('web'):
            return

        email = self.cleaned_data.get('email')
        if is_empty(email):
            msg = _('This field is required.')
            self._errors['email'] = self.error_class([msg])
            return

        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']

    def convert_email_to_lowercase(self):
        email = self.cleaned_data.get('email')
        if email is not None:
            self.cleaned_data['email'] = email.lower()



class SubjectUploadForm(Form):
    error_css_class = 'error'
    required_css_class = 'required'
    file = FileField(label='Import Subjects')
