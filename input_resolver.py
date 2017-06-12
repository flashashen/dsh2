from api import *


#  NOTE for completions, traverse tree and take every leaf's completions. Stop traversal at any node that is status_complete
# OR.. propogate up after child resolution, extending self's completion by that of all children's

class ResolutionPath:

    '''
    A possible completion path that might develop into further paths
    '''
    def __init__(self, node):

        self.cmd_node = node

        self.status = STATUS_UNSATISFIED
        self.match_result = MATCH_RESULT_NONE()

        # lazy initialized list of children paths which wrap cmd_node.children
        self.children = []

        # list of children in order of resolution. From this list the input could be reconstructed
        self.resolutions = []


    def amount_input_consumed(self):
        return self.match_result.stop - self.match_result.start


    def get_match_score(self):
        score = self.amount_input_consumed()*10
        if self.status == STATUS_COMPLETED:
            score += 2
        elif self.status == STATUS_SATISFIED:
            score += 1
        return score


    def pprint(self, level=0):
        print "name:{}, status:{}, match:{}, resolved:{}".format(
            self.cmd_node.name,
            self.status,
            self.match_result,
            [c.cmd_node.name for c in self.resolutions]).ljust(level*3)
        for child in self.children:
            child.pprint(level+1)

    def __repr__(self):
        return "name:{}, status:{}, match:{}, resolved:{}".format(
            self.cmd_node.name,
            self.status,
            self.match_result,
            [c.cmd_node.name for c in self.resolutions])





def execute(path, ctx):

    for child in path.resolutions:
        execute(child, ctx)

    path.cmd_node.exe_method(ctx)



def resolve(path, input_segments, start_index, ctx={}, input_mode=MODE_COMPLETE):

    path.match_result = path.cmd_node.match(input_segments, start_index)
    if path.match_result.status not in [MATCH_FULL]:
        return

    # add self to resolved list
    # path.resolutions.append(path)

    if not path.cmd_node.children:
        path.status = path.cmd_node.evaluate([])
        return


    path.children = [ResolutionPath(child) for child in path.cmd_node.children]
    start_index = path.match_result.stop

    while True:

        # if input_mode != MODE_COMPLETE and start_index >= len(input_segments):
        #     # No more input so nothing to resolve except completions against empty input
        #     break

        remaining_children = [ child for child in path.children if child not in path.resolutions]
        if not remaining_children:
            break

        # depth first traversal, resolving against current position in input.
        for child in remaining_children:
            resolve(child, input_segments, start_index, ctx, input_mode)

        # INVARIANT - Children have all resolved as much input as possible on current input,index.

        # re-evaluate status
        path.status = path.cmd_node.evaluate([child.status for child in path.children])

        # select child that resolved best. First, select based on amount of input consumed,
        # then take the comlpeted, then take the satisfied, then take whichever is first
        ranked = sorted(remaining_children, reverse=True, key=lambda child: child.get_match_score())


        if ranked[0].amount_input_consumed():

            # case 1: one child consumed most input, even counting fragment matches
            #   -> winner contributes completions, etc. resolution is over and solely dependent on this winning child
            if len(ranked) == 1 or ranked[0].amount_input_consumed() > ranked[1].amount_input_consumed():

                # As children are resolved, append to the resolved list so they won't be processed again
                # and also so we can re-construct the 'path' of resolution
                path.resolutions.append(ranked[0])

                # Stop index and completions come from winner
                path.match_result = MATCH_RESULT(
                    path.match_result.status,
                    path.match_result.start,
                    ranked[0].match_result.stop,
                    ranked[0].match_result.completions)

                # If the winner is unsatisfied, then don't give its peers a chance to consume more input.
                # Otherwise change the index into the input and see if its peers can do something with the
                # remaining input
                if ranked[0].status not in (STATUS_SATISFIED, STATUS_COMPLETED):
                    break
                else:
                    start_index = ranked[0].match_result.stop

            # case 2: two or more children 'consumed' input and same amount
            #   -> full/frag matches
            #   -> current path cannot be complete. map complete to satisfied if needed.
            else:
                # By definition, this node can't be completed if there are multiple possible
                # resolutions or completions of the input
                if path.status == STATUS_COMPLETED:
                    path.status = STATUS_SATISFIED
                # Increase the stop index and extend the current completions
                path.match_result = MATCH_RESULT(
                        path.match_result.status,
                        path.match_result.start,
                        ranked[0].match_result.stop,
                        path.match_result.completions)

                for child in path.children:
                    path.match_result.completions.extend(child.match_result.completions)
                break


        else:
            # case 3: no children consumed input
            # -> eval is complete as is. take completions from all
            for child in path.children:
                path.match_result.completions.extend(child.match_result.completions)
            break


        # if current node is completed there is nothing more to resolve, by definition
        if path.status == STATUS_COMPLETED:
            break

