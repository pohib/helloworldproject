from django import forms
from .models import Question, Answer

class TestSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', [])
        super(TestSubmissionForm, self).__init__(*args, **kwargs)
        
        for question in questions:
            answers = question.answers.all()
            choices = [(answer.id, answer.text) for answer in answers]
            
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect(attrs={
                    'class': 'form-check-input'
                }),
                required=True
            )

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

class LectureCommentForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Оставьте ваш комментарий или вопрос...'
        }),
        label='',
        max_length=500,
        required=True
    )