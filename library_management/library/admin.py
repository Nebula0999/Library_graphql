from django.contrib import admin
from .models import Book, LibraryUser, BorrowRecord

admin.site.register(Book)
admin.site.register(LibraryUser)
admin.site.register(BorrowRecord)
# Register your models here.
