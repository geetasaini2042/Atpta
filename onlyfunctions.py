import requests
import base64
import requests

BOT_DATA_URL = "https://botdata123.singodiya.tech/all_registered_bot.json"

def get_webhook_base_url(bot_id: str) -> str:
    """
    🔹 Fetch the webhook_base_url for a given bot_id from remote JSON API.
    Returns the webhook_base_url string if found, otherwise 'N/A'.
    """
    try:
        response = requests.get(BOT_DATA_URL, timeout=10)
        response.raise_for_status()
        bots_data = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to load bots data: {e}")
        return "N/A"

    # 🔍 Search for bot_id in all owners' bot lists
    for owner_info in bots_data.values():
        bots = owner_info.get("bots", {})
        if bot_id in bots:
            return bots[bot_id].get("webhook_base_url", "N/A")

    return "N/A"


def get_bot_token_by_id(bot_id: str) -> str:
    """
    🔹 Fetch bot_token for a given bot_id.
    Steps:
      1. Get webhook_base_url using get_webhook_base_url(bot_id)
      2. Encode it in Base64
      3. Fetch bots.json from remote URL
      4. Return bot_token if found, else 'N/A'
    """
    try:
        # Step 1: Get webhook base URL
        webhook_base_url = get_webhook_base_url(bot_id)
        if webhook_base_url == "N/A":
            print(f"[ERROR] Webhook base URL not found for bot_id {bot_id}")
            return "N/A"

        # Step 2: Encode base URL to Base64
        encoded_url = base64.b64encode(webhook_base_url.encode()).decode()

        # Step 3: Build bots.json URL
        json_url = f"https://botdata123.singodiya.tech/{encoded_url}/bots.json"

        # Step 4: Fetch and parse bots.json
        response = requests.get(json_url, timeout=10)
        response.raise_for_status()
        bots_data = response.json()

        # Step 5: Extract bot_token
        if bot_id in bots_data:
            return bots_data[bot_id].get("bot_token", "N/A")
        else:
            print(f"[INFO] Bot ID {bot_id} not found in bots.json")
            return "N/A"

    except Exception as e:
        print(f"[ERROR] Failed to fetch bot token for {bot_id}: {e}")
        return "N/A"


def is_premium_active(bot_id):
    """
    Bot के webhook_base_url से premium status check करता है।
    Returns:
        True  → अगर premium active है
        False → अगर नहीं है या error हुआ
    """
    try:
        webhook_base_url = get_webhook_base_url(bot_id)
        if not webhook_base_url:
            return False

        url = f"{webhook_base_url}/check_premium/httpappxapi?bot_id={bot_id}"
        print("Webhook Url: ",url)
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return False

        data = response.json()
        print(data)
        return bool(data.get("premium_active", False))

    except Exception:
        return False