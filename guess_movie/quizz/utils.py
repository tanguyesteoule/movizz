from django.core import signing


def sign_img_path(path):
    return signing.dumps(str(path), salt='screenshot')
