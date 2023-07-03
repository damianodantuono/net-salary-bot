import functions_framework

@functions_framework.http
def get_net_salary(request):
    request_json = request.get_json(silent=True)
    return request_json
