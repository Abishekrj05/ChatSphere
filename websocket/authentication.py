from channels.auth import AuthMiddlewareStack

def SessionAuthMiddlewareStack(inner):
    return AuthMiddlewareStack(inner)
