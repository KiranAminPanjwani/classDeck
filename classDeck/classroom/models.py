from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.utils.text import slugify
from django.urls import reverse
from datetime import datetime
import calendar


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)


class Subject(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)


class Quiz(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    duration = models.TimeField(null=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Assignment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignements')
    file = models.FileField(upload_to="assignments/", null=True)
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    note = models.TextField(null=True, default='No Note')
    last_date = models.DateTimeField(auto_now_add=False, null=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz')
    assignments = models.ManyToManyField(Assignment, related_name='assigned_students')
    interests = models.ManyToManyField(Subject, related_name='interested_students')

    def get_unanswered_questions(self, quiz):
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('text')
        return questions

    def __str__(self):
        return self.user.username


class TakenQuiz(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+', null=True)


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    file = models.FileField(upload_to="submissions/", null=True)
    score = models.IntegerField(null=True)
    date = models.DateTimeField(auto_now_add=True, null=True)
    late_submission = models.BooleanField(default=False)
    remarks = models.TextField(null=True, default='No Remarks')


class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    admin = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True, unique=True)
    description = models.TextField(blank=True, default='')
    members = models.ManyToManyField(User, through="ChannelMember")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("channels:single", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["name"]


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, related_name="memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user_channels', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        unique_together = ("channel", "user")


def get_current_year():
    current_Year = datetime.now().year
    return current_Year

class MonthlySchedule(models.Model):
    month = models.IntegerField(unique=True, null=False)
    year = models.IntegerField(null=False,default=get_current_year)
    days = models.IntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.month}-{self.year}-{self.user.username}'

class DailySchedule(models.Model):
    month = models.ForeignKey(MonthlySchedule, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20, null=False)
    day = models.IntegerField(null=False)
    no_notes = models.IntegerField(null=True, default=0)
    imp = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.month}-{self.month.year}-{self.day}-{self.day_of_week}'

class Note(models.Model):
    day = models.ForeignKey(DailySchedule, on_delete=models.CASCADE)
    alert = models.BooleanField(default=False)
    note = models.CharField(max_length=200, null=True)
    at = models.TimeField(null=True)

    def __str__(self):
        return f'{self.month}-{self.day}-{self.day_of_week}-{self.id}'