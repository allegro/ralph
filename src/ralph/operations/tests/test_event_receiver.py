import json
from os import path
from unittest import mock

from ralph.operations.changemanagement.exceptions import IgnoreOperation
from ralph.operations.changemanagement.subscribtions import receive_chm_event
from ralph.operations.models import Operation
from ralph.tests import RalphTestCase


class ChangesReceiverTestCase(RalphTestCase):
    fixtures = ["operation_types", "operation_statuses"]

    def setUp(self):
        with open(
            path.join(path.dirname(__file__), "sample_jira_event.json"), "r"
        ) as f:
            self.jira_event = json.load(f)

    def test_new_event_records_operation(self):
        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id="SOMEPROJ-42")

        self.assertEqual("username.fortytwo", op.assignee.username)
        self.assertEqual("username.fourtwenty", op.reporter.username)
        self.assertEqual("Open", op.status.name)

    def test_recorded_operation_gets_updated(self):
        assignee_bak = self.jira_event["issue"]["fields"]["assignee"]
        self.jira_event["issue"]["fields"]["assignee"] = None

        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id="SOMEPROJ-42")
        self.assertEqual("Open", op.status.name)
        self.assertEqual(None, op.assignee)

        self.jira_event["issue"]["fields"]["assignee"] = assignee_bak
        self.jira_event["issue"]["fields"]["status"]["name"] = "Closed"

        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id="SOMEPROJ-42")
        self.assertEqual("Closed", op.status.name)
        self.assertEqual("username.fortytwo", op.assignee.username)

    def test_no_record_created_unknown_operation_type(self):
        self.jira_event["issue"]["fields"]["issuetype"]["name"] = "DEADBEEF"

        receive_chm_event(self.jira_event)

        with self.assertRaises(Operation.DoesNotExist):
            Operation.objects.get(ticket_id="SOMEPROJ-42")

    @mock.patch(
        "ralph.operations.changemanagement.jira.get_ticket_id",
        side_effect=IgnoreOperation(),
    )
    def test_no_record_created_when_IgnoreOperation_is_rised(self, m_get):
        receive_chm_event(self.jira_event)

        with self.assertRaises(Operation.DoesNotExist):
            Operation.objects.get(ticket_id="SOMEPROJ-42")

    def test_new_status_created_unknown_operation_status(self):
        new_status_name = "DEADBEEF"

        self.jira_event["issue"]["fields"]["status"]["name"] = new_status_name
        receive_chm_event(self.jira_event)
        op = Operation.objects.get(ticket_id="SOMEPROJ-42")

        self.assertEqual(new_status_name, op.status.name)
