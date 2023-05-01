import os

# BASE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# LVL 1 DIR
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
SRC_DIR = os.path.join(BASE_DIR, 'src')
TEST_DIR = os.path.join(BASE_DIR, 'test')

# SPECIFIC FILES
LOGS = os.path.join(OUTPUT_DIR, 'logs', 'logs.txt')
ALL_LOGS = os.path.join(OUTPUT_DIR, 'logs', 'all_logs.txt')
TRADE_HISTORY = os.path.join(OUTPUT_DIR, 'history', 'trade_history.csv')
LIVE_HISTORY = os.path.join(OUTPUT_DIR, 'history', 'live_history.csv')