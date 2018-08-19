def resolver_context_processor(request):
    return {
        'app_name': request.resolver_match.app_name,
        'url_name': request.resolver_match.url_name,
    }
