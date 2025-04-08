from functools import wraps
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return f"An error occurred: {str(e)}"
    return wrapper

def truncate_log_file(filepath='app.log', max_lines=1000):
    try:
        with open(filepath, 'r+') as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                f.seek(0)
                f.writelines(lines[-max_lines:])
                f.truncate()
    except Exception as e:
        logging.warning(f'Log cleanup failed: {str(e)}')
