"""
app.response

Helper for making API returns consistent
"""
from flask import current_app as app
from flask import jsonify, make_response
import os
import sys
import traceback
from werkzeug.http import HTTP_STATUS_CODES


""" Used to jsonify response and code arguments for API return
Args:
    response: Message which needs to be converted to JSON
    code: HTTP error code (Default successful request)
Returns:
    JSON Flask response
"""
def make_json_response(response, code=200):
    #if response type is not defined, use default HTTP status name
    if code is not 200 and not response['errors']['type']:
        response['errors']['type'] = HTTP_STATUS_CODES[code]

    return make_response(jsonify(response), code)


""" Basic success response with optional message
Args:
    msg: message to be included with response
Returns:
    Call to make_json_response with success response
"""
def make_success_resp(msg=None, metadata={}):
    response = {
            'success': True,
            'message': msg or '',
            'metadata':metadata
            }
    return make_json_response(response)


""" Used to convert data to json format
Args:
    data: input data
    msg: message to be included with data
Returns:
    Call to make_json_response with data and msg
"""
def make_data_resp(data, msg=None, metadata={}, success=True):
    response = {
            'success': success,
            'data'   : data,
            'message': msg or '',
            'metadata':metadata
            }
    return make_json_response(response)


""" Used to create a basic JSON error response
Args:
    msg: message associated with error
    type: type of error
    code: HTTP error code
Returns:
    Call to make_json_response with error information
"""
def make_error_resp(msg, type=None, code=400, metadata={}):
    response = {
            'errors': {
                    'message' : msg or "An error occurred",
                    'type'     : type
                    },
            'success': False,
            'metadata':metadata
            }
    return make_json_response(response, code)


""" Used to create a basic JSON form error response
Args:
    form: form where error occurred
    msg: message associated with error
Returns:
    Call to make_json_response with form error information
"""
def make_form_error_resp(form, msg=None):
    type = 'Form validation error'
    if not msg:
        msg = form.errors
    return make_error_resp(msg=msg, type=type, code=422)


""" Used to create response after an exception is thrown
Args:
    exception: exception used for call
    type: type of error
    code: HTTP error code associated with exception
Returns:
    Call to make_error_resp with exception information
"""
def make_exception_resp(exception, type=None, code=500):
    #NOTE: Will probably not want to display exception to users in production
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #include filename, line number and stack-trace
    msg = "Exception: %s: %s: %s %s" % (exc_type, fname, exc_tb.tb_lineno, traceback.format_exc())
    if(app.config['DEBUG']):
        return make_error_resp(msg=msg, type=type, code=422)
    else:
        app.logger.critical('Exception caught:  %s' % msg)
        return make_error_resp(msg="Internal Server Error. Report this problem!", type=type, code=422)
