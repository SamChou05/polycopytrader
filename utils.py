import requests
from web3 import Web3
from config import GAMMA_API_URL

def is_valid_address(address: str) -> bool:
    """Checks if the address is a valid checksummed Ethereum address."""
    return Web3.is_address(address)

def get_user_profile(address: str):
    """Fetches user profile metadata from Gamma API."""
    if not is_valid_address(address):
        raise ValueError(f"Invalid address: {address}")
    
    url = f"{GAMMA_API_URL}/profiles"
    params = {"address": address}
    
    try:
        # Gamma API profiles endpoint is public but might rate limit or block specific user agents
        # 401 Unauthorized implies it expects an API key or the one provided (if any) is wrong.
        # We are not passing headers explicitly here, so requests uses default.
        # Let's try adding a User-Agent.
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 401:
            print(f"Warning: Gamma API returned 401 for {address}. Proceeding without profile data.")
            return None
            
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching profile for {address}: {e}")
        return None

def get_market_price(market_id: str):
    # Placeholder for fetching current market price if needed for notional sizing
    pass
