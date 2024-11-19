from minio import Minio
from minio.commonconfig import CopySource
import numpy as np
import cv2
from tqdm import tqdm
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from utils import count_time, isImage


# load config
config = Config()
    
minioClient = Minio(
    f'{config.minio_url}:{config.minio_port}',
    access_key=config.access_key,
    secret_key=config.secret_key,
    secure=False
)


def get_object_tags(bucket_name, object_name):
    return {"object_name": object_name, "tags": minioClient.get_object_tags(bucket_name, object_name)}

@count_time
def list_objects(bucket_name, prefix, recursive=False):
    if not prefix.endswith("/") and prefix != "":
        prefix += "/"
    if prefix == "/":
        prefix = ""
    objects = minioClient.list_objects(bucket_name, prefix=prefix, recursive=recursive)
    objects = [obj for obj in objects if not obj.object_name.endswith("/")]
    if len(objects) > 0:
        logger.debug(f"Get {len(objects)} objects.")
    else:
        raise Exception(f"No such path: [{bucket_name}:{prefix}] or no objects in the given path.")
    
    result = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        count = len(objects)
        with tqdm(total=count, desc="Getting tags", ncols=80) as pbar:
            futures = [executor.submit(get_object_tags, bucket_name, obj.object_name) for obj in objects]
            for future in as_completed(futures):
                result.append(future.result())
                pbar.update(1)
    logger.debug(f"Get {len(result)} tags.")
    return result


def download_single_image(bucket_name, object_name):
    if isImage(object_name):
        data = minioClient.get_object(bucket_name, object_name).read()
        tag = minioClient.get_object_tags(bucket_name, object_name)
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
        logger.debug(f"Image {bucket_name}:{object_name} downloaded.")
    else:
        logger.warning(f"Object {bucket_name}:{object_name} is not an image.")
        image = None
        tag = minioClient.get_object_tags(bucket_name, object_name)
    return {"object_name": object_name, "image_data": image, "tags": tag}


@count_time
def download_images(bucket_name_list, object_name_list):
    if len(bucket_name_list) != len(object_name_list):
        raise ValueError(f"The length of bucket_name_list({len(bucket_name_list)}) and object_name_list({len(object_name_list)}) should be the same.")
    
    result = []
    logger.debug(f"Downloading {len(bucket_name_list)} images...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        count = len(bucket_name_list)
        with tqdm(total=count, ncols=80) as pbar:
            futures = [executor.submit(download_single_image, bucket_name, object_name) for bucket_name, object_name in zip(bucket_name_list, object_name_list)]
            for future in as_completed(futures):
                result.append(future.result())
                pbar.update(1)
    return result


def download_folder(bucket_name, src_path):
    list_result = list_objects(bucket_name, src_path)
    object_name_list = [res["object_name"] for res in list_result]

    result = download_images([bucket_name]*len(list_result), object_name_list)
    return result


def download_file(bucket_name, object_name):
    if not minioClient.bucket_exists(bucket_name):
        raise ValueError(f"Bucket {bucket_name} does not exist.")
    
    file_data = minioClient.get_object(bucket_name, object_name).read()
    tag = minioClient.get_object_tags(bucket_name, object_name)
    logger.debug(f"File {bucket_name}:{object_name} downloaded.")
    return {"object_name": object_name, "file_data": file_data, "tags": tag}


def download_file_list(bucket_name_list, object_name_list):
    if len(bucket_name_list) != len(object_name_list):
        raise ValueError(f"The length of bucket_name_list({len(bucket_name_list)}) and object_name_list({len(object_name_list)}) should be the same.")
    
    result = []
    logger.debug(f"Downloading {len(bucket_name_list)} files...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        count = len(bucket_name_list)
        with tqdm(total=count, ncols=80) as pbar:
            futures = [executor.submit(download_file, bucket_name, object_name) for bucket_name, object_name in zip(bucket_name_list, object_name_list)]
            for future in as_completed(futures):
                result.append(future.result())
                pbar.update(1)
    return result


def copy_single_object(src_bucket_name, src_object_name, dst_bucket_name, dst_object_name):
    minioClient.copy_object(dst_bucket_name, dst_object_name, CopySource(src_bucket_name, src_object_name))
    logger.debug(f"Object {src_bucket_name}:{src_object_name} copied to {dst_bucket_name}:{dst_object_name}.")
    return 0


@count_time
def copy_object_list(src_bucket_name_list, src_object_name_list, dst_bucket_name_list, dst_object_name_list):
    if len(src_bucket_name_list) != len(src_object_name_list) or len(src_bucket_name_list) != len(dst_bucket_name_list) or len(src_bucket_name_list) != len(dst_object_name_list):
        raise ValueError(f"The length of src_bucket_name_list({len(src_bucket_name_list)}), src_object_name_list({len(src_object_name_list)}), dst_bucket_name_list({len(dst_bucket_name_list)}) and dst_object_name_list({len(dst_object_name_list)}) should be the same.")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        count = len(src_bucket_name_list)
        logger.debug(f"Copying {count} objects...")
        with tqdm(total=count, ncols=80) as pbar:
            futures = [executor.submit(copy_single_object, src_bucket_name, src_object_name, dst_bucket_name, dst_object_name) for src_bucket_name, src_object_name, dst_bucket_name, dst_object_name in zip(src_bucket_name_list, src_object_name_list, dst_bucket_name_list, dst_object_name_list)]
            for future in as_completed(futures):
                _ = future.result()
                pbar.update(1)
    return 0


if __name__ == '__main__':
    # test list_objects
    result = list_objects("dev", "test/")
    # [print(obj.object_name, obj.tags) for obj in objects]
    
    # test download_images
    # n = 100
    # images, tags = download_images(["dev"]*n, [f"test/image{i}" for i in range(n)], isThumbnail=False)
    # cv2.imshow("test", images[0])
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    # images, tags = download_folder("dev", "test", isThumbnail=False)
    # print(images[0].shape)
    # print(tags[0])