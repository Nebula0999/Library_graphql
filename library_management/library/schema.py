import graphene
from graphene_django import DjangoObjectType
from .models import Book, LibraryUser, BorrowRecord
from graphene_django.filter import DjangoFilterConnectionField
import re
from graphql import GraphQLError
from django.db.models import Q
import datetime


class BookType(DjangoObjectType):
    class Meta:
        model = Book
        filter_fields = {
            'title': ['exact', 'icontains', 'istartswith'],
            'author': ['exact', 'icontains', 'istartswith'],
            'published_date': ['exact', 'lt', 'gt'],
            'isbn_number': ['exact'],
            'language': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)

class LibraryUserType(DjangoObjectType):
    class Meta:
        model = LibraryUser
        filter_fields = {
            'first_name': ['exact', 'icontains', 'istartswith'],
            'last_name': ['exact', 'icontains', 'istartswith'],
            'email': ['exact', 'icontains'],
            'membership_date': ['exact', 'lt', 'gt'],
        }
        interfaces = (graphene.relay.Node,)

class BorrowRecordType(DjangoObjectType):
    class Meta:
        model = BorrowRecord
        filter_fields = {
            'user__first_name': ['exact', 'icontains', 'istartswith'],
            'user__last_name': ['exact', 'icontains', 'istartswith'],
            'book__title': ['exact', 'icontains', 'istartswith'],
            'borrow_date': ['exact', 'lt', 'gt'],
            'return_date': ['exact', 'lt', 'gt'],
        }
        interfaces = (graphene.relay.Node,)

class Query(graphene.ObjectType):
    book = graphene.relay.Node.Field(BookType)
    all_books = DjangoFilterConnectionField(BookType)

    library_user = graphene.relay.Node.Field(LibraryUserType)
    all_library_users = DjangoFilterConnectionField(LibraryUserType)

    borrow_record = graphene.relay.Node.Field(BorrowRecordType)
    all_borrow_records = DjangoFilterConnectionField(BorrowRecordType)

    search_books = graphene.List(BookType, query=graphene.String(required=True))

    def resolve_search_books(self, info, query):
        if not query:
            return Book.objects.none()
        
        # Sanitize input to prevent injection attacks
        sanitized_query = re.sub(r'[^a-zA-Z0-9\s]', '', query)
        if not sanitized_query:
            return Book.objects.none()

        return Book.objects.filter(
            Q(title__icontains=sanitized_query) |
            Q(author__icontains=sanitized_query) |
            Q(isbn_number__icontains=sanitized_query) |
            Q(language__icontains=sanitized_query)
        ).distinct()
    def resolve_all_books(self, info, **kwargs):
        return Book.objects.all()
    def resolve_all_library_users(self, info, **kwargs):
        return LibraryUser.objects.all()
    def resolve_all_borrow_records(self, info, **kwargs):
        return BorrowRecord.objects.all()
    
class Mutation(graphene.ObjectType):
    # mutation fields are attached below
    create_book = None
    
class CreateBook(graphene.Mutation):
    """Create a new Book record.

    published_date must be an ISO date string: YYYY-MM-DD.
    isbn_number must be 10 or 13 digits.
    """
    class Arguments:
        title = graphene.String(required=True)
        author = graphene.String(required=True)
        published_date = graphene.String(required=True)
        isbn_number = graphene.String(required=True)
        pages = graphene.Int(required=True)
        cover_image = graphene.String()
        language = graphene.String(required=True)

    book = graphene.Field(BookType)
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, author, published_date, isbn_number, pages, language, cover_image=None):
        errors = []

        # Validate ISBN (only digits, 10 or 13)
        if not re.match(r'^\d{10}(?:\d{3})?$', isbn_number):
            errors.append('ISBN must be 10 or 13 digits.')

        # Validate published_date
        try:
            pub_date = datetime.date.fromisoformat(published_date)
        except Exception:
            errors.append('published_date must be in YYYY-MM-DD format.')

        if errors:
            return CreateBook(book=None, ok=False, errors=errors)

        # Check uniqueness
        if Book.objects.filter(isbn_number=isbn_number).exists():
            return CreateBook(book=None, ok=False, errors=['Book with this ISBN already exists.'])

        # Create the book
        book = Book.objects.create(
            title=title,
            author=author,
            published_date=pub_date,
            isbn_number=isbn_number,
            pages=pages,
            cover_image=cover_image,
            language=language,
        )

        return CreateBook(book=book, ok=True, errors=[])


class Mutation(graphene.ObjectType):
    create_book = CreateBook.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)