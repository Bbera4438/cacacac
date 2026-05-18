import os
import json
import random
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'frutiger-aero-upgrader-2024-secure'

# ======================== БАЗА ДАННЫХ СКИНОВ ========================
SKINS_DB = {
    1: {'id': 1, 'name': 'AK-47 | Redline', 'price': 50,
        'image': 'skins/ak47_redline.png', 'rarity': 'classified'},
    2: {'id': 2, 'name': 'AWP | Dragon Lore', 'price': 300,
        'image': 'skins/awp_dragon_lore.png', 'rarity': 'covert'},
    3: {'id': 3, 'name': 'M4A4 | Howl', 'price': 250,
        'image': 'skins/m4a4_howl.png', 'rarity': 'covert'},
    4: {'id': 4, 'name': 'Desert Eagle | Blaze', 'price': 150,
        'image': 'skins/deagle_blaze.png', 'rarity': 'classified'},
    5: {'id': 5, 'name': 'USP-S | Orion', 'price': 40,
        'image': 'skins/usps_orion.png', 'rarity': 'restricted'},
    6: {'id': 6, 'name': 'Glock-18 | Fade', 'price': 120,
        'image': 'skins/glock_fade.png', 'rarity': 'classified'},
    7: {'id': 7, 'name': 'SSG 08 | Blood in the Water', 'price': 80,
        'image': 'skins/ssg08_blood.png', 'rarity': 'restricted'},
    8: {'id': 8, 'name': 'P250 | Sand Dune', 'price': 1,
        'image': 'skins/p250_sand.png', 'rarity': 'consumer'},

    100: {'id': 100, 'name': '★ Karambit | Doppler', 'price': 1500,
          'image': 'skins/karambit_doppler.png', 'rarity': 'rare_special', 'chance': 1},
    101: {'id': 101, 'name': '★ Butterfly Knife | Slaughter', 'price': 1200,
          'image': 'skins/butterfly_slaughter.png', 'rarity': 'rare_special', 'chance': 2},
    102: {'id': 102, 'name': 'M4A1-S | Knight', 'price': 600,
          'image': 'skins/m4a1s_knight.png', 'rarity': 'covert', 'chance': 4},
    103: {'id': 103, 'name': 'AWP | Medusa', 'price': 500,
          'image': 'skins/awp_medusa.png', 'rarity': 'covert', 'chance': 5},
    104: {'id': 104, 'name': 'AK-47 | Fire Serpent', 'price': 400,
          'image': 'skins/ak47_fire_serpent.png', 'rarity': 'classified', 'chance': 6},
    105: {'id': 105, 'name': 'USP-S | Kill Confirmed', 'price': 350,
          'image': 'skins/usps_kill_confirmed.png', 'rarity': 'classified', 'chance': 7},
    106: {'id': 106, 'name': 'Glock-18 | Dragon Tattoo', 'price': 200,
          'image': 'skins/glock_dragon_tattoo.png', 'rarity': 'restricted', 'chance': 10},
    107: {'id': 107, 'name': 'Desert Eagle | Cobalt Disruption', 'price': 100,
          'image': 'skins/deagle_cobalt.png', 'rarity': 'restricted', 'chance': 15},
    200: {'id': 200, 'name': 'Nothing', 'price': 0,
          'image': 'skins/nothing.png', 'rarity': 'none', 'chance': 50}
}

SHOP_SKIN_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
UPGRADE_OUTCOMES_BASE = {100: 1, 101: 2, 102: 4, 103: 5, 104: 6, 105: 7, 106: 10, 107: 15, 200: 50}

def get_skin(id):
    return SKINS_DB.get(id)

# ======================== ХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ В JSON ========================
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_current_user():
    if 'user_id' in session:
        users = load_users()
        uid = session['user_id']
        if uid in users:
            return uid, users[uid]
    return None, None

# ======================== LIVE FEED ========================
REAL_WINS = []

FAKE_NAMES = ['CyberSlayer', 'Xx_ProGamer_xX', 'AWP_Goddess', 'FadeMaster', 'RushB_no_stop',
              'ToxicKid', 'NitroBoost', 'EzKatka', 'SilverElite', 'GlobalNinja']

def add_win_to_feed(nickname, outcome_name, price, image):
    global REAL_WINS
    REAL_WINS.insert(0, {
        'nickname': nickname,
        'outcome': outcome_name,
        'price': price,
        'image': image
    })
    if len(REAL_WINS) > 20:
        REAL_WINS.pop()

def generate_fake_wins(count=3):
    fake = []
    for _ in range(count):
        skin = random.choice(list(SKINS_DB.values()))
        if skin['id'] == 200:
            continue
        name = random.choice(FAKE_NAMES)
        fake.append({
            'nickname': name,
            'outcome': skin['name'],
            'price': skin['price'],
            'image': skin['image']
        })
    return fake

# ======================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ========================
def add_history(user_data, action, item_name, amount):
    user_data.setdefault('history', [])
    user_data['history'].insert(0, {
        'action': action,
        'item': item_name,
        'amount': amount,
        'time': datetime.now().strftime('%H:%M:%S')
    })
    if len(user_data['history']) > 30:
        user_data['history'].pop()

def add_xp(user_data, amount):
    user_data['xp'] = user_data.get('xp', 0) + amount

def get_level(user_data):
    return user_data.get('xp', 0) // 100 + 1

def calculate_odds(bet_price):
    mod_weights = {}
    for oid, base_weight in UPGRADE_OUTCOMES_BASE.items():
        outcome = get_skin(oid)
        if oid == 200:
            factor = max(0.2, 1 - bet_price / 200)
            mod_weights[oid] = base_weight * factor
        else:
            factor = min(bet_price / max(outcome['price'], 1), 1.0)
            mod_weights[oid] = base_weight * factor
    total = sum(mod_weights.values())
    odds = []
    for oid, weight in mod_weights.items():
        outcome = get_skin(oid)
        odds.append({
            'id': oid,
            'name': outcome['name'],
            'price': outcome['price'],
            'image': outcome['image'],
            'rarity': outcome['rarity'],
            'probability': round(weight / total * 100, 4)
        })
    return odds

# ======================== МАРШРУТЫ ========================
@app.before_request
def make_session_permanent():
    session.permanent = True

# --- АВТОРИЗАЦИЯ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        users = load_users()
        for uid, user in users.items():
            if user['login'] == login and hashlib.sha256((password + user['salt']).encode()).hexdigest() == user['password']:
                session['user_id'] = uid
                return redirect(url_for('index'))
        return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        if not login or not password:
            return render_template('register.html', error='Заполните все поля')
        users = load_users()
        if any(u['login'] == login for u in users.values()):
            return render_template('register.html', error='Пользователь уже существует')
        uid = str(len(users) + 1)
        salt = os.urandom(4).hex()
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        users[uid] = {
            'login': login,
            'password': hashed,
            'salt': salt,
            'balance': 1000,
            'inventory': [],
            'xp': 0,
            'history': [],
            'last_bonus': '2000-01-01T00:00:00',
            'avatar': 'default',
            'nickname': login
        }
        save_users(users)
        session['user_id'] = uid
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- ГЛАВНАЯ (МАГАЗИН) ---
@app.route('/')
def index():
    uid, user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    shop = [get_skin(i) for i in SHOP_SKIN_IDS]
    # Статистика сайта (из users.json)
    users = load_users()
    total_users = len(users)
    total_spins = sum(len(u.get('history', [])) for u in users.values())
    return render_template('index.html', user=user, balance=user['balance'], shop_skins=shop,
                           level=get_level(user), total_users=total_users, total_spins=total_spins)

# ПОКУПКА (POST, поддержка количества)
@app.route('/buy', methods=['POST'])
def buy_skin():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    skin_id = data.get('skin_id')
    quantity = data.get('quantity', 1)
    try:
        skin_id = int(skin_id)
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Неверные параметры'}), 400

    skin = get_skin(skin_id)
    if not skin or skin_id not in SHOP_SKIN_IDS:
        return jsonify({'error': 'Скин не найден'}), 404

    total_price = skin['price'] * quantity
    if user['balance'] < total_price:
        return jsonify({'error': 'Недостаточно средств'}), 400

    user['balance'] -= total_price
    for _ in range(quantity):
        user.setdefault('inventory', []).append(skin_id)
    add_history(user, 'Покупка', f'{skin["name"]} x{quantity}', -total_price)
    add_xp(user, 10 * quantity)

    users = load_users()
    users[uid] = user
    save_users(users)

    return jsonify({'message': f'Куплено {quantity} шт. {skin["name"]} за ${total_price}', 'balance': user['balance']})

# --- АПГРЕЙД ---
@app.route('/upgrade')
def upgrade():
    uid, user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    inv = [get_skin(i) for i in user.get('inventory', [])]
    return render_template('upgrade.html', user=user, balance=user['balance'], inventory=inv, level=get_level(user))

@app.route('/calculate_odds', methods=['POST'])
def calc_odds():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    skin_index = data.get('skin_index', 0)
    inv = user.get('inventory', [])
    if skin_index < 0 or skin_index >= len(inv):
        return jsonify({'error': 'Неверный индекс'}), 400
    skin = get_skin(inv[skin_index])
    odds = calculate_odds(skin['price'])
    return jsonify(odds)

@app.route('/spin', methods=['POST'])
def spin():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    skin_index = data.get('skin_index', 0)
    inv = user.get('inventory', [])
    if skin_index < 0 or skin_index >= len(inv):
        return jsonify({'error': 'invalid index'}), 400

    selected_id = inv[skin_index]
    selected_skin = get_skin(selected_id)
    bet_price = selected_skin['price']
    del inv[skin_index]

    mod_weights = {}
    for oid, base_weight in UPGRADE_OUTCOMES_BASE.items():
        outcome = get_skin(oid)
        if oid == 200:
            factor = max(0.2, 1 - bet_price / 200)
            mod_weights[oid] = base_weight * factor
        else:
            factor = min(bet_price / max(outcome['price'], 1), 1.0)
            mod_weights[oid] = base_weight * factor

    total = sum(mod_weights.values())
    roll = random.uniform(0, total)
    cum = 0
    outcome_id = None
    for oid, weight in mod_weights.items():
        cum += weight
        if roll <= cum:
            outcome_id = oid
            break

    outcome_skin = get_skin(outcome_id)

    if outcome_skin['name'] != 'Nothing':
        inv.append(outcome_id)

    add_history(user, 'Апгрейд', selected_skin['name'] + ' → ' + outcome_skin['name'], 0)
    add_xp(user, 20)

    if outcome_skin['name'] != 'Nothing':
        add_win_to_feed(user['nickname'], outcome_skin['name'], outcome_skin['price'], outcome_skin['image'])

    users = load_users()
    users[uid] = user
    save_users(users)

    sector_order = [100, 101, 102, 103, 104, 105, 106, 107, 200]
    sector_index = sector_order.index(outcome_id) if outcome_id in sector_order else 0

    return jsonify({
        'selected_name': selected_skin['name'],
        'outcome_name': outcome_skin['name'],
        'outcome_id': outcome_id,
        'outcome_price': outcome_skin['price'],
        'outcome_rarity': outcome_skin['rarity'],
        'sector_index': sector_index
    })

@app.route('/double', methods=['POST'])
def double_or_nothing():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    skin_id = data.get('skin_id')
    inv = user.get('inventory', [])
    if skin_id not in inv:
        return jsonify({'error': 'Скин не найден в инвентаре'}), 400

    skin = get_skin(skin_id)
    if not skin:
        return jsonify({'error': 'Неизвестный скин'}), 400

    win = random.random() < 0.5
    if win:
        doubled_value = skin['price'] * 2
        # Подбираем скины из базы (не Nothing) для начисления
        available_skins = [s for s in SKINS_DB.values() if s['id'] != 200 and s['price'] <= doubled_value]
        # Сортируем по убыванию цены, чтобы выдавать наиболее дорогие
        available_skins.sort(key=lambda x: x['price'], reverse=True)
        skins_to_give = []
        remaining = doubled_value
        for s in available_skins:
            if s['price'] <= remaining:
                skins_to_give.append(s)
                remaining -= s['price']
            if remaining <= 0:
                break
        # Если не набрали ни одного скина (слишком маленькая ставка), просто кладём деньги
        if not skins_to_give:
            user['balance'] += doubled_value
            msg = f'Вы удвоили! +${doubled_value} на баланс'
            add_history(user, 'Double Win (баланс)', skin['name'], doubled_value)
        else:
            # Добавляем скины в инвентарь
            for s in skins_to_give:
                inv.append(s['id'])
            # Остаток на баланс
            if remaining > 0:
                user['balance'] += remaining
            names = ', '.join([s['name'] for s in skins_to_give])
            msg = f'Вы удвоили! Получены: {names}'
            if remaining > 0:
                msg += f' + ${remaining} на баланс'
            add_history(user, 'Double Win (скины)', f'{skin["name"]} → {names}', doubled_value)
        add_xp(user, 30)
        add_win_to_feed(user['nickname'], skin['name'] + ' (Double)', doubled_value, skin['image'])
    else:
        inv.remove(skin_id)
        msg = 'Вы проиграли скин :('
        add_history(user, 'Double Lose', skin['name'], -skin['price'])
        add_xp(user, 5)

    users = load_users()
    users[uid] = user
    save_users(users)
    return jsonify({'win': win, 'message': msg, 'balance': user['balance']})

@app.route('/sell', methods=['POST'])
def sell_skin():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    skin_id = data.get('skin_id')
    inv = user.get('inventory', [])
    if skin_id not in inv:
        return jsonify({'error': 'Скин не найден'}), 400
    skin = get_skin(skin_id)
    commission = int(skin['price'] * 0.3)
    sell_price = skin['price'] - commission
    user['balance'] += sell_price
    inv.remove(skin_id)
    add_history(user, 'Продажа', skin['name'], sell_price)
    users = load_users()
    users[uid] = user
    save_users(users)
    return jsonify({'message': f'Продано за ${sell_price} (комиссия ${commission})', 'balance': user['balance']})

@app.route('/daily_bonus')
def daily_bonus():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    now = datetime.now()
    try:
        last = datetime.fromisoformat(user['last_bonus'])
    except:
        last = datetime(2000,1,1)
    if (now - last).total_seconds() < 86400:
        return jsonify({'error': 'Бонус можно получать раз в 24 часа', 'balance': user['balance']})
    bonus = random.randint(10, 100)
    user['balance'] += bonus
    user['last_bonus'] = now.isoformat()
    add_history(user, 'Ежедневный бонус', '', bonus)
    users = load_users()
    users[uid] = user
    save_users(users)
    return jsonify({'message': f'Вы получили ${bonus}!', 'balance': user['balance']})

@app.route('/live_feed')
def live_feed():
    real = REAL_WINS[:5]
    fake = generate_fake_wins(3)
    combined = real + fake
    random.shuffle(combined)
    return jsonify(combined[:8])

@app.route('/profile')
def profile():
    uid, user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    inv = [get_skin(i) for i in user.get('inventory', [])]
    return render_template('profile.html', user=user, balance=user['balance'], inventory=inv,
                           history=user.get('history', []), xp=user.get('xp', 0),
                           level=get_level(user), nickname=user.get('nickname', user['login']),
                           avatar=user.get('avatar', 'default'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    uid, user = get_current_user()
    if not user:
        return jsonify({'error': 'Не авторизован'}), 401
    data = request.get_json()
    if 'nickname' in data:
        user['nickname'] = data['nickname'][:20]
    if 'avatar' in data:
        user['avatar'] = data['avatar']
    users = load_users()
    users[uid] = user
    save_users(users)
    return jsonify({'status': 'ok'})

# ======================== ЗАПУСК ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)