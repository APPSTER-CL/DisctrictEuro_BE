import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from core.app_settings import SITE_NAME
from district_euro import settings as de_settings

logger = logging.getLogger(__name__)


def get_admin_email():
    return 'joaquin@asap.uy'


def send_mail_join_request(join_request):
    email_context = {'join_request': join_request}
    email_content = render_to_string('email/join_request_email.txt', email_context)
    html_content = render_to_string('email/join_request_email.html', email_context)

    admin_email = get_admin_email()

    email_subject = "[%s] New Join Request" % SITE_NAME
    try:
        send_mail(email_subject, email_content, de_settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=False,
                  html_message=html_content)
        logger.info('Join request #%d email sent to %s', join_request.id, admin_email)
    except Exception as e:
        logger.critical('Sending join request (#%d) email notification error: %s', join_request.id, e)
