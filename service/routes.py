"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application
from .common.error_handlers import not_found, request_validation_error


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    location_url = url_for("read_account", account_id=account.id, _external=True)
    # location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################

# ... place you code here to LIST accounts ...
@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    Gets all the account records
    """
    app.logger.info("Request to read all accounts")
    accounts = Account.all()
    account_sers = [a.serialize() for a in accounts]

    app.logger.info("Found [%d] accounts", len(account_sers))
    return jsonify(account_sers), status.HTTP_200_OK


######################]################################################
# READ AN ACCOUNT
######################################################################

# ... place you code here to READ an account ...
@app.route("/accounts/<int:account_id>", methods=["GET"])
def read_account(account_id):
    """
    Reads an account by its id
    returns with error if the id is invalid
    """
    app.logger.info("Request to read an Account with id: %s", account_id)
    account = Account.find(account_id)

    if not account:
        app.logger.error("Account %s does not exist.", account_id)
        return not_found(f"Account {account_id} does not exist.")

    return account.serialize(), status.HTTP_200_OK

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################

# ... place you code here to UPDATE an account ...
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """
    Updates an account specified by its id, using the json payload
    """
    account_found = Account.find(account_id)

    if not account_found:
        app.logger.error("Account %s does not exist.", account_id)
        return not_found(f"Account {account_id} does not exist.")

    account_found.deserialize(request.get_json())

    if not account_found.id == account_id:
        app.logger.error("Invalid request, account id in URL: %d, and in the payload: %d is different",
                         account_id, account_found.id)
        return request_validation_error("ID mismatch")

    account_found.update()
    return account_found.serialize(), status.HTTP_200_OK

######################################################################
# DELETE AN ACCOUNT
######################################################################

# ... place you code here to DELETE an account ...
@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """
    Deletes an account specified by its id
    """
    app.logger.info("Request to delete an Account with id: %s", account_id)
    account_found = Account.find(account_id)

    if account_found:
        app.logger.info("Account %s has been found and will be deleted.", account_id)
        account_found.delete()

    return "", status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
