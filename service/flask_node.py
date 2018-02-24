'''
    创建三个接口：
        /transactions/new 用于创建一个交易并添加到区块
        /mine 告诉服务器去挖掘新的区块
        /chain 返回整个区块链
'''

from textwrap import dedent
from flask import Flask, jsonify, request
from core.blockchain import BlockChain
from uuid import uuid4
import requests

# 实例化节点 
app = Flask(__name__)

# 为该节点生成一个随机的全局唯一的地址
node_identifier = str(uuid4()).replace('-', '')

# 实例化区块链对象
blockchain = BlockChain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # 创建/transactions/new POST接口，可以给接口发送交易数据.
    values = request.get_json()

    # 检查所需要的字段是否位于POST的data中
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing values', 400

    # 新建交易信息
    index = blockchain.new_transactions(
        values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}

    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # 创建/mine GET接口，运行工作算法的证明来获得下一个证明

    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transactions(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # 构建新的区块
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    # 创建 /chain 接口, 返回整个区块链。
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }

    return jsonify(response), 200


def resolve_conflicts():
    """
    共识算法解决冲突
    使用网络中最长的链.
    遍历所有的邻居节点，并用上一个方法检查链的有效性， 如果发现有效更长链，就替换掉自己的链
    :return: <bool> True 如果链被取代, 否则为False
    """

    neighbours = blockchain.nodes
    new_chain = None

    # 寻找最长的区块链
    max_length = len(blockchain.chain)

    # 获取并验证网络中的所有节点的区块链
    for node in neighbours:
        response = requests.get(f'http://{node}/chain')
        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            # 检查长度是否长，链是否有效
            if length > max_length and blockchain.valid_chain(chain):
                max_length = length
                new_chain = chain

    # 如果我们发现一个新的有效链比我们的长，就替换我们的链
    if new_chain:
        blockchain.chain = new_chain
        return True

    return False


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    '''
        该路由用于注册节点
    '''
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    '''
        该路由用于解决冲突
    '''
    replaced = resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain,
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain,
        }

    return jsonify(response), 200


def run(port):
    # 让服务运行在端口5000上
    app.run(host='127.0.0.1', port=port)
