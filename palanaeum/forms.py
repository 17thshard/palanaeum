# coding=utf-8
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import EmailField, ModelForm, Form, PasswordInput, CharField, \
    DateField, ChoiceField, SelectMultiple, \
    IntegerField, BooleanField, ImageField
from django.forms.widgets import DateInput
from django.utils.translation import ugettext_lazy as _

from .models import UserSettings, Event, Entry, RelatedSite, UsersEntryCollection, ImageSource


class UserCreationFormWithEmail(UserCreationForm):
    """
    We add an email field to be filled while registering a new account.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    email = EmailField(label=_('E-mail address'))

    def __init__(self, *args, **kwargs):
        super(UserCreationFormWithEmail, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('User with this e-mail address already exists.'))
        return email

    def save(self, commit=True):
        user = super(UserCreationFormWithEmail, self).save(commit)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user


class EmailChangeForm(Form):
    """
    Display a field to insert an e-mail address and password for verification.
    """
    email = EmailField(label=_('E-mail address'))
    password = CharField(label=_('Password'), widget=PasswordInput(), required=False,
                         help_text=_('Password is required to change your e-mail address.'))

    def __init__(self, *args, user=None, **kwargs):
        super(EmailChangeForm, self).__init__(*args, **kwargs)
        assert(isinstance(user, User))
        self.user = user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError(_('User with this e-mail address already exists.'))
        return email

    def clean_password(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email != self.user.email and not self.user.check_password(password):
            raise ValidationError(_('Invalid password.'))
        return password

    def save(self, commit=True):
        self.user.email = self.cleaned_data.get('email')
        if commit:
            self.user.save()
        return self.user


class SortForm(Form):
    """
    Display a simple 2 select form showing what available sort options are there.
    """
    sort_by = ChoiceField(choices=())
    sort_ord = ChoiceField(choices=(('', _('ascending')), ('-', _('descending'))), required=False)

    def __init__(self, field_choices, *args, **kwargs):
        super(SortForm, self).__init__(*args, **kwargs)
        self.fields['sort_by'].choices = field_choices


class UserSettingsForm(ModelForm):
    """
    A form for changing user settings.
    """
    class Meta:
        model = UserSettings
        fields = ('timezone', 'page_length', 'website')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['page_length'] = IntegerField(max_value=100, min_value=10)


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ('name', 'date', 'review_state', 'location', 'tour', 'bookstore', 'meta')

    class Media:
        js = ('palanaeum/js/third_party/modernizr.js', 'palanaeum/js/modernize_forms.js')

    date = DateField(widget=DateInput(attrs={'type': 'date'}))
    # Selected tags will be added by JavaScript
    tags = CharField(label=_('Tags'), required=False, widget=SelectMultiple(attrs={'class': 'tag-selector',
                                                                                   'data-tags': "true"}))
    update_entry_dates = BooleanField(label=_('Update entry dates'), required=False,
                                      help_text=_("Will modify the dates of "
                                                  "entries which didn't have different date set."))

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.original_date = self.instance.date

    def save(self, commit=True):
        if self.cleaned_data['update_entry_dates']:
            Entry.objects.filter(event=self.instance, date=self.original_date).update(date=self.cleaned_data['date'])
        super(EventForm, self).save()
        tags = self.cleaned_data['tags'][1:-1]  # No [] at ends
        tags = tags.split(',')  # Separate tags
        tags = [str(tag).strip("'\"") for tag in tags]
        self.instance.update_tags(", ".join(tags))
        return self.instance


class ImageRenameForm(ModelForm):
    class Meta:
        model = ImageSource
        fields = ('name',)


class RelatedSiteForm(ModelForm):
    class Meta:
        model = RelatedSite
        fields = ('name', 'url', 'image', 'order')


class UsersEntryCollectionForm(ModelForm):
    class Meta:
        model = UsersEntryCollection
        fields = ('name', 'description', 'public')


class GeneralConfig(Form):
    page_title = CharField(max_length=100, label=_('Page name'))
    index_hello = CharField(max_length=1000, label=_('Index welcome text'),
                            help_text=_('This text will be displayed on the home page.'))
    default_page_length = IntegerField(max_value=100, min_value=10, label=_('Default page length'),
                                       help_text=_('This value affects all paginated sections.'))
    google_analytics = CharField(max_length=200, label=_('Google analytics ID'), required=False)
    approval_message = CharField(max_length=100, label=_('Label of approval'), initial='Reviewed',
                                 help_text=_('This text will be displayed for approved events.'))
    review_pending_explanation = CharField(max_length=250, label=_('Pending review explanation'), required=False)
    review_reviewed_explanation = CharField(max_length=250, label=_('Reviewed review explanation'), required=False)
    logo_file = ImageField(allow_empty_file=True, required=False, label=_('Your logo'),
                           help_text=_('Your logo should have size ratio similar to 370x150px.'))


class FaviconsConfig(Form):
    favicon16 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 16px'))
    favicon32 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 32px'))
    favicon96 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 96px'))
    favicon120 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 120px'))
    favicon152 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 152px'))
    favicon167 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 167px'))
    favicon180 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 180px'))
    favicon200 = ImageField(allow_empty_file=True, required=False, label=_('Favicon 200px'))


class AudioConfig(Form):
    audio_keep_original_file = BooleanField(required=False, label=_('Keep original files'),
                                            help_text=_("Should original files be kept on the server after they're "
                                                        "transcoded."))
    audio_quality = ChoiceField(choices=[('256k', '256 kb/s'), ('128k', '128 kb/s'),
                                         ('96k', '96 kb/s'), ('64k', '64 kb/s'),
                                         ('32k', '32 kb/s'), ('16k', '16 kb/s')],
                                label=_('Transcoded audio quality'),
                                help_text=_('This settings affects both audio sources and snippets.'))
    audio_staff_size_limit = IntegerField(max_value=2000, min_value=10, label=_('Staff size limit'),
                                          help_text=_('In megabytes'))
    audio_user_size_limit = IntegerField(max_value=2000, min_value=10,
                                         label=_('User size limit'),
                                         help_text=_('In megabytes'))


class ImageConfig(Form):
    image_size_limit = IntegerField(min_value=1, max_value=20,
                                    label=_('Image size limit'),
                                    help_text=_('In megabytes'))


class CloudConfig(Form):
    cloud_backend = ChoiceField(choices=[
        ('', 'None'), ('b2', 'Backblaze B2')
    ], label=_('Cloud backend type'), required=False)
    cloud_login = CharField(max_length=100, label='App ID', required=False)
    cloud_passwd = CharField(max_length=256, label='App KEY', required=False)
    cloud_b2_bucket_id = CharField(max_length=24, label=_('B2 bucket ID'), required=False,
                                   help_text=_('Set this only if you use B2.'))