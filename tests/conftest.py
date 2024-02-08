# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pathlib import Path
import requests
import shutil
import time
import typing
import json

import pytest

from tests.toolbar import ToolBar


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--experiment-recipe",
        action="store",
        default=None,
        help="Recipe JSON for experiment",
    ),
    parser.addoption(
        "--experiment-branch",
        action="store",
        default=None,
        help="Experiment Branch to test",
    ),
    parser.addoption(
        "--run-update-test",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    ),
    parser.addoption(
        "--run-firefox-release",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    ),
    parser.addoption(
        "--private-browsing-enabled",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    )


@pytest.fixture(name="enroll_experiment", autouse=True)
def fixture_enroll_experiment(
    request: typing.Any,
    selenium: typing.Any,
    variables: dict,
    check_ping_for_experiment: object,
) -> typing.Any:
    """Fixture to enroll into an experiment"""
    experiment_branch = request.config.getoption("--experiment-branch")
    if experiment_branch == "":
        pytest.raises("The experiment branch must be declared")
    script = f"""
        const ExperimentManager = ChromeUtils.import("resource://nimbus/lib/ExperimentManager.jsm");
        const branchSlug = arguments[1];
        ExperimentManager.ExperimentManager.store._deleteForTests(arguments[1])
        const recipe = JSON.parse(arguments[0]);
        let branch = recipe.branches.find(b => b.slug == branchSlug);
        ExperimentManager.ExperimentManager.forceEnroll(recipe, branch);
    """

    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.execute_script(script, json.dumps(variables), experiment_branch)
    assert (
        check_ping_for_experiment(f"optin-{variables['slug']}") is not None
    ), "Experiment not found in telemetry"


@pytest.fixture(name="experiment_slug")
def fixture_experiment_slug(variables: dict) -> typing.Any:
    return f"optin-{variables['slug']}"


@pytest.fixture
def setup_profile(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    """Fixture to create a copy of the profile to use within the test."""
    if request.config.getoption("--run-update-test"):
        shutil.copytree(
            Path("utilities/klaatu-profile-old-base").absolute(),
            Path("utilities/klaatu-profile").absolute(),
            dirs_exist_ok=True,
            ignore_dangling_symlinks=True,
        )
        return f'{Path("utilities/klaatu-profile").absolute()}'
    if request.node.get_closest_marker(
        "reuse_profile"
    ) and not request.config.getoption("--run-update-test"):
        if request.config.getoption("--run-firefox-release"):
            shutil.copytree(
                Path("utilities/klaatu-profile-release-firefox-base").absolute(),
                Path("utilities/klaatu-profile-release-firefox").absolute(),
                dirs_exist_ok=True,
            )
            return f'{os.path.abspath("utilities/klaatu-profile-release-firefox")}'
        shutil.copytree(
            Path("utilities/klaatu-profile-current-base").absolute(),
            Path("utilities/klaatu-profile-current-nightly").absolute(),
            dirs_exist_ok=True,
        )
        return f'{Path("utilities/klaatu-profile-current-nightly").absolute()}'


@pytest.fixture
def firefox_options(
    setup_profile: typing.Any,
    pytestconfig: typing.Any,
    firefox_options: typing.Any,
    request: typing.Any,
) -> typing.Any:
    """Setup Firefox"""
    firefox_options.log.level = "trace"
    # if request.config.getoption("--run-update-test"):
    #     # if request.node.get_closest_marker(
    #     #     "update_test"
    #     # ):  # disable test needs different firefox
    #     #     binary = Path(
    #     #         "utilities/firefox-old-nightly-disable-test/firefox/firefox-bin"
    #     #     ).absolute()
    #     #     firefox_options.binary = f"{binary}"
    #     #     firefox_options.add_argument("-profile")
    #     #     firefox_options.add_argument(
    #     #         f'{Path("utilities/klaatu-profile-disable-test").absolute()}'
    #     #     )
    #     # else:
    #     binary = Path(
    #         "utilities/firefox-old-nightly/firefox/firefox-bin"
    #     ).absolute()
    #     firefox_options.binary = f"{binary}"
    #     firefox_options.add_argument("-profile")
    #     firefox_options.add_argument(setup_profile)
    # if request.config.getoption("--run-firefox-release"):
    #     binary = Path("utilities/firefox-release/firefox/firefox-bin").absolute()
    #     firefox_options.binary = f"{binary}"
    # if request.node.get_closest_marker("reuse_profile") and not request.config.getoption(
    #     "--run-update-test"
    # ):
    #     firefox_options.add_argument("-profile")
    #     firefox_options.add_argument(setup_profile)
    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    firefox_options.log.level = "trace"
    firefox_options.set_preference("browser.cache.disk.smart_size.enabled", False)
    firefox_options.set_preference("toolkit.telemetry.server", "http://localhost:5000")
    firefox_options.set_preference("telemetry.fog.test.localhost_port", -1)
    firefox_options.set_preference("toolkit.telemetry.initDelay", 1)
    firefox_options.set_preference("ui.popup.disable_autohide", True)
    firefox_options.set_preference("toolkit.telemetry.minSubsessionLength", 0)
    firefox_options.set_preference("datareporting.healthreport.uploadEnabled", True)
    firefox_options.set_preference("datareporting.policy.dataSubmissionEnabled", True)
    firefox_options.set_preference("remote.prefs.recommended", False)
    firefox_options.set_preference(
        "datareporting.policy.dataSubmissionPolicyBypassNotification", False
    )
    firefox_options.set_preference("sticky.targeting.test.pref", True)
    firefox_options.set_preference("toolkit.telemetry.log.level", "Trace")
    firefox_options.set_preference("toolkit.telemetry.log.dump", True)
    firefox_options.set_preference("toolkit.telemetry.send.overrideOfficialCheck", True)
    firefox_options.set_preference(
        "toolkit.telemetry.testing.disableFuzzingDelay", True
    )
    firefox_options.set_preference("nimbus.debug", True)
    firefox_options.set_preference("app.normandy.run_interval_seconds", 30)
    firefox_options.set_preference(
        "security.content.signature.root_hash",
        "5E:36:F2:14:DE:82:3F:8B:29:96:89:23:5F:03:41:AC:AF:A0:75:AF:82:CB:4C:D4:30:7C:3D:B3:43:39:2A:FE",  # noqa: E501
    )
    firefox_options.set_preference("services.settings.server", "http://kinto:8888/v1")
    firefox_options.set_preference("datareporting.healthreport.service.enabled", True)
    firefox_options.set_preference(
        "datareporting.healthreport.logging.consoleEnabled", True
    )
    firefox_options.set_preference("datareporting.healthreport.service.firstRun", True)
    firefox_options.set_preference(
        "datareporting.healthreport.documentServerURI",
        "https://www.mozilla.org/legal/privacy/firefox.html#health-report",
    )
    firefox_options.set_preference(
        "app.normandy.api_url", "https://normandy.cdn.mozilla.net/api/v1"
    )
    firefox_options.set_preference(
        "app.normandy.user_id", "7ef5ab6d-42d6-4c4e-877d-c3174438050a"
    )
    firefox_options.set_preference("messaging-system.log", "debug")
    firefox_options.set_preference("toolkit.telemetry.scheduler.tickInterval", 30)
    firefox_options.set_preference("toolkit.telemetry.collectInterval", 1)
    firefox_options.set_preference(
        "toolkit.telemetry.eventping.minimumFrequency", 30000
    )
    firefox_options.set_preference("toolkit.telemetry.unified", True)
    firefox_options.set_preference("allowServerURLOverride", True)
    firefox_options.set_preference("browser.aboutConfig.showWarning", False)
    firefox_options.add_argument("-headless")
    yield firefox_options

    # Delete old pings
    requests.delete("http://localhost:5000/pings")

    # Remove old profile
    if (
        request.node.get_closest_marker("reuse_profile")
        and not request.config.getoption("--run-update-test")
        or request.config.getoption("--run-update-test")
    ):
        shutil.rmtree(setup_profile)


@pytest.fixture
def firefox_startup_time(firefox: typing.Any) -> typing.Any:
    """Startup with no extension installed"""
    return firefox.selenium.execute_script(
        """
        perfData = window.performance.timing 
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )


@pytest.fixture
def selenium(
    pytestconfig: typing.Any, selenium: typing.Any, variables: dict
) -> typing.Any:
    """Setup Selenium"""
    return selenium


@pytest.fixture
def trigger_experiment_loader(selenium):
    def _trigger_experiment_loader():
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(
                """
                    const { RemoteSettings } = ChromeUtils.import(
                        "resource://services-settings/remote-settings.js"
                    );
                    const { RemoteSettingsExperimentLoader } = ChromeUtils.import(
                        "resource://nimbus/lib/RemoteSettingsExperimentLoader.jsm"
                    );

                    RemoteSettings.pollChanges();
                    RemoteSettingsExperimentLoader.updateRecipes();
                """
            )
        time.sleep(5)

    return _trigger_experiment_loader


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(trigger_experiment_loader):
    def _check_ping_for_experiment(experiment=None):
        control = True
        timeout = time.time() + 60 * 5
        while control and time.time() < timeout:
            data = requests.get("http://localhost:5000/pings").json()
            try:
                experiments_data = [
                    item["environment"]["experiments"]
                    for item in data
                    if "experiments" in item["environment"]
                ]
            except KeyError:
                continue
            else:
                for item in experiments_data:
                    if experiment in item:
                        return item[experiment]
                time.sleep(5)
                trigger_experiment_loader()
        else:
            return False

    return _check_ping_for_experiment
