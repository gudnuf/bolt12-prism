# config.py
import os

PATH_TO_LIGHTNING = os.environ.get('PATH_TO_LIGHTNING')
LIGHTNING_BIN_DIR = os.environ.get('LIGHTNING_BIN_DIR')

if PATH_TO_LIGHTNING and LIGHTNING_BIN_DIR:
    l1 = f'{LIGHTNING_BIN_DIR}/lightning-cli --lightning-dir={PATH_TO_LIGHTNING}/l1'
    l2 = f'{LIGHTNING_BIN_DIR}/lightning-cli --lightning-dir={PATH_TO_LIGHTNING}/l2'
    l3 = f'{LIGHTNING_BIN_DIR}/lightning-cli --lightning-dir={PATH_TO_LIGHTNING}/l3'
    l4 = f'{LIGHTNING_BIN_DIR}/lightning-cli --lightning-dir={PATH_TO_LIGHTNING}/l4'
    l5 = f'{LIGHTNING_BIN_DIR}/lightning-cli --lightning-dir={PATH_TO_LIGHTNING}/l5'
    
else:
    raise EnvironmentError("Environment variables 'PATH_TO_LIGHTNING' and 'LIGHTNING_BIN_DIR' must be set.")
