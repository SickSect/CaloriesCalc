import re

def check_if_digits_only(value):
    if re.match(r'^\d+$', value):
        return True
    else:
        return False
