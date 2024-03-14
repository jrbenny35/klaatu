@generic_telemetry
Feature: Generic Telemetry event tests

    @smoke
    Scenario: Report correct telemetry for organic searches
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something
        And The browser reports correct provider telemetry for the withads organic event
        Then The user clicks on an ad
        Then The browser reports correct provider telemetry for the adclick organic event

    @smoke
    Scenario: Report correct telemetry for tagged searches
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        Then The browser reports correct telemetry for the urlbar search event
        Then The user clicks on an ad
        Then The browser reports correct telemetry for the urlbar adclick event

    @smoke
    Scenario: Report correct telemetry for tagged follow on searches
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something
        And The browser reports correct provider telemetry for the withads organic event
        Then The user triggers a follow-on search
        Then The browser reports correct provider telemetry for the withads unknown tagged follow on event
