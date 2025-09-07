from django.db import models

class Book(models.Model):
     title = models.CharField(max_length=200)
     author = models.CharField(max_length=100)
     published_date = models.DateField()
     isbn_number = models.CharField(max_length=13, unique=True)
     pages = models.IntegerField()
     cover_image = models.URLField(blank=True, null=True)
     language = models.CharField(max_length=30)

     def __str__(self):
         return self.title
     
class LibraryUser(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    membership_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class BorrowRecord(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} borrowed {self.book}"
    


# Create your models here.
