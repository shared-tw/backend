from django.http import JsonResponse
from ninja.errors import HttpError


class Status403Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, HttpError) and exception.status_code == 403:
            return JsonResponse(dict(message=str(exception)), status=403)
        return None
