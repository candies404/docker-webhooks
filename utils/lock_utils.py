import os
import platform
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 根据操作系统选择锁实现
if platform.system() == 'Windows':
    import msvcrt


    def file_lock(file):
        try:
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except IOError:
            return False


    def file_unlock(file):
        try:
            msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        except IOError:
            pass
else:
    import fcntl


    def file_lock(file):
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            return False


    def file_unlock(file):
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        except IOError:
            pass

# 锁文件目录
LOCKS_DIR = '/tmp/locks'
os.makedirs(LOCKS_DIR, exist_ok=True)


def get_deploy_lock(project):
    """获取项目的文件锁"""
    lock_file = f'{LOCKS_DIR}/{project}.lock'
    return open(lock_file, 'w')


def get_last_deploy_time(project):
    """获取项目最后部署时间"""
    status_file = f'{LOCKS_DIR}/{project}.status'
    try:
        mtime = os.path.getmtime(status_file)
        return datetime.fromtimestamp(mtime)
    except OSError:
        return None


def update_deploy_time(project):
    """更新项目部署时间"""
    status_file = f'{LOCKS_DIR}/{project}.status'
    with open(status_file, 'w') as f:
        f.write(datetime.now().isoformat())
