from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


_BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "169.254.169.254",
    "metadata.google.internal",
}


def _is_disallowed_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_external_resume_url(
    url: str,
    *,
    allow_http: bool = False,
    validate_dns: bool = True,
    max_length: int = 2048,
) -> str:
    candidate = (url or "").strip()
    if not candidate:
        raise ValueError("Resume source URL is empty.")
    if len(candidate) > max_length:
        raise ValueError("Resume source URL is too long.")

    parsed = urlparse(candidate)
    allowed_schemes = {"https", "http"} if allow_http else {"https"}
    if parsed.scheme.lower() not in allowed_schemes:
        allowed_label = "https/http" if allow_http else "https"
        raise ValueError(f"Only {allowed_label} resume URLs are allowed.")

    if parsed.username or parsed.password:
        raise ValueError("Resume source URL must not include credentials.")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise ValueError("Resume source URL host is required.")
    if host in _BLOCKED_HOSTS:
        raise ValueError("Resume source URL points to a disallowed host.")

    try:
        host_ip = ipaddress.ip_address(host)
    except ValueError:
        host_ip = None

    if host_ip is not None and _is_disallowed_ip(str(host_ip)):
        raise ValueError("Resume source URL resolves to a non-public IP.")

    if validate_dns:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("Unable to resolve resume source URL host.") from exc

        for info in infos:
            sockaddr = info[4]
            resolved_ip = sockaddr[0]
            if _is_disallowed_ip(resolved_ip):
                raise ValueError("Resume source URL resolves to a non-public IP.")

    return candidate