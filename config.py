class Config:
    port = 12030
    enable_jwt = False
    
    # MinIO server configuration
    minio_url= "host.docker.internal"
    minio_port = 9000
    access_key = "minio"
    secret_key = "minioadmin"
    backup_expiration_days = 0
    
    # Bucket / Folder names defined in MinIO
    # storage_bucket = "storage"
    # job_data_subfolder = "job_data"
    # datasets_subfolder = "datasets"
    # model_subfolder = "models"
    # database_subfolder = "database"

class MySQLConfig:
    user = 'root'
    password = 'root'
    host = 'host.docker.internal'
    database = 'erm_db'
    raise_on_warnings = True