import time
import random
from instagram_login import login
from utils import handle_errors

@handle_errors
def send_bulk_dms(username, password, target_user, message, limit, delay, mode):
    cl = login(username, password)
    user_id = cl.user_id_from_username(target_user)

    if mode == 'followers':
        targets = cl.user_followers(user_id)
    else:
        targets = cl.user_following(user_id)

    success, errors = 0, 0
    for pk in list(targets.keys())[:limit]:
        try:
            cl.direct_send(message, [pk])
            success += 1
            time.sleep(delay)
        except Exception:
            errors += 1
            time.sleep(delay + random.uniform(1, 3))
    return f"✅ Sent: {success} | ❌ Failed: {errors}"
