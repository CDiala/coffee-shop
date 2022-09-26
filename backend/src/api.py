from crypt import methods
from distutils.dep_util import newer
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# Uncomment the following line to initialize the database, and comment it afterwards
# db_drop_and_create_all()

# ROUTES

# Get drink endpoint
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()

    # abort if drinks is empty
    if len(drinks) == 0:
        abort(404)

    drink_short_list = [drink.short() for drink in drinks]

    return jsonify({
        "success": True,
        'drinks': drink_short_list
    })


# Display drink details
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(jwt):
    drinks = Drink.query.all()

    drink_long = [drink.long() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drink_long
    })


# Create new drink
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(jwt):

    body = request.get_json()

    if body is None:
        abort(404)
    
    new_title = body.get('title', None)
    new_recipe = json.dumps(body.get('recipe', None))
    drink = Drink(title = new_title, recipe = new_recipe)
    drink.insert()
    
    return jsonify({
        'success': True,
        "drinks": drink.long()
    })


# Update drink
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):

    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    body = request.get_json()
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)

    if body is None:
        abort(404)
    else:
        if new_title is None:
            new_title = drink.title
        
        if new_recipe is not None:
            drink.recipe = json.dumps(new_recipe)

        drink.update()

        # Get updated drinks list
        drinks = Drink.query.all()
        drinks_short = [drink.short() for drink in drinks]

    return jsonify({
        "success": True,
        "drinks": drinks_short
    })


# Delete drink
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)
    
    drink.delete()

    return jsonify({
        "success": True, 
        "delete": id
    })

# Error Handling

# Example error handling for unprocessable entity
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found():
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

# AuthError error handler
@app.errorhandler(AuthError)
def auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response
