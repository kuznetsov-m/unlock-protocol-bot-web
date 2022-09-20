from flask import Flask
from flask import render_template, request, jsonify
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
import os
import telebot
from app import app

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


@app.route('/')
def hello_world():
    telegram_bot_name = os.environ.get('TELEGRAM_BOT_NAME')
    return render_template('index.html', telegram_bot_name=telegram_bot_name)

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
        print(f'current dir: {os.getcwd()}')
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        STATIC_DIR = os.path.join(APP_ROOT, 'static')
        print(f'current dir: {APP_ROOT}')
        with open(f'{STATIC_DIR}/abi.json', 'r') as file:
            token_abi = file.read()
        balance = balanceOf(token_address, token_abi, account_address)
        response['balance'] = balance

        send_result_to_telegram_bot(user_id, sign_is_valid, balance)

        return jsonify(response)
    else:
        return render_template(
            'sign.html',
            message=message,
            sign_url=f'{os.environ.get("BASE_URL")}/sign?user_id={user_id}&token_address={token_address}'
        )