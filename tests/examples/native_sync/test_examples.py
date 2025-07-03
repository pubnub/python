# flake8: noqa
import os
from examples.native_sync.file_handling import main as test_file_handling
from examples.native_sync.message_reactions import main as test_message_reactions

os.environ['CI'] = '1'