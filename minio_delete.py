from minio import Minio
from minio.deleteobjects import DeleteObject
from tqdm import tqdm, trange
from loguru import logger
from config import Config


# load config
config = Config()
    
minioClient = Minio(
    f'{config.minio_url}:{config.minio_port}',
    access_key=config.access_key,
    secret_key=config.secret_key,
    secure=False
)


def delete_file(bucket_name, object_name):
    # check if the object exists
    if minioClient.bucket_exists(bucket_name):
        minioClient.remove_object(bucket_name, object_name)
        logger.debug(f"Image {bucket_name}:{object_name} deleted.")
    else:
        logger.warning(f"Object {bucket_name}:{object_name} does not exist.")
    return 0


def delete_files(bucket_name_list, object_name_list):
    if len(bucket_name_list) != len(object_name_list):
        raise ValueError(f"The length of bucket_name_list({len(bucket_name_list)}) and object_name_list({len(object_name_list)}) should be the same.")
    
    bucket_name_unique = list(set(bucket_name_list))
    delete_dict = {}
    for bucket_name in bucket_name_unique:
        delete_dict[bucket_name] = []
    for bucket_name, object_name in zip(bucket_name_list, object_name_list):
        delete_dict[bucket_name].append(DeleteObject(object_name))
    
    for bucket_name, delete_object_list in tqdm(delete_dict.items()):
        errors = minioClient.remove_objects(bucket_name, delete_object_list)
        for error in errors:
            logger.warning(f"Error occurred when deleting {bucket_name}:{error.object_name}: {error.message}")
    logger.debug(f"Delete {len(object_name_list)} objects completed.")
    return 0


def delete_folder(bucket_name, prefix):
    if not prefix.endswith("/"):
        prefix += "/"
    delete_object_list = map(
        lambda obj: DeleteObject(obj.object_name),
        minioClient.list_objects(bucket_name, prefix=prefix, recursive=True)
    )
    errors = minioClient.remove_objects(bucket_name, delete_object_list)
    for error in errors:
        logger.warning(f"Error occurred when deleting {bucket_name}:{error.object_name}: {error.message}")
    logger.debug(f"Delete {bucket_name}:{prefix} completed.")
    return 0