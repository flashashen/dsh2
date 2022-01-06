import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../dsh')))

import dsh.main, dsh.node, dsh.evaluators, dsh.matchers, dsh.api, dsh.executors