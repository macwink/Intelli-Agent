from functools import wraps
import time

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from .logger_utils import get_logger

logger = get_logger(__name__)


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # first item in the args, ie `args[0]` is `self`
        # logger.info(
        #     f'Function {func.__name__} {str(args)} {str(kwargs)[:32]} Took {total_time:.4f} seconds\n')
        logger.info(
            f'Function {func.__name__} Took {total_time:.4f} seconds\n')
        return result
    return timeit_wrapper


def get_china_now():
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai'
    )
    # 协调世界时
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return utc_now.date()
