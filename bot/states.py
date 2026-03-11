from enum import IntEnum


class DialogState(IntEnum):
    """Состояния диалога для ConversationHandler"""
    SET_CALORIES = 0
    ADD_PRODUCT = 1
    SET_PRODUCT_WEIGHT = 2
    SET_TODAY_CALORIES = 3
    SET_PRODUCT_CALORIES_PER_HUNDRED = 4
    SET_PRODUCT_NAME = 5
    PHOTO = 6
    SET_NEW_PRODUCT_CALORIES = 7
    SAVE_NEW_PRODUCT = 8