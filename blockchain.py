from time import time
import json
import hashlib
from urllib.parse import urlparse
import requests


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Need to create the initial Block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # reset currrent list of transactions
        self.current_transactions = []

        # add this new Block to the list of Blocks
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Append a transaction object to the next mined Block

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        next_block_index = self.last_block['index'] + 1
        return next_block_index

    @staticmethod
    def hash(block):
        """
        Serialise our Block object into utf-8 encoded JSON and hash using hashlib's sha256 implementation

        :param block: <dict> Block
        :return: <str>
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        """
        Find a number p where the value of hash(previous p, p) contains 4 leading zeros 0000

        :param previous_proof: <int>
        :return: <int>
        """

        current_proof = 0
        while self.verify_proof(previous_proof, current_proof) is False:
            current_proof += 1

        return current_proof

    @staticmethod
    def verify_proof(previous_proof, proof):
        """
        Verifies the proof - Does hash(previous_proof, current_proof) contain 4 leading zeroes?

        :param previous_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{previous_proof}{proof}'.encode()
        hashed_guess = hashlib.sha256(guess).hexdigest()

        return hashed_guess[:4] == '0000'

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: <str> Address of the node. Eg. 'http://0.0.0.0:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.verify_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm which resolves chain discrepancies by replacing
        our chain with the longest valid chain in the list of registered nodes.

        :return: <bool> True if our chain was replaced, False if not
        """

        all_nodes = self.nodes
        new_chain = None
        max_length_seen = len(self.chain)

        # For each node, verify that nodes chain
        for node in all_nodes:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # This will eventually result in new_chain containing the longest valid chain
                if length > max_length_seen and self.valid_chain(chain):
                    max_length_seen = length
                    new_chain = chain

        # Replace our chain with the longest valid chain we could find
        if new_chain:
            self.chain = new_chain
            return True

        return False
