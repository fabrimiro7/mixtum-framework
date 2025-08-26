# Production overlay (harden what you need)
DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # abilita se dietro proxy con https
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
