from rest_framework.throttling import SimpleRateThrottle


def throttle_by(rate, scope):
    _rate, _scope = rate, scope

    class InnerThrottle(SimpleRateThrottle):
        rate = _rate
        scope = _scope

        def get_cache_key(self, request, view):
            return self.cache_format % {
                'scope': self.scope,
                'ident': self.get_ident(request)
            }

    return InnerThrottle
