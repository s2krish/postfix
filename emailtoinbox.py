mport sys
from email.parser import FeedParser

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from smarty.models import Action
from smarty.email_utils import get_best_part, make_text, decode_header

class Command(BaseCommand):
    args = '<username>'
    help = 'Accepts an email message and writes it into the inbox for the specified user'

    def add_arguments(self, parser):
        parser.add_argument('--username', nargs='?', required=True)

    def handle(self, *args, **options):
        username = options.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("The specified user does not exist")

        parser = FeedParser()
        message_chunk = sys.stdin.read(10000)
        while message_chunk:
            parser.feed(message_chunk)
            message_chunk = sys.stdin.read(10000)
        message = parser.close()

        try:
            message_part = get_best_part(message)
            subject = decode_header(message['Subject'])
            body = make_text(message_part)

            if int(options['verbosity']) > 1:
                print(body)

            action = Action(
                user=user,
                title=subject,
                notes=body
            )
            action.insert_in_inbox()
            action.save()

        except RuntimeError:
            # Recursion depth exceeded parsing message; throw the message away
            pass
