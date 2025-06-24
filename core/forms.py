from django import forms
from .models import Comment

class TestSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', [])
        super(TestSubmissionForm, self).__init__(*args, **kwargs)
        
        for question in questions:
            field_name = f'question_{question.id}'
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=question.answers.all(),
                widget=forms.RadioSelect,
                label=question.text,
                empty_label=None,
                to_field_name='id'
            )
            self.fields[field_name].question = question
class CodeTaskForm(forms.Form):
    code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control code-editor',
            'rows': 15,
            'placeholder': 'Введите ваш код здесь...',
            'spellcheck': 'false'
        }),
        label='',
        required=True
    )

class CTFFlagForm(forms.Form):
    flag = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите флаг в формате FLAG{...}',
            'autocomplete': 'off'
        }),
        label='',
        max_length=100,
        required=True
    )

    def clean_flag(self):
        flag = self.cleaned_data['flag']
        if not (flag.startswith('FLAG{') and flag.endswith('}')):
            raise forms.ValidationError("Флаг должен быть в формате FLAG{...}")
        return flag

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control hacker-textarea',
                'rows': 3,
                'placeholder': 'Ваш комментарий...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
        self.fields['text'].max_length = 500

class TaskResponseForm(forms.Form):
    answer = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control hacker-textarea',
            'rows': 8,
            'placeholder': 'Введите ваш ответ здесь...'
        }),
        label='',
        required=True
    )