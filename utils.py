import os, sys
from flask_jwt_extended import jwt_required
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MySQLConfig
import ipaddress
from flask import jsonify, request
from loguru import logger
import time, functools
import cv2
import base64
import numpy as np
import hashlib
from datetime import timedelta
import mysql.connector
from mysql.connector import Error


default_log_path = os.path.join(sys.path[0], "log")

def set_log_level(console_level="INFO", file_level="DEBUG", log_path=default_log_path):
    log_format = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>'
    logger.remove()
    if console_level.upper() in ["DEBUG", "INFO", "ERROR"]:
        logger.add(sys.stdout,  format=log_format, level=console_level, enqueue=True)
        logger.debug(f"Set console log level to {console_level}.")
    if file_level.upper() in ["DEBUG", "INFO", "ERROR"]:
        logger.add(os.path.join(log_path, "log_file/log_{time:YYYY_MM_DD}.log"), rotation="23:59",format=log_format, level=file_level, enqueue=True)
        logger.debug(f"Set file log level to {file_level}.")

def count_time(fn):
    @functools.wraps(fn)
    def wrapper(*args,**kw):
        logger.info(f'+-+-+-+-+ Function {fn.__module__}::{fn.__name__}(..) started. +-+-+-+-+')
        t1=time.perf_counter()
        result = fn(*args,**kw)
        t2=time.perf_counter()
        logger.success(f'+-+-+-+-+ Function {fn.__module__}::{fn.__name__}(..) ended. Cost {round(t2-t1, 6)}s +-+-+-+-+')
        return result
    return wrapper

def kill_port(port):
    find_port = f'netstat -aon | findstr {port}'
    result = os.popen(find_port).read()
    pid = result.split("\n")[0][-6:]
    if pid:
        print(result)
        find_kill = f'taskkill -f -pid {pid}'
        os.popen(find_kill)
        return True
    else:
        return False

def get_ip_whitelist():
    query = "SELECT * FROM erm_db.allowed_ip_table"
    result = execute_query(query)
    ip_whitelist = [item[1] for item in result]
    return ip_whitelist
    

def ip_in_whitelist(client_ip):
    ip = ipaddress.ip_address(client_ip)
    for ip_range in get_ip_whitelist():
        if ip in ipaddress.ip_network(ip_range):
            return True
    return False

def ip_whitelist(f):
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        if not ip_in_whitelist(client_ip):
            return jsonify({'message': 'Access forbidden: IP address not allowed'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def conditional_jwt(enabled_jwt=False):
    def decorator_wrapper(func):
        if enabled_jwt:
            return jwt_required(func)
        else:
            return func
    return decorator_wrapper

def decode_img(base64_data):
    img_data = base64.b64decode(base64_data)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

def encode_img(img):
    if img is None:
        return None
    img_data = cv2.imencode(".bmp", img)[1]
    base64_data = base64.b64encode(img_data)
    # bytes to str
    base64_data = str(base64_data, encoding="utf-8")
    return base64_data

def isImage(fn):
    ext = os.path.splitext(fn)[-1].lower()
    return ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

def execute_query(query):
    try:
        config = MySQLConfig()
        connection = mysql.connector.connect(user=config.user, password=config.password, host=config.host, database=config.database, raise_on_warnings=config.raise_on_warnings)
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
    except Error as e:
        logger.error(f"Error: {e}")
        raise Exception("Error: Cannot get JWT config")
    return result

def generate_md5_hash(str):
    return hashlib.md5(str.encode()).hexdigest()

def get_jwt_config():
    query = "SELECT * FROM erm_db.jwt_config_table"
    result = execute_query(query)
    
    result_dict = {item[1]: item[2] for item in result}
    
    class JWTConfig:
        def __init__(self):
            self.SECRET_KEY = generate_md5_hash(result_dict['SECRET_KEY'])
            
            self.JWT_SECRET_KEY = generate_md5_hash(result_dict['JWT_SECRET_KEY'])
            
            timedelta_str = result_dict['JWT_ACCESS_TOKEN_EXPIRES']
            k, v = timedelta_str.split('=')
            self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(**{k: int(v)})
    
    return JWTConfig()