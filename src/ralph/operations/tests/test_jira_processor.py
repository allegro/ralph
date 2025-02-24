import json
from datetime import datetime
from os import path

from ralph.operations.changemanagement import jira
from ralph.tests import RalphTestCase


class JiraProcessorTestCase(RalphTestCase):
    def setUp(self):
        with open(
            path.join(path.dirname(__file__), "sample_jira_event.json"), "r"
        ) as f:
            self.jira_event = json.load(f)

    def test_get_assignee_username(self):
        self.assertEqual(
            "username.fortytwo", jira.get_assignee_username(self.jira_event)
        )

    def test_get_assignee_username_no_assignee_returns_none(self):
        self.jira_event["issue"]["fields"]["assignee"] = None
        self.assertIsNone(jira.get_assignee_username(self.jira_event))

    def test_get_reporter_username(self):
        self.assertEqual(
            "username.fourtwenty", jira.get_reporter_username(self.jira_event)
        )

    def test_get_reporter_username_no_reporter_returns_none(self):
        self.jira_event["issue"]["fields"]["reporter"] = None
        self.assertIsNone(jira.get_reporter_username(self.jira_event))

    def test_get_title(self):
        self.assertEqual("THIS IS THE SUMMARY", jira.get_title(self.jira_event))

    def test_get_description(self):
        self.assertEqual("THAT IS A TEST TICKET", jira.get_description(self.jira_event))

    def test_get_create_datetime(self):
        self.assertEqual(
            datetime(2017, 3, 20, 9, 10, 40, 0), jira.get_creation_date(self.jira_event)
        )

    def test_get_last_update_datetime(self):
        self.assertEqual(
            datetime(2017, 3, 20, 11, 33, 44, 0),
            jira.get_last_update_date(self.jira_event),
        )

    def test_get_resolution_datetime(self):
        self.jira_event["issue"]["fields"]["resolutiondate"] = (
            "2017-03-20T14:10:40.000+0100"
        )

        self.assertEqual(
            datetime(2017, 3, 20, 13, 10, 40, 0),
            jira.get_resolution_date(self.jira_event),
        )

    def test_get_resolution_datetime_no_time_returns_none(self):
        self.assertIsNone(jira.get_resolution_date(self.jira_event))

    def test_get_ticket_id(self):
        self.assertEqual("SOMEPROJ-42", jira.get_ticket_id(self.jira_event))

    def test_get_operation_name(self):
        self.assertEqual("Change", jira.get_operation_name(self.jira_event))

    def test_get_operation_status(self):
        self.assertEqual("Open", jira.get_operation_status(self.jira_event))
