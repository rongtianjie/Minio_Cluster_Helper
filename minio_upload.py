from minio import Minio
from minio.commonconfig import Tags
import numpy as np
import cv2
import io 
import os
from tqdm import tqdm, trange
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
import mimetypes
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter
from config import Config
from minio_download import *


# load config
config = Config()
    
minioClient = Minio(
    f'{config.minio_url}:{config.minio_port}',
    access_key=config.access_key,
    secret_key=config.secret_key,
    secure=False
)
expiration_days = config.backup_expiration_days


def upload_single_image(bucket_name, object_name, image, new_tag):
    # get extension from path
    _, ext = os.path.splitext(object_name)
    image_data = cv2.imencode(ext, image)[1].tobytes()
    content_type = mimetypes.guess_type(os.path.basename(object_name))[0]
    
    tags = Tags.new_object_tags()
    if not new_tag is None:
        for key, value in new_tag.items():
            tags[key] = str(value)
    if len(tags) > 10:
        raise ValueError("The number of tags exceeds the limit.")
    
    # upload raw image
    minioClient.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=io.BytesIO(image_data),
        length=len(image_data),
        content_type=content_type,
        tags=tags,
    )
    
    logger.debug(f"Image {bucket_name}:{object_name} uploaded.")
    return 0


@count_time
def upload_images(bucket_name_list, object_name_list, image_list, tag_list):
    if len(image_list) != len(tag_list) or len(image_list) != len(bucket_name_list) or len(image_list) != len(object_name_list):
        raise ValueError(f"The length of image_list({len(image_list)}), tag_list({len(tag_list)}), bucket_name_list({len(bucket_name_list)}) and object_name_list({len(object_name_list)}) should be the same.")
    
    # Check bucket existence
    bucket_name_unique = list(set(bucket_name_list))
    for bucket_name in bucket_name_unique:
        check_bucket(bucket_name)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        image_num = len(image_list)
        logger.info(f"Uploading {image_num} images...")
        with tqdm(total=image_num, ncols=80) as pbar:
            futures = [executor.submit(upload_single_image, bucket_name, object_name, image, tag) for bucket_name, object_name, image, tag in zip(bucket_name_list, object_name_list, image_list, tag_list)]
            for future in as_completed(futures):
                _ = future.result()
                pbar.update(1)
    return 0


def set_object_tag(bucket_name, object_name, tag):
    tag_ori = minioClient.get_object_tags(bucket_name, object_name)
    
    logger.debug(f"Original tags: {tag_ori}")
    if tag_ori is None:
        tag_ori = Tags.new_object_tags()
    for key, value in tag.items():
        tag_ori[key] = str(value)
    logger.debug(f"New tags: {tag_ori}")
    if len(tag_ori) > 10:
        raise ValueError("The number of tags exceeds the limit.")
    
    minioClient.set_object_tags(bucket_name, object_name, tag_ori)
    logger.debug(f"Tags set for {bucket_name}:{object_name}")
    return 0


@count_time
def set_objects_tag(bucket_name_list, object_name_list, tag_list):
    if len(object_name_list) != len(tag_list) or len(object_name_list) != len(bucket_name_list):
        raise ValueError(f"The length of object_name_list({len(object_name_list)}) and tag_list({len(tag_list)}) should be the same.")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        object_num = len(object_name_list)
        logger.info(f"Setting tags for {object_num} images...")
        with tqdm(total=object_num, ncols=80) as pbar:
            futures = [executor.submit(set_object_tag, bucket_name, object_name, tag) for bucket_name, object_name, tag in zip(bucket_name_list, object_name_list, tag_list)]
            for future in as_completed(futures):
                _ = future.result()
                pbar.update(1)
    return 0


def upload_file(bucket_name, object_name, file_data, tag):
    tags = Tags.new_object_tags()
    if not tag is None:
        for key, value in tag.items():
            tags[key] = str(value)
        
    content_type = mimetypes.guess_type(os.path.basename(object_name))[0]
    if content_type is None:
        content_type = "application/octet-stream"
    logger.debug(f"Content type: {content_type}")
    
    minioClient.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
        tags=tags,
    )
    
    logger.debug(f"File {bucket_name}:{object_name} uploaded.")
    return 0


@count_time
def upload_file_list(bucket_name_list, object_name_list, file_data_list, tag_list):
    if len(file_data_list) != len(tag_list) or len(file_data_list) != len(bucket_name_list) or len(file_data_list) != len(object_name_list):
        raise ValueError(f"The length of file_data_list({len(file_data_list)}), tag_list({len(tag_list)}), bucket_name_list({len(bucket_name_list)}) and object_name_list({len(object_name_list)}) should be the same.")
    
    # Check bucket existence
    bucket_name_unique = list(set(bucket_name_list))
    for bucket_name in bucket_name_unique:
        check_bucket(bucket_name)
        
    with ThreadPoolExecutor(max_workers=8) as executor:
        file_num = len(file_data_list)
        logger.info(f"Uploading {file_num} files...")
        with tqdm(total=file_num, ncols=80) as pbar:
            futures = [executor.submit(upload_file, bucket_name, object_name, file_data, tag) for bucket_name, object_name, file_data, tag in zip(bucket_name_list, object_name_list, file_data_list, tag_list)]
            for future in as_completed(futures):
                _ = future.result()
                pbar.update(1)
    return 0


def check_bucket(bucket_name):
    found = minioClient.bucket_exists(bucket_name)
    if not found:
        logger.warning(f"Bucket {bucket_name} not found, creating...")
        minioClient.make_bucket(bucket_name)
        logger.info(f"Bucket {bucket_name} created.")
    else:
        pass


def set_bucket_lifecycle(bucket_name, prefix="backup/", expiration_days=0):
    if expiration_days > 0:
        exp_config = LifecycleConfig(
            [
                Rule(
                    rule_id=f"{bucket_name}:{prefix}-{expiration_days}",
                    status="Enabled",
                    rule_filter=Filter(prefix=prefix),
                    expiration=Expiration(days=expiration_days)
                ),
            ],
        )
        minioClient.set_bucket_lifecycle(bucket_name, exp_config)
        logger.info(f"Set expiration for {bucket_name}:{prefix}-{expiration_days} days")
    else:
        logger.debug(f"Expiration days less than 1, skip setting lifecycle.")
    return 0


def generate_thumbnail(src_bucket_name, src_object_name, dst_bucket_name, dst_object_name, thumbnail_size=128):
    check_bucket(dst_bucket_name)
    
    result = download_single_image(src_bucket_name, src_object_name)
    image = result["image_data"]
    tags = result["tags"]
    
    thumbnail= cv2.resize(image, (thumbnail_size, thumbnail_size), interpolation=cv2.INTER_AREA)
    
    tags["thumbnail_url"] = f"{dst_bucket_name}:{dst_object_name}"
    tags["raw_url"] = f"{src_bucket_name}:{src_object_name}"
    set_object_tag(src_bucket_name, src_object_name, tags)
    
    upload_single_image(dst_bucket_name, dst_object_name, thumbnail, tags)
    
    logger.debug(f"Thumbnail {src_bucket_name}:{src_object_name} -> {dst_bucket_name}:{dst_object_name} generated.")
    return 0


@count_time
def generate_folder_thumbnail(src_bucket_name, src_path, dst_bucket_name, dst_path, thumbnail_size=128):
    check_bucket(dst_bucket_name)
    
    list_result = list_objects(src_bucket_name, src_path)
    src_object_names = [res["object_name"] for res in list_result]
    src_bucket_names = [src_bucket_name] * len(list_result)
    
    dst_object_names = [f"{dst_path}/{res['object_name'].split('/')[-1]}" for res in list_result]
    dst_bucket_names = [dst_bucket_name] * len(list_result)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        object_num = len(list_result)
        logger.info(f"Generating thumbnails for {object_num} images...")
        with tqdm(total=object_num, ncols=80) as pbar:
            futures = [executor.submit(generate_thumbnail, src_bucket_name, src_object_name, dst_bucket_name, dst_object_name, thumbnail_size) for src_bucket_name, src_object_name, dst_bucket_name, dst_object_name in zip(src_bucket_names, src_object_names, dst_bucket_names, dst_object_names)]
            for future in as_completed(futures):
                _ = future.result()
                pbar.update(1)
    return 0
    
                
if __name__ == '__main__':
    # 定义要上传的NumPy数组图片
    n=10000
    
    images=[]
    for i in range(n):
        image_raw = np.random.randint(0, 255, size=(512, 512), dtype=np.uint8)  # 这里随机生成一个大小为512x512的图片
        image_thumbnail = cv2.resize(image_raw, (32, 32))  # 将图片缩小为32x32的缩略图
        tags = dict(tag="tag1")
        images.append(image_raw)
    
    # _ = upload_images(images, [tags]*n, ["dev"]*n, [f"test/image{i}" for i in range(n)])
    _ = upload_single_image(image_raw, tags, "dev", "test/image0")