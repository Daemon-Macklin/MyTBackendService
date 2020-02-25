from flask import current_app as app
from flask import jsonify, make_response
import os
import sys
import traceback
from werkzeug.http import HTTP_STATUS_CODES

# Function to make a json object response
def make_json_response(response, code=200):
    # if response type is not defined, use default HTTP status name
    if code is not 200 and not response['errors']['type']:
        response['errors']['type'] = HTTP_STATUS_CODES[code]

    return make_response(jsonify(response), code)


# Function to make a success response
def make_success_resp(msg=None, metadata={}):
    response = {
        'success': True,
        'message': msg or '',
        'metadata': metadata
    }
    return make_json_response(response)


# Function to make data response
def make_data_resp(data, msg=None, metadata={}, success=True):
    response = {
        'success': success,
        'data': data,
        'message': msg or '',
        'metadata': metadata
    }
    return make_json_response(response)

# Function to make error response
def make_error_resp(msg, type=None, code=400, metadata={}):
    response = {
        'errors': {
            'message': msg or "An error occurred",
            'type': type
        },
        'success': False,
        'metadata': metadata
    }
    return make_json_response(response, code)


# Function to make form error response
def make_form_error_resp(form, msg=None):
    type = 'Form validation error'
    if not msg:
        msg = form.errors
    return make_error_resp(msg=msg, type=type, code=422)


