# Hermes CF Bypass

From GitHub research (June 2026):

- **Stars**: ★6
- **Repository**: Created specifically for Hermes Agent ecosystem
- **Technique**: Uses `curl_cffi` to monkey-patch `httpx` library — replaces httpx's transport with curl_cffi's impersonating transport
- **Effect**: Any code using httpx (requests' underlying library) transparently gets Chrome TLS fingerprints
- **Limitation**: Same as curl_cffi — won't solve Turnstile challenges
- **Repo**: https://github.com/EndlessLoading/hermes-cf-bypass
