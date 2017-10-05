from api import *



def match_always_consume_no_input(input_segments, start_index=None):
    """
    This matcher makes the node a container. No input is consumed and the
    completions are delegated to children

    :param self:
    :param input_segments:
    :param start_index:
    :return:
    """
    return MATCH_RESULT(MATCH_FULL, start_index, start_index, [])



def get_matcher_exact_string(str):
    return lambda input, index=None: match_string(str, input, index)

def match_string(str, input_segments, start_index=None):
    """
    Get a match status and stop,start indices of resovled input segments. Only a full match
    will return resolved indices. Indices are inclusive. This form of the match function, if
    there is a full match, always returns a stop index of start+1 since it performs a simple,
    single word match

    :param input_segments: split input
    :param start_index: Where to look in the input. Analagous to cursor position
    :return: (MATCH_STATUS, (start_of_resolved, end_of_resolved))
    """
    if start_index == None:
        start_index = 0

    if input_segments == None or len(input_segments) <= start_index:
        # If nothing is given as the input, then it matches as MATCH_EMPTY, a special case of fragment
        return MATCH_RESULT(MATCH_EMPTY, start_index, start_index, [str])

    word = input_segments[start_index].strip()

    if str.startswith(word):
        if str == word:
            # Full match 'consumes' this word and provides no completions
            return MATCH_RESULT(MATCH_FULL, start_index, start_index+1, [])
        else:
            # Fragment match also 'consumes this word but also provides completions
            return MATCH_RESULT(MATCH_FRAGMENT, start_index, start_index+1, [str])

    return MATCH_RESULT_NONE(start_index)


