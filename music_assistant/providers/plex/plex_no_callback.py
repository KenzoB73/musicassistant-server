#!/usr/bin/env python3
"""Make the Plex sign-in finish without the browser returning to Music Assistant."""
import re, sys

path = sys.argv[1]
src = open(path).read()
if "_wait_myplex_token" in src:
    sys.exit("already applied")

old_pat = re.compile(
    r"    auth_url = plex_auth\.oauthUrl\(session\.callback_url\)\n"
    r"(?:    #.*\n)?"
    r"    await session\.external\(auth_url, step_id=\"myplex_auth\", expires_in=600\)\n"
    r"    token = await session\.progress_until\(\n"
    r"        _poll_myplex_token\(plex_auth\),\n"
    r"        step_id=\"finalizing_auth\",\n"
    r"        text=\"finalizing_auth\",\n"
    r"        expires_in=45,\n"
    r"    \)\n"
)
new = (
    "    auth_url = plex_auth.oauthUrl()\n"
    "    # no browser callback needed: the token is obtained by polling plex.tv\n"
    "    token = await session.external_until(\n"
    "        _wait_myplex_token(plex_auth),\n"
    "        auth_url,\n"
    "        step_id=\"myplex_auth\",\n"
    "        expires_in=600,\n"
    "    )\n"
)
if not old_pat.search(src):
    sys.exit("Could not find the expected sign-in block; send me lines containing 'oauthUrl' in setup_flow.py")
src = old_pat.sub(new, src, count=1)

helper = '''

async def _wait_myplex_token(plex_auth: MyPlexPinLogin) -> str | None:
    """Poll plex.tv every 2 seconds until the PIN is linked (bounded by the step deadline)."""
    while True:
        if await asyncio.to_thread(plex_auth.checkLogin):
            return str(plex_auth.token) if plex_auth.token else None
        await asyncio.sleep(2)
'''
marker = "\n\nasync def _poll_myplex_token("
assert marker in src
src = src.replace(marker, helper + marker, 1)
open(path, "w").write(src)
print("patched", path)
