'''server'''
import os
from flask import Flask, send_from_directory, json
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv, find_dotenv
from flask_cors import CORS

# pylint: disable=no-member, too-few-public-methods, wrong-import-position, invalid-envvar-default, global-statement

load_dotenv(find_dotenv())  # This is to load your env variables from .env

APP = Flask(__name__, static_folder='./build/static')

# Point SQLAlchemy to your Heroku database
APP.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# Gets rid of a warning
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DB = SQLAlchemy(APP)

# IMPORTANT: This must be AFTER creating DB variable to prevent
# circular import issues
import models

DB.create_all()

# global users
# users=[]
# global rankings
# rankings=[]

CORS = CORS(APP, resources={r"/*": {"origins": "*"}})

SOCKETIO = SocketIO(APP,
                    CORS_allowed_origins="*",
                    json=json,
                    manage_session=False)


@APP.route('/', defaults={"filename": "index.html"})
@APP.route('/<path:filename>')
def index(filename):
    '''index'''
    return send_from_directory('./build', filename)


# When a client connects from this Socket connection, this function is run
@SOCKETIO.on('connect')
def on_connect():
    '''when user is connected'''
    print('User connected!')


# When a client disconnects from this Socket connection, this function is run
@SOCKETIO.on('disconnect')
def on_disconnect():
    '''when user is disconnected'''
    print('User disconnected!')


@SOCKETIO.on('login')
def on_login(data):
    '''when user is logged in'''
    print('logged in')
    print(data)
    # models.Player.query.filter(models.Player.username==data['username']).first()
    player = DB.session.query(models.Player).filter(
        models.Player.username ==
        data['username']).first()  #checking is username is in DB
    print(str(player is None))
    if player is None:  #if there is no player with this username in the database
        print('player not in DB')
        new_player = models.Player(username=data['username'], rank=100)
        DB.session.add(new_player)
        DB.session.commit()

    users = []
    rankings = []
    update_db(users, rankings)

    SOCKETIO.emit('login', {
        'newUsers': data['newUsers'],
        'username': data['username'],
        'users': users,
        'ranks': rankings
    },
                  broadcast=True,
                  include_self=False)


# When a client emits the event 'onClickBoard' to the server, this function is run
# 'onClickBoard' is a custom event name that we just decided
@SOCKETIO.on('board')
def on_board(
        data):  # data is whatever arg you pass in your emit call on client
    '''when user clicks on board'''
    print(data)
    # This emits the 'onClickBoard' event from the server to all clients except for
    # the client that emmitted the event that triggered this function
    board(data)

    SOCKETIO.emit('board', data, broadcast=True, include_self=False)


def board(element):
    '''to test on_board logic in tests/unmocked/on_board_test.py'''
    board_dict = {}
    for key, value in element.items():
        if key == 'cell':
            board_dict[key] = value

    return board_dict


@SOCKETIO.on('leaderboard')
def on_leaderboard(data):  # updating leaderboard data
    '''when user wants to see the leaderboard'''
    print(data)

    users = []
    rankings = []
    update_db(users, rankings)

    # This emits the 'onClickBoard' event from the server to all clients except for
    # the client that emmitted the event that triggered this function
    SOCKETIO.emit('leaderboard', {
        'users': users,
        'ranks': rankings
    },
                  broadcast=True,
                  include_self=True)


@SOCKETIO.on('winner')
def on_winner(data):  # update the ranking for that username in the DB based on the event data
    '''when there is a winner'''
    print(data)
    # models.Player.query.filter(models.Player.username==data['username']).first()
    if (data['winner'] != 'draw') and (data['loser'] != ''):
        winner = DB.session.query(models.Player).filter(
            models.Player.username == data['winner']).first()
        loser = DB.session.query(models.Player).filter(
            models.Player.username == data['loser']).first()
        winner.rank = winner.rank + 1
        loser.rank = loser.rank - 1
        DB.session.commit()
    print(str(winner.rank))
    print(str(loser.rank))

    users = []
    rankings = []
    update_db(users, rankings)

    SOCKETIO.emit('leaderboard', {
        "users": users,
        "ranks": rankings
    },
                  broadcast=True,
                  include_self=True)


def winner_test(elements):
    '''testing on_winner'''
    if (elements['winner'] != 'draw') and (elements['loser'] != ''):
        elements['winner'].rank = elements['winner'].rank + 1
        elements['loser'].rank = elements['loser'].rank - 1
        DB.session.commit()
        return [elements['winner'].rank, elements['loser'].rank]
    return None


@SOCKETIO.on('restart')
def on_restart(data):
    '''to replay'''
    print('restart ' + str(data))

    restart(data)

    SOCKETIO.emit('restart', data, broadcast=True, include_self=False)


def restart(element):
    '''to test on_restart logic in tests/unmocked/on_restart_test.py'''
    restart_dict = {}
    for x_key, y_value in element.items():
        if x_key == 'updateBoard' and y_value == [
                None, None, None, None, None, None, None, None, None
        ]:
            restart_dict[x_key] = y_value
        if x_key == 'cell' and y_value is None:
            restart_dict[x_key] = y_value
    return restart_dict


def update_db(users, rankings):
    '''orders players by rankings'''
    # table should be ordered from highest to lowest score
    all_players = DB.session.query(models.Player).order_by(
        models.Player.rank.desc())
    # clearing arrays before populating them with correctly ordered data

    for player in all_players:  # reordering users based on rank order
        users.append(player.username)
        rankings.append(player.rank)

    print(users)
    print(rankings)


def update_test():
    '''testing update_db'''
    # all_players = DB.session.query(models.Player).order_by(models.Player.rank.desc())
    all_players = models.Player.query.order_by(models.Player.rank.desc())
    # clearing arrays before populating them with correctly ordered data
    users = all_players
    print(users)
    return users


# Note we need to add this line so we can import app in the python shell
if __name__ == "__main__":
    SOCKETIO.run(
        APP,
        host=os.getenv('IP', '0.0.0.0'),
        port=8081 if os.getenv('C9_PORT') else int(os.getenv('PORT', 8081)),
    )
