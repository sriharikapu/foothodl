from web3 import Web3
from ethereum import utils
import logging 
import os
from dotenv import load_dotenv
load_dotenv()

CONFIG = {
    'provider': 'https://dai.poa.network',
    'gas': 21000,
    'gasPrice': Web3.toWei('1', 'gwei')
}

def checksum_encode(addr): # Takes a 20-byte binary address as input
    o = ''
    v = utils.big_endian_to_int(utils.sha3(addr.hex()))
    for i, c in enumerate(addr.hex()):
        if c in '0123456789':
            o += c
        else:
            o += c.upper() if (v & (2**(255 - 4*i))) else c.lower()
    return '0x'+o


def send_payment(address, amount):
    formatted_address = checksum_encode(bytes.fromhex(address[2:]))
    web3 = Web3(Web3.HTTPProvider(CONFIG['provider']))
    nonce = web3.eth.getTransactionCount(os.getenv('PAYMENT_ADDRESS'))
    tx = {
      'to': formatted_address,
      'value': web3.toWei(amount, 'ether'),
      'gas': CONFIG['gas'],
      'gasPrice': CONFIG['gasPrice'],
      'nonce': nonce
      }
    signed = web3.eth.account.signTransaction(tx, os.getenv('PAYMENT_PK'))
    raw_tx = signed.rawTransaction
    logging.info(f'Raw transaction: {raw_tx}')
    tx_hash = web3.eth.sendRawTransaction(raw_tx)
    logging.info(f'Transaction hash: {tx_hash}') 
    #web3.eth.getTransactionReceipt(tx_hash)

