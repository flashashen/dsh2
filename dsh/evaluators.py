from dsh import api
from collections import defaultdict




def no_children(children):
    if children:
        raise ValueError('This evaluation method is not valid for nodes with children')
    return api.STATUS_COMPLETED



def require_all_children(statuses):
    """
    Satisfied when all children in the list are satisfied.
    Completed when all children in the list are completed.

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return api.STATUS_COMPLETED

    status_counts = __count_statuses(statuses )

    if status_counts[api.STATUS_EXCEEDED] > 0:
        # Don't propagate as exceeded. The parent of an exceeded child will
        # just be un-satisfied since the parent itself is not really exceeded.
        return api.STATUS_UNSATISFIED
    elif status_counts[api.STATUS_UNSATISFIED] > 0:
        return api.STATUS_UNSATISFIED
    elif status_counts[api.STATUS_COMPLETED] == len(statuses):
        return api.STATUS_COMPLETED
    else:
        # All are satisfied, but not all completed.
        return api.STATUS_SATISFIED



def choose_one_child(statuses):
    """
    Satisfied when exactly one child in the list is satisfied (completed implies satisfied).
    Completed when exactly one child in the list is satisfied and also is completed.

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return api.STATUS_COMPLETED

    status_counts = __count_statuses(statuses)

    if (status_counts[api.STATUS_COMPLETED] + status_counts[api.STATUS_SATISFIED]) > 1:
        return api.STATUS_EXCEEDED
    elif status_counts[api.STATUS_SATISFIED] == 1:
        return api.STATUS_SATISFIED
    elif status_counts[api.STATUS_COMPLETED] == 1:
        return api.STATUS_COMPLETED
    else:
        return api.STATUS_UNSATISFIED



def children_as_options(statuses):
    """
    All children are optional. Initial status is SATISFIED since
    no children are required. Status becomes completed when every
    child is completed

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return api.STATUS_COMPLETED

    status_counts = __count_statuses(statuses)

    if status_counts[api.STATUS_EXCEEDED]:
        return api.STATUS_UNSATISFIED
    elif status_counts[api.STATUS_COMPLETED] == len(statuses):
        return api.STATUS_COMPLETED
    else:
        return api.STATUS_SATISFIED


def __count_statuses(statuses):
    # use defaultdict counting idiom
    status_counts = defaultdict(int)
    for status in statuses:
        status_counts[status] += 1
    # There are only four valid statuses
    assert len(status_counts) <= 4
    return status_counts



