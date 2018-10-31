import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import random
from numpy import exp, array, dot
import requests
import socket
from flask import Flask, redirect, jsonify, request, render_template, url_for


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = [{
            'sender': "0",
            'recipient': "0",
            'amount': 21000000,
            'data': 'Genesis Block',
            'sender_unspent_outputs': 21000000,
            'recipient_unspent_outputs': 21000000,
            'smart_contract': "N/A",
            'transactionID': str(uuid4()).replace('-', ''),
        }]
        self.nodes = set()

        #Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        transactions = [self.current_transactions.pop()]
        carry_over_transactions = []

        for t in self.current_transactions:
            s = 0
            for a in transactions:
                s += 1
                if t['recipient'] == a['recipient']:
                    print("Recipient == recipient")
                    carry_over_transactions.append(t)
                    break
                elif t['sender'] == a['recipient']:
                    print("sender == recipient")
                    carry_over_transactions.append(t)
                    break
                elif t['sender'] == a['sender']:
                    print("sender == sender")
                    carry_over_transactions.append(t)
                    break
                elif t['recipient'] == a['sender']:
                    print("recipient == sender")
                    carry_over_transactions.append(t)
                    break
                elif len(transactions) == s:
                    transactions.append(t)
                    break

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        #Reset the current list of transactions
        self.current_transactions = carry_over_transactions

        self.chain.append(block)
        return block

    def register_node(self, address):
        """
        Add new node to node list
        :param address: <str> address of node
        :return: None
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Determine valid blockchain
        :param chain: <list> Blockchain
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
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm
        :return: <bool> True if our chain was replaced, False if not
        """
        print("checking conflicts")
        neighbors = self.nodes
        new_chain = None

        #only want chains longer than ours
        max_length = len(self.chain)

        myip = socket.gethostbyname(socket.gethostname()) + ":5000"

        #Grab and verify the chain from all the nodes in our network
        for node in neighbors:
            if socket.getfqdn(node) != myip:
                print("sending get to " + socket.getfqdn(node))
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    #Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

        #Replace our chain if discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            print("replaced")
            return True

        print("Not replaced")
        return False

    def new_transaction(self, sender, recipient, amount, data, contract):
        """"
        #Adds a new transaction to the list of transactions
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :param data: <str> any message or data wanted to upload by user
        :param contract: <str> the terms on which the user will allow others to use the data
        :return: <int> The index of the Block that will hold this transaction
        """

        balance = self.check_balance(sender)

        if balance < amount:
            return "Transaction not added.\nNot enough balance."

        self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
                'data': data,
                'sender_unspent_outputs': balance - amount,
                'recipient_unspent_outputs': self.check_balance(recipient) + amount,
                'smart_contract': contract,
                'transactionID': str(uuid4()).replace('-', '')
            })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm
        :param last_block: <int>
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def hash(block):
        #Creates a SHA-256 hash of a Block
        """"
        :param block: <dict> Block
        :return: <str>
        """

        #We must make sure that the dictionary is ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def check_balance(self, address):
        """

        :param address: <str> address of user we want balance of
        :return: <int> balance of user
        """
        chain = self.chain

        for block in reversed(chain):
            for trans in block['transactions']:
                if trans['sender'] == address:
                    return trans['sender_unspent_outputs']
                elif trans['recipient'] == address:
                    return trans['recipient_unspent_outputs']
        return 0

    def valid_proof(self, last_proof, proof, last_hash):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param proof: <int> Current Proof
        :param last_proof: <int> Previous Proof
        :param last_hash: <str> The hash of the previous Block
        :return: <bool> True if correct, False if not
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @property
    def last_block(self):
        #Returns the last Block in the chain
        return self.chain[-1]

#Insantiate our Node
app = Flask(__name__)

#Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

#Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    #We run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    #We must receive an aware for finding the proof
    #The sender is "0" to signify that this node has mined a new coin
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=15,
        data="mining reward",
        contract="N/A",
    )

    #Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return render_template('mining.html', proof=response, code="<h1>Blah</h1>"), 302

@app.route('/nodes/register/')
@app.route('/nodes/register/<string:values>')
def register_nodes(values=None):
    if values is None:
        blockchain.resolve_conflicts()
    else:
        blockchain.register_node(values)
        blockchain.resolve_conflicts()

    return redirect("/", 302)

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'chain': blockchain.chain
        }

    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    #Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], "Normal trnx", "N/A")

    response = {
        'message': index
    }
    return jsonify(response), 201


@app.route('/transactions/upload', methods=['POST'])
def upload():
    values = request.get_json()

    #Check that the required fields are in the POST'ed data
    required = ['sender', 'data', 'contract']
    if not all(k in values for k in required):
        return 'Missing values', 400

    #Create a new Transaction
    index = blockchain.new_transaction(values['sender'], '1', 0, values['data'], values['contract'])

    response = {
        'message': index
    }
    return jsonify(response), 201


@app.route('/transactions/ai', methods=['POST'])
def run_ai():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'amount', 'transactionID']
    if not all(k in values for k in required):
        return 'Missing values', 300

    recipient = ""
    chain = blockchain.chain
    code = ""
    smart_contract = ""

    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == values['transactionID']:
                code = trans['data']
                recipient = trans['sender']
                smart_contract = trans['smart_contract']

    response = blockchain.new_transaction(values['sender'], recipient, values['amount'], "AI purchase", smart_contract)

    print(response)
    print("Executing code")
    exec(code)

    return "Done", 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/', methods=['GET'])
def home():
    chain = blockchain.chain
    ip = socket.gethostbyname(socket.gethostname())
    nodes = [f'http://{ip}:5000']

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    return render_template('index.html', chain=chain, nodes=list(blockchain.nodes)), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)
