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
    github_token = models.CharField(max_length=100, blank=True)

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
                                  limit_choices_to={'profile__is_prof': True},
                                  on_delete=models.CASCADE)
    students = models.ManyToManyField(SGUser,
                                      through="Repository",
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
                                limit_choices_to={'profile__is_prof': False},
                                on_delete=models.CASCADE)
    course = models.ForeignKey(SGCourse,
                               on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    url = models.URLField()
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portal_assignment"
        managed = False