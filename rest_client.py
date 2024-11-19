import json
import requests
import numpy as np
import cv2
from utils import encode_img
import random
from glob import glob
import base64


def get_random_img(size=(512, 512, 1)):
    return np.random.randint(0, 256, size, np.uint8)


# download test
if 0:
    data = dict(
        bucket_name = "storage",
        prefix = "job_data/test_tool/20240720",
    )
    result = requests.post("http://127.0.0.1:12030/list_objects", data=json.dumps(data))
    result = result.json()
    if result["code"] == 0:
        print(result["message"])
        print(f'Get {len(result["objects"])} objects.')
        [print(obj, tag) for obj, tag in zip(result["objects"], result["tags"])]
    else:
        print(result["message"])

if 0:   
    data = dict(
        tool_name = "test_tool",
        prefix = "20240720",
    )
    result = requests.post("http://127.0.0.1:12030/download_folder", data=json.dumps(data))
    result = result.json()
    if result["code"] == 0:
        print(result["message"])
        print(f'Get {len(result["images"])} images.')
    else:
        print(result["message"])
        
# upload test
if 0:
    n = 300
    images = [np.random.randint(0, 256, (512, 512, 3), np.uint8) for _ in range(n)]
    images = [cv2.resize(img, (512, 512)) for img in images]
    
    tags = [{} for _ in range(n)]
    for i in range(n):
        tags[i]["DefectID"] = i // 3
        tags[i]["Channel"] = i % 3
        tags[i]["XREL"] = random.uniform(-100, 100)
        tags[i]["YREL"] = random.uniform(-100, 100)
        tags[i]["XINDEX"] = random.randint(-100, 100)
        tags[i]["YINDEX"] = random.randint(-100, 100)
        tags[i]["ADCClass"] = "NV99"
        tags[i]["ManualClass"] = "NV99"
        
    data = dict(
        bucket_name_list = ["test"]*n,
        object_name_list = [f"20240720/image_{i}.bmp" for i in range(n)],
        imagedata_list = [encode_img(img) for img in images],
        tag_list = tags,
        
    )
    result = requests.post("http://127.0.0.1:12030/upload_images", data=json.dumps(data))
    result = result.json()
    print(result["message"])
    
# set tag test
if 0:
    # for i in range(300):
    #     data = dict(
    #         tool_name = "test_tool",
    #         prefix = f"20240720/image_{i}",
    #         tag = dict(test=10),
    #     )
    #     result = requests.post("http://127.0.0.1:12030/set_image_tag", data=json.dumps(data))
    #     result = result.json()
    #     print(result["message"])
    
    data = dict(
        tool_name_list = ["test_tool"]*300,
        prefix_list = [f"20240720/image_{i}" for i in range(300)],
        tag_list = [dict(test=i) for i in range(300)],
    )
    result = requests.post("http://127.0.0.1:12030//set_image_list_tag", data=json.dumps(data))
    result = result.json()
    print(result["message"])
    
# upload / download file test
if 1:
    # Upload / download tif file
    with open(r"D:\ToDesk.exe", "rb") as f:
        file_data = f.read()
        
    file_data = base64.b64encode(file_data).decode('utf-8')
    
    data = dict(
        filedata_list = [file_data],
        tag_list = dict(test=2),
        bucket_name_list = ["storage"],
        object_name_list = ["backup/Space_Oddity.mp3"],
        is_base64_list = [True],
    )
    data = json.dumps(data)
    code = requests.post("http://localhost:12030/upload_files", data=data).json()["code"]
    if code == 0:
        print("Upload file success.")
    else:
        print("Upload file failed.")
    
    # data = dict(
    #     bucket_name = "tool1",
    #     file_path = "backup/Space_Oddity.mp3",
    #     is_base64 = True,
    # )
    
    # result = requests.post("http://localhost:12030/download_file", data=json.dumps(data)).json()
    # file_data = result["file_data"]
    # file_data = base64.b64decode(file_data)
    # with open("Space_Oddity_1.mp3", "wb") as f:
    #     f.write(file_data)
    # print(result["message"])
    
    