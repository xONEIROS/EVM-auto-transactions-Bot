import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3
from eth_account import Account

CONFIG_FILE = 'config.json'

HEADER = """
 #######  ##    ## ######## #### ########   #######   ######  
##     ## ###   ## ##        ##  ##     ## ##     ## ##    ## 
##     ## ####  ## ##        ##  ##     ## ##     ## ##       
##     ## ## ## ## ######    ##  ########  ##     ##  ######  
##     ## ##  #### ##        ##  ##   ##   ##     ##       ## 
##     ## ##   ### ##        ##  ##    ##  ##     ## ##    ## 
 #######  ##    ## ######## #### ##     ##  #######   ######  
"""

LINK = "https://x.com/0xoneiros"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    clear_screen()
    print(HEADER)
    print(LINK)
    print("\n" + "=" * 70 + "\n")

def save_config(rpc_url, chain_id, private_key, block_explorer):
    config = {'rpc_url': rpc_url, 'chain_id': chain_id, 'private_key': private_key, 'block_explorer': block_explorer}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def get_user_input():
    rpc_url = input("Enter the RPC URL: ")
    chain_id = int(input("Enter the Chain ID: "))
    private_key = input("Enter your private key: ")
    block_explorer = input("Enter the Block Explorer URL (e.g., https://etherscan.io/tx/): ")
    return rpc_url, chain_id, private_key, block_explorer

def get_gas_settings(w3):
    gas_price = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    gas_limit = 21000  # Standard gas limit for ETH transfers

    print(f"\nCurrent gas settings:")
    print(f"Gas Price: {gas_price_gwei:.2f} Gwei")
    print(f"Gas Limit: {gas_limit}")

    confirm = input("\nDo you want to use these gas settings? (y/n): ").lower()
    if confirm != 'y':
        gas_price_gwei = float(input("Enter new Gas Price (in Gwei): "))
        gas_price = w3.to_wei(gas_price_gwei, 'gwei')
        gas_limit = int(input("Enter new Gas Limit: "))

    return gas_price, gas_limit

def send_transaction(w3, from_account, to_address, amount, nonce, chain_id, gas_price, gas_limit):
    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id
    }
    signed_tx = from_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash

def send_transactions(w3, from_account, to_addresses, amount, chain_id, delay, block_explorer, gas_price, gas_limit):
    nonce = w3.eth.get_transaction_count(from_account.address)
    for i, to_address in enumerate(to_addresses, 1):
        try:
            tx_hash = send_transaction(w3, from_account, to_address, amount, nonce, chain_id, gas_price, gas_limit)
            print(f"Transaction {i} sent:")
            print(f"  To: {to_address}")
            print(f"  Amount: {amount} ETH")
            print(f"  Transaction Hash: {tx_hash.hex()}")
            if block_explorer:
                print(f"  Block Explorer Link: {block_explorer}{tx_hash.hex()}")
            print("--------------------")
            nonce += 1
            time.sleep(delay / 1000)
        except Exception as e:
            print(f"Transaction {i} failed:")
            print(f"  To: {to_address}")
            print(f"  Error: {str(e)}")
            print("--------------------")

def get_config():
    config = load_config()
    if config:
        use_previous = input("Do you want to use the previous configuration? (y/n): ").lower()
        if use_previous == 'y':
            return config['rpc_url'], config['chain_id'], config['private_key'], config['block_explorer']
    
    rpc_url, chain_id, private_key, block_explorer = get_user_input()
    save_config(rpc_url, chain_id, private_key, block_explorer)
    return rpc_url, chain_id, private_key, block_explorer

def main():
    display_header()
    
    rpc_url, chain_id, private_key, block_explorer = get_config()

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("Failed to connect to the network. Please check your RPC URL.")
        return

    network_chain_id = w3.eth.chain_id
    if network_chain_id != chain_id:
        print(f"Warning: The provided Chain ID ({chain_id}) does not match the network's Chain ID ({network_chain_id}).")
        continue_anyway = input("Do you want to continue anyway? (y/n): ").lower()
        if continue_anyway != 'y':
            return

    from_account = Account.from_key(private_key)

    gas_price, gas_limit = get_gas_settings(w3)

    num_wallets = int(input("Enter the number of wallets you want to create: "))
    amount = float(input("Enter the amount of ETH to send to each wallet: "))
    delay = int(input("Enter the delay between transactions in milliseconds (default 1000): ") or 1000)

    display_header()  # Clear screen and show header again before starting operations

    with ThreadPoolExecutor() as executor:
        new_wallets = list(executor.map(lambda _: Account.create(), range(num_wallets)))

    to_addresses = [wallet.address for wallet in new_wallets]

    try:
        send_transactions(w3, from_account, to_addresses, amount, chain_id, delay, block_explorer, gas_price, gas_limit)
        print("\nAll transactions sent.")
        
        print("\nNew wallet addresses:")
        for i, wallet in enumerate(new_wallets, 1):
            print(f"Wallet {i}: {wallet.address}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
