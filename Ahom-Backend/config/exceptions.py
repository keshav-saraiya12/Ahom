from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        data = response.data
        # Normalise into {"detail": "...", "code": "..."}
        if isinstance(data, dict):
            if "detail" not in data:
                first_key = next(iter(data), None)
                if first_key:
                    messages = data[first_key]
                    if isinstance(messages, list):
                        messages = " ".join(str(m) for m in messages)
                    response.data = {
                        "detail": str(messages),
                        "code": first_key,
                    }
            elif "code" not in data:
                code = getattr(exc, "default_code", None) or "error"
                response.data["code"] = code
        elif isinstance(data, list):
            response.data = {
                "detail": " ".join(str(m) for m in data),
                "code": "error",
            }
    return response
