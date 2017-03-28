import json
from os import path

from ralph.operations.changemanagement.subscribtions import receive_chm_event
from ralph.operations.models import Operation, OperationStatus
from ralph.tests import RalphTestCase


class ChangesReceiverTestCase(RalphTestCase):

    def setUp(self):
        with open(
            path.join(path.dirname(__file__), 'sample_jira_event.json'), 'r'
        ) as f:
            self.jira_event = json.load(f)

    def test_new_event_records_operation(self):
        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id='SOMEPROJ-42')

        self.assertEqual('username.fortytwo', op.asignee.username)
        self.assertEqual(OperationStatus.opened, op.status)

    def test_recorded_operation_gets_updated(self):
        assignee_bak = self.jira_event['issue']['fields']['assignee']
        self.jira_event['issue']['fields']['assignee'] = None

        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id='SOMEPROJ-42')
        self.assertEqual(OperationStatus.opened, op.status)
        self.assertEqual(None, op.asignee)

        self.jira_event['issue']['fields']['assignee'] = assignee_bak
        self.jira_event['issue']['fields']['status']['name'] = 'Closed'

        receive_chm_event(self.jira_event)

        op = Operation.objects.get(ticket_id='SOMEPROJ-42')
        self.assertEqual(OperationStatus.closed, op.status)
        self.assertEqual('username.fortytwo', op.asignee.username)

    def test_no_record_created_unknown_operation_type(self):
        self.jira_event['issue']['fields']['issuetype']['name'] = 'DEADBEEF'

        receive_chm_event(self.jira_event)

        with self.assertRaises(Operation.DoesNotExist):
            Operation.objects.get(ticket_id='SOMEPROJ-42')

    def test_no_record_created_unknown_operation_status(self):
        self.jira_event['issue']['fields']['status']['name'] = 'DEADBEEF'

        receive_chm_event(self.jira_event)

        with self.assertRaises(Operation.DoesNotExist):
            Operation.objects.get(ticket_id='SOMEPROJ-42')
