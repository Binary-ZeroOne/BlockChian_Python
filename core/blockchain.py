'''
    Blockchain类用来管理链条，它能存储交易，加入新块等
'''

import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse

class BlockChain(object):

    def __init__(self):
        # 初始化区块链以及当前的交易事务列表
        self.chain = []  # 该实例变量用于存储区块链
        self.current_transactions = []  # 该实例变量用于当前的交易事务列表
        # 创建创世区块
        self.new_block(previous_hash=1, proof=100)
        # 存储网络中其他节点的集合
        self.nodes = set()

    def new_block(self, proof, previous_hash=None):
        """
        在链上新建一个区块以及地址
        :param proof: <int> The proof given by the Proof of Work algorithm （新区块的工作量证明）
        :param previous_hash: (Optional) <str> Hash of previous Block （上一个区块的hash值）
        :return: <dict> New Block （返回新建的区块）
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            # 如果没有传递上一个区块的hash就计算出区块链中最后一个区块的hash
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 重置当前的交易信息列表
        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transactions(self, sender, recipient, amount):
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param sender: <str> Address of the Sender（发送方的地址）
        :param recipient: <str> Address of the Recipient （接收方的地址）
        :param amount: <int> Amount （交易数量）
        :return: <int> The index of the Block that will hold this transaction （返回该交易事务的块的索引）
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        生成区块的 SHA-256 hash值
        :param block: <dict> Block 区块
        :return: <str> 返回该区块的hash
        """

        # 我们必须确保字典是有序的，否则将会导致有不一致的hash
        blocak_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(blocak_string).hexdigest()
    
    @property
    def last_block(self):
        # 返回链中最后一个区块
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明:
         - 查找一个 p' 使得 hash(pp') 以4个0开头
         - p 是上一个区块的证明,  p' 是当前的证明
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头?
        :param last_proof: <int> Previous Proof  上一个区块的工作量证明
        :param proof: <int> Current Proof  当前的工作量证明
        :return: <bool> True if correct, False if not.  当hash以4个0开头则会返回True，否则会返回False
        """

        # 相当于使用了format函数，这是python3.6的新特性
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        Add a new node to the list of nodes 注册节点
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid  检查是否是有效链，遍历每个区块验证hash和proof，来确定一个给定的区块链是否有效
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-------------------------\n")

            # 检查block的hash是否正确
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            last_block = block
            current_index += 1

        return True

