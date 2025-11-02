from rest_framework.throttling import AnonRateThrottle
from django.utils import timezone
from accounts.models import BannedIP
from django.conf import settings
from datetime import timedelta


class EscalatingAnonThrottle(AnonRateThrottle):
    scope = "anon"

    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        if not allowed:  # request was throttled
            self.handle_ban(request)
        return allowed

    def handle_ban(self, request):
        ip = self.get_ident(request)
        ladder = getattr(settings, "IPBAN_BAN_LADDER", [15, 60, 24*60])
        perm_after = getattr(settings, "IPBAN_PERMANENT_AFTER", 4)

        ban, _ = BannedIP.objects.get_or_create(ip_address=ip)
        ban.ban_count += 1

        if ban.ban_count >= perm_after:
            ban.banned_until = timezone.now() + timedelta(days=365*10)
            ban.reason = "permanent_after_repeats"
        else:
            idx = min(ban.ban_count - 1, len(ladder)-1)
            minutes = ladder[idx]
            ban.banned_until = timezone.now() + timedelta(minutes=minutes)

        ban.save()

        if getattr(settings, "IPBAN_USE_CACHE", False):
            from django.core.cache import cache
            key = f"bannedip:{ip}"
            timeout = (ban.banned_until - timezone.now()).total_seconds()
            cache.set(key, {"banned_until": ban.banned_until.isoformat(),
                            "ban_count": ban.ban_count},
                      timeout=int(timeout))
