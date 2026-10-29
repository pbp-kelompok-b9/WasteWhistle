def is_petugas(user):
    return user.is_authenticated and user.is_staff