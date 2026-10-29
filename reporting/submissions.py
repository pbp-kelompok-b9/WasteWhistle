from uuid import UUID, uuid4

from django.core import signing


SALT = "reporting.create"


def new_submission_token(user):
    return signing.dumps({"id": str(uuid4()), "user": str(user.pk)}, salt=SALT)


def read_submission_id(token, user):
    try:
        data = signing.loads(token, salt=SALT)
        if data["user"] != str(user.pk):
            raise signing.BadSignature("Submission belongs to another user.")
        return UUID(data["id"])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise signing.BadSignature("Invalid report submission.") from exc
