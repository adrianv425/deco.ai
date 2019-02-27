import hashlib
import json
import ujson
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import random
from numpy import exp, array, dot
import requests
import socket
from flask import Flask, redirect, jsonify, request, render_template, url_for
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
import ast
import base64
import zlib


# Blockchain class, creates genesis block upon creation
class Blockchain(object):
    def __init__(self):
        # Set chain as empty array
        self.chain = []
        # Create first transaction to create tokens
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
        # initialize a list for nodes
        self.nodes = set()

        # Add transaction to the genesis block and add it to the chain
        self.new_block(previous_hash=1, proof=100)
        # Hold master key for sending out genesis tokens (not secure)
        self.master_private_key = RSA.generate(1024, Random.new().read)

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        transactions = [self.current_transactions.pop()]

        # Attempt to add all pending transactions to the next block
        # It will not allow sending/receiving two transactions from the same address in the same block
        # We will use a carry_over array to hold those transaction until next available block
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

        # Populate new block with new valid transactions
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = carry_over_transactions

        # Add block to chain
        self.chain.append(block)
        return block

    def register_node(self, address):
        """
        Add new node to node list. Needed to keep nodes synced across the network.
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
        Determine valid blockchain. (Verify all hash values with next block's value)
        :param chain: <list> Blockchain
        :return: <bool> True if valid, False if not
        """
        # We must verify the chain from the first block
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
        :param sender: <obj> key object of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :param data: <json> any message or data wanted to upload by user
        :param contract: <json> the terms on which the user will allow others to use the data
        :return: <int> The index of the Block that will hold this transaction
        """

        contract = json.loads(contract)
        balance = self.check_balance(sender)

        if balance < amount and recipient is not '4':
            print("Transaction not added.\nNot enough balance.")
            return -1

        required_amount = contract["amount"]

        if required_amount is not None:
            if recipient is not '1' and recipient is not '4':
                if amount < required_amount:
                    return -1

        txnID = str(uuid4()).replace('-', '')
        if not isinstance(data, str):
            if data['method'] == 'BUY':
                if 'weights' in data:
                    if 'inputs' in data:
                        code_return = {'output': "", 'weights': data['weights'], 'inputs': data['inputs']}
                    else:
                        code_return = {'output': "", 'weights': data['weights']}
                else:
                    if 'inputs' in data:
                        code_return = {'output': "", 'inputs': data['inputs']}
                    else:
                        code_return = {'output': ""}
                print()
                print("----------------------Executing code---------------------")
                print(data['code'])
                print("---------------------------------------------------------")
                exec(data['code'], code_return)
                data = code_return['output']
            elif data['method'] == 'TRAIN':
                code_return = {'output': "", 'training_data': data['training_data'], 'training_output': ""}
                print("---------------Training-------------------")
                print(data['training_data'])
                exec(data['code'], code_return)
                data = {
                    'output': code_return['output'],
                    'code': str(self.master_encoder(data['code'])),
                    'method': 'SELL',
                    'weights': str(code_return['training_output']),
                    'title': "Enhanced " + data['title']
                }

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'data': data,
            'sender_unspent_outputs': balance - amount,
            'recipient_unspent_outputs': self.check_balance(recipient) + amount,
            'smart_contract': contract,
            'transactionID': txnID
        })

        response = {
            'block_index': self.last_block['index'] + 1,
            'transactionID': txnID
        }

        return response

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
        block_string = json.dumps(block, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

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

    def master_encoder(self, code_string):
        # encrypt with master key
        public = blockchain.master_private_key.publickey()
        cipher = PKCS1_OAEP.new(public)
        cipher_text = {}
        length_values = len(code_string)
        ENCRYPTION_LIMIT = 86
        if length_values > ENCRYPTION_LIMIT:
            iterations = (length_values // ENCRYPTION_LIMIT) + 1
            x = 0
            y = ENCRYPTION_LIMIT
            for i in range(iterations):
                text = code_string[x:y].encode()
                cipher_text[str(i)] = cipher.encrypt(text)
                x += ENCRYPTION_LIMIT
                y += ENCRYPTION_LIMIT
        else:
            text = code_string.encode()
            cipher_text['0'] = cipher.encrypt(text)
        return cipher_text

    @property
    def last_block(self):
        #Returns the last Block in the chain
        return self.chain[-1]


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode()
            # <- or any other encoding of your choice
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


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
    print()
    print('---------Last Block ------------')
    print(last_block)
    proof = blockchain.proof_of_work(last_block)
    print('--------------------------------')
    print()

    # We must receive an award for finding the proof
    # The sender is "0" to signify that this node has mined a new coin
    blockchain.new_transaction("0", node_identifier, 15, "mining reward", "{\"amount\":0}")

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Created",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return render_template('mining.html', proof=response, chain=blockchain.chain, nodes=list(blockchain.nodes)), 302

#
# DECO.AI API ROUTES
#

@app.route('/nodes/register/')
@app.route('/nodes/register/<string:values>')
def register_nodes(values=None):
    if values is None:
        blockchain.resolve_conflicts()
    else:
        blockchain.register_node(values)
        blockchain.resolve_conflicts()

    return redirect("/", 302)


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


@app.route('/transactions/data-upload', methods=['POST'])
def data_upload():
    print()
    print("--------Attempting to upload data to blockchain---------")
    values = request.get_json()

    #Check that the required fields are in the POST'ed data
    required = ['sender_public', 'sender_private', 'data', 'contract']
    if not all(k in values for k in required):
        return 'Missing values', 400

    print()
    print("---Unencrypted----")
    print(len(values['data']['code']))
    print("-------------------")
    print()
    code_string = blockchain.master_encoder(values['data']['code'])
    values['data']['code'] = str(code_string)
    print('----Encrypted with Master Key-----')
    print(code_string)
    print('----------------------------------')
    print()


    #Create a new Transaction
    response = blockchain.new_transaction(values['sender_public'], '1', 0, values['data'], values['contract'])

    return jsonify(response), 200


@app.route('/transactions/upload', methods=['POST'])
def upload():
    print()
    print("--------Attempting to upload to blockchain---------")
    values = request.get_json()

    #Check that the required fields are in the POST'ed data
    required = ['sender_public', 'sender_private', 'data', 'contract']
    if not all(k in values for k in required):
        return 'Missing values', 400

    print()
    print("---Unencrypted----")
    print(len(values['data']['code']))
    print("-------------------")
    print()
    code_string = blockchain.master_encoder(values['data']['code'])
    values['data']['code'] = str(code_string)
    print('----Encrypted with Master Key-----')
    print(code_string)
    print('----------------------------------')
    print()


    #Create a new Transaction
    response = blockchain.new_transaction(values['sender_public'], '1', 0, values['data'], values['contract'])

    return jsonify(response), 200


@app.route('/transactions/uploads')
def show_uploads():
    chain = blockchain.chain
    return render_template('showUploads.html', chain=chain, nodes=list(blockchain.nodes)), 200


@app.route('/transactions/train-complete/<string:transactionID>')
def train_results(transactionID):
    chain = blockchain.chain
    result = ""
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == transactionID:
                result = trans['data']['output']
    return render_template('runAI.html', chain=chain, data=result, nodes=list(blockchain.nodes), modelTitle=transactionID), 200


@app.route('/transactions/training/<string:transactionID>')
def getData(transactionID):
    chain = blockchain.chain
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == transactionID:
                if trans['data']['method'] == 'SELL':
                    return render_template('training.html', model=trans, chain=chain, nodes=list(blockchain.nodes)), 200
    return render_template('notValid.html'), 200

@app.route('/transactions/train', methods=['POST'])
def train_ai():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'transactionID', 'training_data']
    if not all(k in values for k in required):
        return 'Missing values', 300

    chain = blockchain.chain
    code = ""
    smart_contract = ""
    response = {}
    title = ""

    private = blockchain.master_private_key
    cipher = PKCS1_OAEP.new(private)

    #look for requested model
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == values['transactionID']:
                print("*****Found the code******")
                title = trans['data']['title']
                print(type(trans['data']['code']))
                print(trans['data']['code'])
                print("______________________")
                c = ast.literal_eval(trans['data']['code'])
                print(c)
                print(type(c))
                if '1' not in c:
                    print("Less than")
                    print(c['0'])
                    code = cipher.decrypt(c['0'])
                else:
                    print("Greater than")
                    for t in c:
                        print(c[str(t)])
                        text = c[str(t)]
                        cipher_text = cipher.decrypt(text)
                        code += cipher_text.decode()
                print(code)
                smart_contract = json.dumps(trans['smart_contract'])
                break
    print("---------------------------------------------------------------------")
    print(type(values['training_data']))

    if code is not "":
        c = {
            'code': code,
            'method': "TRAIN",
            'training_data': values['training_data'],
            'title': title
        }
        response = blockchain.new_transaction(values['sender'], '4', 0, c, smart_contract)
    else:
        response['block_index'] = -2

    if response['block_index'] != -1:
        print()
        print("*********Success. Added new transaction to pool*************")
        print()
    elif response['block_index'] == -2:
        print("No code found with that transaction ID.")
    else:
        print("Not enough credits")

    return response['transactionID'], 200


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
    response = {}
    weights = ""

    private = blockchain.master_private_key
    cipher = PKCS1_OAEP.new(private)

    print()
    print("----------------Looking for requested service-----------------------")
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == values['transactionID']:
                print("*****Found the code******")
                print(type(trans['data']['code']))
                print(trans['data']['code'])
                print("______________________")
                c = ast.literal_eval(trans['data']['code'])
                print(c)
                print(type(c))
                if 'weights' in trans['data']:
                    weights = trans['data']['weights']

                if '1' not in c:
                    print("Less than")
                    print(c['0'])
                    code = cipher.decrypt(c['0'])
                else:
                    print("Greater than")
                    for t in c:
                        print(c[str(t)])
                        text = c[str(t)]
                        cipher_text = cipher.decrypt(text)
                        code += cipher_text.decode()
                print(code)
                recipient = trans['sender']
                smart_contract = json.dumps(trans['smart_contract'])
                
    print("---------------------------------------------------------------------")
    print()

    if code is not "":
        if 'inputs' in values:
            if weights is not "":
                c = {
                    'code': code,
                    'method': "BUY",
                    'inputs': values['inputs'],
                    'weights': weights
                }
            else:
                c = {
                    'code': code,
                    'method': "BUY",
                    'inputs': values['inputs']
                }
        else:
            if weights is not "":
                c = {
                    'code': code,
                    'method': "BUY",
                    'weights': weights
                }
            else:
                c = {
                    'code': code,
                    'method': "BUY"
                }
        response = blockchain.new_transaction(values['sender'], recipient, int(values['amount']), c, smart_contract)
    else:
        response['block_index'] = -2

    if response['block_index'] != -1:
        print()
        print("*********Success. Added new transaction to pool*************")
        print()
    elif response['block_index'] == -2:
        print("No code found with that transaction ID.")
    else:
        print("Not enough credits")

    return response['transactionID'], 200


@app.route('/transactions/ai/<string:transactionID>')
def ai_results(transactionID):
    chain = blockchain.chain
    result = ""
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == transactionID:
                result = trans['data']
    return render_template('runAI.html', chain=chain, data=result, nodes=list(blockchain.nodes), modelTitle=transactionID), 200


@app.route('/transactions/confirm/<string:transactionID>')
def confirm(transactionID):
    chain = blockchain.chain
    for block in chain:
        for trans in block['transactions']:
            if trans['transactionID'] == transactionID:
                if trans['data']['method'] == 'SELL':
                    return render_template('confirm.html', model=trans, chain=blockchain.chain, nodes=list(blockchain.nodes)), 200

    return render_template('notValid.html'), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/key-pair', methods=['GET'])
def key_pair():
    random_n = Random.new().read
    private_key = RSA.generate(1024, random_n)
    public = private_key.publickey()
    f = open('mypublickey.pem', 'wb')
    f2 = open('myprivatekey.pem', 'wb')
    f.write(public.exportKey('PEM'))
    f2.write(private_key.exportKey('PEM'))
    f.close()
    f2.close()

    return str(public.exportKey("PEM")) + str(private_key.exportKey("PEM")), 200


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
