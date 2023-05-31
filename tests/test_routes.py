"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.INFO)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should read an account if id is provided"""
        account = self._create_accounts(1)[0]

        response = self.client.get(f"{BASE_URL}/{account.id}", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], account.name)

    def test_account_not_found(self):
        """It should return with error, if account id is invalid"""

        response = self.client.get(f"{BASE_URL}/0", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """It shall return with the list of all accounts"""
        self._create_accounts(5)

        response = self.client.get(f"{BASE_URL}", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(5, len(data))

    def test_update_account(self):
        """
        Existing account shall be updated
        """

        original_account = AccountFactory()
        original_response = self.client.post(
            f"{BASE_URL}",
            json=original_account.serialize(),
            content_type="application/json")
        self.assertEqual(original_response.status_code, status.HTTP_201_CREATED)
        read_account = original_response.get_json()

        #update account
        read_account["name"] += " Foo"
        read_account_id = read_account["id"]
        updated_response = self.client.put(
            f"{BASE_URL}/{read_account_id}",
            json=read_account,
            content_type="application/json")

        self.assertEqual(updated_response.status_code, status.HTTP_200_OK)
        updated_account = updated_response.get_json()
        self.assertEqual(updated_account, read_account)

    def test_update_nonexistent(self):
        """
        Nonexistent account results 404
        """

        account = AccountFactory()
        response = self.client.put(
            f"{BASE_URL}/0",
            json=account.serialize(),
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_update(self):
        """
        Account update with invalid ID shall be rejected
        """

        original_account = AccountFactory()
        original_response = self.client.post(
            f"{BASE_URL}",
            json=original_account.serialize(),
            content_type="application/json")
        self.assertEqual(original_response.status_code, status.HTTP_201_CREATED)
        read_data = original_response.get_json()

        # save old account id
        read_account_id = int(read_data["id"])

        # make it invalid
        read_account = Account()
        read_account.deserialize(read_data)
        read_account.id = read_account_id+1

        response = self.client.put(
            f"{BASE_URL}/{read_account_id}",
            json=read_account.serialize(),
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

