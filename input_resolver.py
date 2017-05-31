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
        self.match_result = MATCH_RESULT_NONE

        # lazy initialized list of children paths which wrap cmd_node.children
        self.children = []

        # list of children in order of resolution. From this list the input could be reconstructed
        self.resolutions = []


    def get_match_score(self):
        score = (self.match_result.stop - self.match_result.start)*10
        if self.status == STATUS_COMPLETED:
            score += 2
        elif self.status == STATUS_SATISFIED:
            score += 1
        return score


    def __repr__(self):
        return "name:{}, status:{}, match:{}, input indices{}, resolved:{}".format(
            self.cmd_node.name,
            self.status,
            self.match_status,
            self.input_indices,
            [c.name for c in self.resolved_children])


 
    # 
    # def get_next_paths__all_peers(self):
    # 
    #     # self.assert_for_next_paths()
    # 
    #     # return peers as new paths, each with a peerlist containing all peers but themselves
    #     return [ResolutionPath(peer, self.remaining_segments, self.eligible_peers[:index]+self.eligible_peers[index+1:])
    #             for index, peer in enumerate(self.eligible_peers) ]
    # 
    # 
    # 
    # def get_next_paths__all_children(self):
    #
    #     # self.assert_for_next_paths()
    #
    #     # return children as new paths, each with a peerlist containing all children but themselves
    #     # return [ResolutionPath(child, self.remaining_segments, self.cmd_node.children[:index]+self.cmd_node.children[index+1:])
    #     #         for index, child in enumerate(self.cmd_node.children) ]
    #
    #     # no peers. the effect of this is that multiple children cannot be selected
    #     return [ResolutionPath(child, self.remaining_segments, self.cmd_node.peers_of(child))
    #             for index, child in enumerate(self.cmd_node.children) ]






def resolve(path, input_segments, start_index, input_mode=MODE_COMPLETE):

    path.match_result = path.cmd_node.match(input_segments, start_index)
    if path.match_result.status not in [MATCH_FULL]:
        return

    # add self to resolved list
    path.resolutions.append(path)

    if not path.cmd_node.children:
        path.status = path.cmd_node.evaluate([])
        return


    path.children = [ResolutionPath(child) for child in path.cmd_node.children]
    start_index = path.match_result.stop

    while True:
        remaining_children = [ child for child in path.children if child not in path.resolutions]
        if not remaining_children:
            break

        # depth first traversal, resolving against current position in input
        for child in remaining_children:
            resolve(child, input_segments, start_index)

        # select child that resolves best. First, select based on amount of input consumed,
        # then take the comlpeted, then take the satisfied, then take whichever is first
        winner = sorted(remaining_children, key=lambda child: child.get_match_score())[0]

        # if no input has been consumed then nothing has changed and nothing more to do
        if winner.match_result.stop <= winner.match_result.start:
            break

        path.resolutions.extend(winner.resolutions)
        start_index = winner.match_result.stop+1

        # re-evaluate status
        path.status = path.cmd_node.evaluate([child.status for child in path.children])
        if path.status == STATUS_COMPLETED:
            break



