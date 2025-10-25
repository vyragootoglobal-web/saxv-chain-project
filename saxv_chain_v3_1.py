import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError
import threading

# ======= Wallet =======
class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def sign(self, message):
        message_bytes = json.dumps(message, sort_keys=True).encode()
        return self.private_key.sign(message_bytes).hex()

    @staticmethod
    def verify_signature(public_key_hex, message, signature_hex):
        try:
            public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
            message_bytes = json.dumps(message, sort_keys=True).encode()
            signature = bytes.fromhex(signature_hex)
            return public_key.verify(signature, message_bytes)
        except BadSignatureError:
            return False

# ======= Blockchain =======
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        neighbours = self.nodes