"""
Asynchronous runner for transitions
"""
import logging

from django.db import transaction

from ralph.attachments.models import Attachment
from ralph.lib.transitions.exceptions import (
    AsyncTransitionError,
    FailedActionError,
    FreezeAsyncTransition,
    MoreThanOneStartedActionError,
    RescheduleAsyncTransitionActionLater
)
from ralph.lib.transitions.models import (
    _check_action_with_instances,
    _check_instances_for_transition,
    _order_actions_by_requirements,
    _post_transition_instance_processing,
    _prepare_action_data,
    TransitionJob,
    TransitionJobAction,
    TransitionJobActionStatus
)

logger = logging.getLogger(__name__)


def _check_previous_actions(job, executed_actions):
    """
    Check if:
    * none of previously executed actions has failed
    * there is max 1 started action
    """
    started_actions = 0
    for action in executed_actions:
        if action.status == TransitionJobActionStatus.FAILED:
            job.fail('Action {} has failed.'.format(action))
            raise FailedActionError()
        elif action.status == TransitionJobActionStatus.STARTED:
            started_actions += 1

    if started_actions > 1:
        job.fail('More than one started action')
        raise MoreThanOneStartedActionError()


def run_async_transition(job_id):
    transition_job = TransitionJob.objects.get(pk=job_id)
    transition_job.start()
    try:
        _perform_async_transition(transition_job)
    except Exception as e:
        logger.exception(e)
        transition_job.fail(str(e))


# TODO: unify this function with `ralph.lib.transitions.models.run_field_transition`  # noqa
def _perform_async_transition(transition_job):
    transition = transition_job.transition
    obj = transition_job.obj
    requester = transition_job.user
    _check_instances_for_transition(
        instances=[obj],
        transition=transition,
        check_async_job=False,
        requester=requester
    )
    _check_action_with_instances([obj], transition)
    # check if this job isn't already finished
    if not transition_job.is_running:
        logger.warning(
            'Running previously ended transition job: %s', transition_job
        )
        return
    # make sure that none of previous actions has failed
    executed_actions = list(transition_job.transition_job_actions.all())
    try:
        _check_previous_actions(transition_job, executed_actions)
    except AsyncTransitionError:
        return

    completed_actions_names = set([
        tja.action_name for tja in executed_actions
        if tja.status != TransitionJobActionStatus.STARTED
    ])
    attachments = []
    # TODO: move this to transition (sth like
    # `for action in transition.get_actions(obj)`)
    for action in _order_actions_by_requirements(transition.actions.all(), obj):
        transition_job.refresh_from_db()
        if transition_job.is_killed:
            logger.info('Transition job: {} is killed'.format(transition_job))
            return

        if action.name in completed_actions_names:
            logger.debug('Action {} already performed - skipping'.format(
                action.name
            ))
            continue
        logger.info('Performing action {} in transition {} (job: {})'.format(
            action, transition, transition_job
        ))
        func = getattr(obj, action.name)
        # TODO: disable save object ?
        # data should be in transition_job.params dict
        defaults = _prepare_action_data(
            action=action,
            **transition_job.params
        )
        tja = TransitionJobAction.objects.get_or_create(
            transition_job=transition_job,
            action_name=action.name,
            defaults=dict(
                status=TransitionJobActionStatus.STARTED,
            )
        )[0]
        freeze = False
        try:
            # we shouldn't run whole transition atomically since it could be
            # spreaded to multiple processes (multiple tasks) - run single
            # action in transaction instead
            with transaction.atomic():
                try:
                    result = func(
                        instances=[obj],
                        requester=requester,
                        tja=tja,
                        **defaults
                    )
                except RescheduleAsyncTransitionActionLater:
                    # action is not ready - reschedule this job later and
                    # continue when you left off
                    transition_job.reschedule()
                    return
                except FreezeAsyncTransition:
                    # if action raise this exception, we're assumming that it's
                    # finished
                    freeze = True
                else:
                    if isinstance(result, Attachment):
                        attachments.append(result)
        except Exception as e:
            logger.exception(e)
            tja.status = TransitionJobActionStatus.FAILED
            raise FailedActionError('Action {} has failed'.format(action.name)) from e  # noqa
        else:
            tja.status = TransitionJobActionStatus.FINISHED
        finally:
            tja.save()
        completed_actions_names.add(action.name)
        # freeze whole transition if demanded by some action
        if freeze:
            transition_job.freeze()
            return

    # save obj and history
    _post_transition_instance_processing(
        obj, transition, transition_job.params['data'],
        history_kwargs=transition_job.params['history_kwargs'],
        requester=requester, attachments=attachments,
    )
    transition_job.success()
