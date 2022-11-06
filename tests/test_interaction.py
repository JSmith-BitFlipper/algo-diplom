import pytest
import algosdk

from algopytest import (
    application_local_state,
    call_app, 
    opt_in_app,
    close_out_app,
)

DIPLOMA_METADATA = "Damian Barabonkov :: MIT :: BSc Computer Science and Engineering :: 2020"

def issue_diploma(owner_in, user_in, smart_contract_id):
    # The application arguments and account to be passed in to 
    # the smart contract as it expects
    app_args = ['issue_diploma', DIPLOMA_METADATA, 4]

    # Issue the `DIPLOMA_METADATA` to the recipient `user`
    call_app(owner_in, smart_contract_id, app_args=app_args, accounts=[user_in])


@pytest.mark.parametrize(
    "users",
    [
        # Issue a single diploma
        ["user1_in"],
        # Issue multiple diplomas
        ["user1_in", "user2_in", "user3_in", "user4_in"],
    ]
)
def test_issue_diplomas(request, owner_in, users, smart_contract_id):
    for user in users:
        user_in = request.getfixturevalue(user)
        issue_diploma(owner_in, user_in, smart_contract_id)

        # Check that the diploma was issued
        state = application_local_state(smart_contract_id, user_in)
        assert state['diploma'] == DIPLOMA_METADATA
        assert state['degree_duration'] == 4

def test_issue_many_diplomas(request, owner_in, create_user, smart_contract_id):
    num_users = 8
    users = []
    for i in range(num_users):
        user = create_user()
        users.append(user)
        opt_in_app(user, smart_contract_id)

        # Do some funky business to capture the `user` of this
        # local scope for every iteration of the loop
        def opt_out_fn(user):
            def _wrapper():
                close_out_app(user, smart_contract_id)
            return _wrapper

        # Opt out each `user` upon completion of this test, pass or fail
        request.addfinalizer(opt_out_fn(user))

        issue_diploma(owner_in, user, smart_contract_id)

    for user in users:
        # Check that the diploma was issued to `user`
        state = application_local_state(smart_contract_id, user)
        assert state['diploma'] == DIPLOMA_METADATA
        assert state['degree_duration'] == 4


def test_issue_diploma_raises(user1_in, smart_contract_id):    
    # Issue the `DIPLOMA_METADATA` to the recipient `user1`
    with pytest.raises(algosdk.error.AlgodHTTPError, match=r'transaction .*: logic eval error: assert failed'):    
        issue_diploma(user1_in, user1_in, smart_contract_id)

def test_revoke_diploma(owner_in, user1_in, smart_contract_id):
    # Issue and then revoke the diploma
    issue_diploma(owner_in, user1_in, smart_contract_id)

    # Check that the diploma was issued
    state = application_local_state(smart_contract_id, user1_in)
    assert state['diploma'] == DIPLOMA_METADATA
    assert state['degree_duration'] == 4

    # Revoke the `DIPLOMA_METADATA` to the `user1`
    call_app(owner_in, smart_contract_id, app_args=['revoke_diploma'], accounts=[user1_in])

    # Check that the diploma has been revoked
    state = application_local_state(smart_contract_id, user1_in)
    assert state == {}

def test_revoke_diploma_raises(owner_in, user1_in, user2_in, smart_contract_id):
    # Issue and then revoke the diploma
    issue_diploma(owner_in, user1_in, smart_contract_id)

    # Check that the diploma was issued
    state = application_local_state(smart_contract_id, user1_in)
    assert state['diploma'] == DIPLOMA_METADATA
    assert state['degree_duration'] == 4

    # The `user2` attempts to revoke the `DIPLOMA_METADATA` of `user1`
    with pytest.raises(algosdk.error.AlgodHTTPError, match=r'transaction .*: logic eval error: assert failed'):    
        call_app(user2_in, smart_contract_id, app_args=['revoke_diploma'], accounts=[user1_in])
