from django.db import models


class SGUser(models.Model):
    username = models.CharField(max_length=191)

    class Meta:
        db_table = 'auth_user'
        managed = False


class SGProfile(models.Model):
    user = models.OneToOneField(SGUser, related_name="profile")
    name = models.CharField(max_length=20)
    sid = models.CharField(max_length=20, blank=True)
    github_username = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "accounts_profile"
        managed = False


class SGCourse(models.Model):
    SEMESTER = (
        (0, "1학기"),
        (1, "여름 계절학기"),
        (2, "2학기"),
        (3, "겨울 계절학기")
    )
    professor = models.ForeignKey(SGUser,
                                  related_name="courses",
                                  limit_choices_to={'sgprofile__is_prof': True},
                                  on_delete=models.CASCADE)
    students = models.ManyToManyField(SGUser,
                                      through="SGRepository",
                                      through_fields=("course", "student"))
    title = models.CharField(max_length=100)
    content = models.TextField(max_length=5000)
    year = models.IntegerField()
    semester = models.IntegerField(choices=SEMESTER)
    attachments = models.FileField(blank=True,
                                   upload_to="uploads/course/%Y/%m/%d/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_course"
        managed = False


class SGRepository(models.Model):
    student = models.ForeignKey(SGUser,
                                limit_choices_to={'sgprofile__is_prof': False},
                                on_delete=models.CASCADE)
    course = models.ForeignKey(SGCourse,
                               on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    url = models.URLField()
    key = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_repository"
        managed = False


class SGAssignment(models.Model):
    course = models.ForeignKey(SGCourse, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField(max_length=5000)
    attachments = models.FileField(blank=True,
                                   upload_to="uploads/assignment/%Y/%m/%d/")
    deadline = models.DateTimeField()
    is_test = models.BooleanField(default=False)
    test_file_name = models.CharField(max_length=100)
    test_input = models.TextField(max_length=5000, blank=True)
    test_output = models.TextField(max_length=5000, blank=True)
    test_time = models.FloatField(default=2)
    test_langids = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_assignment"
        managed = False


def update_filename(instance, filename):
    import os
    import uuid
    random_id = str(uuid.uuid4())
    path = "uploads/history/%s/" % (random_id,)
    filename = str(instance.student.profile.sid) + "-" + filename
    return os.path.join(path, filename)


class SGSubmission(models.Model):
    LANG_CHOICES = (
        (0, "Python"),
        (1, "Ruby"),
        (2, "Clojure"),
        (3, "PHP"),
        (4, "Javascript"),
        (5, "Scala"),
        (6, "Go"),
        (7, "C"),
        (8, "Java"),
        (9, "VB.NET"),
        (10, "C#"),
        (11, "Bash"),
        (12, "Objective-C"),
        (13, "MySQL"),
        (14, "Perl"),
        (15, "C++"),
    )
    student = models.ForeignKey(SGUser,
                                limit_choices_to={'sgprofile__is_prof': False},
                                on_delete=models.CASCADE)
    assignment = models.ForeignKey(SGAssignment,
                                   on_delete=models.CASCADE)
    is_passed = models.BooleanField(default=False)
    is_working = models.BooleanField(default=True)
    is_last_submission = models.BooleanField(default=True)
    has_error = models.BooleanField(default=False)
    raw_code = models.FileField(upload_to=update_filename,
                                blank=True)
    code = models.TextField(max_length=5000, blank=True)
    langid = models.IntegerField(choices=LANG_CHOICES, null=True, blank=True)
    errors = models.TextField(max_length=5000, blank=True)
    output = models.TextField(max_length=5000, blank=True)
    time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_submission"
        managed = False
