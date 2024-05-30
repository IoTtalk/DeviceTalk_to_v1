import logging

from colorama import (
    Fore,
    Style,
    init,
)


__all__ = [
    'color_log',
]

init()


def color_log(log_record: logging.LogRecord):
    log_record.levelname_color_sequence = ''
    log_record.reset_color_sequence = Style.RESET_ALL
    log_record.msg_color_sequence = Fore.GREEN + Style.BRIGHT

    if log_record.levelno == logging.ERROR:
        log_record.levelname_color_sequence = Fore.MAGENTA + Style.BRIGHT
        log_record.reset_color_sequence = Style.RESET_ALL
        log_record.msg_color_sequence = Fore.MAGENTA + Style.BRIGHT
    elif log_record.levelno == logging.WARNING:
        log_record.levelname_color_sequence = Fore.RED
        log_record.reset_color_sequence = Style.RESET_ALL
        log_record.msg_color_sequence = Fore.RED + Style.BRIGHT

    return True
