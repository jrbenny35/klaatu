# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pytest_bdd import given, scenario, then


@scenario(
    "../features/generic_nimbus.feature",
    "The browser will enroll into the requested branch",
)
def test_experiment_enrolls_into_correct_branch():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    return selenium


@then("The experiment branch should be correctly reported")
def check_branch_in_telemetry(check_ping_for_experiment, request, variables):
    experiment_branch = request.config.getoption("--experiment-branch")
    data = check_ping_for_experiment(f"optin-{variables['slug']}")
    assert experiment_branch in data["branch"]