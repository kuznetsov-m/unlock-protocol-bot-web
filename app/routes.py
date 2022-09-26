from flask import Flask
from flask import render_template, request, jsonify
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
import os
import telebot
from app import app, db
from app.models import TelegramUser

from siwe import SiweMessage
import siwe

user_to_message = {}

def signIsValid(sign: str, text: str, address: str):
    if None in [sign, text, address]:
        return False

    w3 = Web3(Web3.HTTPProvider(''))
    message = encode_defunct(text=text)
    sign_address = w3.eth.account.recover_message(
        message,
        signature=HexBytes(sign)
    )
    return sign_address.lower() == address.lower()

def signIsValid2(sign: str, message: SiweMessage, user_id: int, address: str):
    if None in [sign, user_id, address]:
        return False
    
    provider = os.environ.get('WEB3_PROVIDER')
    try:
        message.verify(signature=sign, nonce=message.nonce, domain=message.domain, provider=provider)
    except Exception as e:
        print(f'ERROR message.verify(): {e}')
        return False
    return True

def balanceOf(token_address: str, token_abi: str, address: str):
    w3 = Web3(Web3.HTTPProvider(os.environ.get('WEB3_PROVIDER')))
    contract = w3.eth.contract(
        address=Web3.toChecksumAddress(token_address),
        abi = token_abi
    )
    balance = contract.functions.balanceOf(Web3.toChecksumAddress(address)).call()
    return balance

def send_result_to_telegram_bot(user_id: int, sign_is_valid: str, balance: int):
    bot = telebot.TeleBot(os.environ.get('TELEGRAM_BOT_TOKEN'))

    keyboard = telebot.types.ReplyKeyboardMarkup(True, one_time_keyboard=True)
    keyboard.row('/start')

    if not sign_is_valid:
        bot.send_message(user_id, 'Sign is not valid. Check your wallet and try again.', reply_markup=keyboard)
    elif balance == 0:
        bot.send_message(user_id, 'You have no unlock token. Please check token you in wallet or buy new.', reply_markup=keyboard)
    else:
        bot.send_message(user_id, 'Check passed. Your link to go to the channel.\nPlease note that the link is one-time and only available for your telegram account.')

def update_user_data(user_id: int, account_address: str, sign_is_valid: str, balance: int):
    user = TelegramUser.query.filter_by(id=user_id).first()
    if sign_is_valid:    
        user.account_address = account_address
    user.balance = balance
    db.session.commit()

def build_message(account_address: str) -> str:
    domain = os.environ.get('BASE_URL')
    chain_id = 5
    eip_4361_string = {
        'domain': domain,
        'address': Web3.toChecksumAddress(account_address),
        'chain_id': chain_id
    }

    message: SiweMessage = SiweMessage(message=eip_4361_string)
    return message 

@app.route('/')
def hello_world():
    telegram_bot_name = os.environ.get('TELEGRAM_BOT_NAME')
    return render_template('index.html', telegram_bot_name=telegram_bot_name)

@app.route('/siwe_message', methods=['GET'])
def message():
    user_id = int(request.args.get('user_id'))
    token_address = request.args.get('token_address')
    account_address = request.args.get('account_address')

    siwe_message = build_message(account_address)
    user_to_message[user_id] = siwe_message
    return siwe_message.prepare_message()

@app.route('/siwe_sign', methods=['GET', 'POST'])
def siwe_sign():
    user_id = int(request.args.get('user_id'))
    token_address = request.args.get('token_address')
    if request.method == 'POST':
        assert token_address != None, 'token_address must be not empty'
        assert user_id != None, f'user_id must be not empty'

        response = request.json
        response['user_id'] = user_id

        sign = request.json.get('sign')
        account_address = request.json.get('address')

        sign_is_valid = signIsValid2(sign, user_to_message[user_id], user_id, account_address)
        response['sign_is_valid'] = sign_is_valid

        # balanceOf
        token_abi = ''
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        STATIC_DIR = os.path.join(APP_ROOT, 'static')
        with open(f'{STATIC_DIR}/abi.json', 'r') as file:
            token_abi = file.read()
        balance = balanceOf(token_address, token_abi, account_address)
        response['balance'] = balance

        update_user_data(user_id, account_address, sign_is_valid, balance)

        send_result_to_telegram_bot(user_id, sign_is_valid, balance)

        return jsonify(response)
    else:
        return render_template(
                'siwe_sign.html',
                sign_url=f'{os.environ.get("BASE_URL")}/siwe_sign?user_id={user_id}&token_address={token_address}',
                message_url=f'{os.environ.get("BASE_URL")}/siwe_message?user_id={user_id}&token_address={token_address}'
        )

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    message = 'message for sign'
    user_id = int(request.args.get('user_id'))
    token_address = request.args.get('token_address')

    if request.method == 'POST':
        assert token_address != None, 'token_address must be not empty'
        assert user_id != None, f'user_id must be not empty'

        response = request.json
        response['user_id'] = user_id

        sign = request.json.get('sign')
        account_address = request.json.get('address')

        sign_is_valid = signIsValid(sign, message, account_address)
        response['sign_is_valid'] = sign_is_valid

        # balanceOf
        token_abi = ''
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        STATIC_DIR = os.path.join(APP_ROOT, 'static')
        with open(f'{STATIC_DIR}/abi.json', 'r') as file:
            token_abi = file.read()
        balance = balanceOf(token_address, token_abi, account_address)
        response['balance'] = balance

        update_user_data(user_id, account_address, sign_is_valid, balance)

        send_result_to_telegram_bot(user_id, sign_is_valid, balance)

        return jsonify(response)
    else:
        return render_template(
            'sign.html',
            message=message,
            sign_url=f'{os.environ.get("BASE_URL")}/sign?user_id={user_id}&token_address={token_address}'
        )