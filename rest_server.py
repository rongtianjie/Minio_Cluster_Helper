from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os, sys
import base64
from minio_upload import *
from minio_download import *
from minio_delete import *
from loguru import logger
import traceback
from config import Config
import uvicorn
from utils import set_log_level, decode_img, encode_img, kill_port

# load config
config = Config()

log_path = os.path.join(sys.path[0], "log")
os.makedirs(log_path, exist_ok=True)

set_log_level(console_level="DEBUG", file_level="INFO", log_path=log_path)

app = FastAPI()

@app.post("/upload_images")
async def upload_images_route(request: Request):
    try:
        logger.info(f"Uploading images from {request.client.host}")
        data = await request.json()
        bucket_name_list = data["bucket_name_list"]
        object_name_list = data["object_name_list"]
        image_list = [decode_img(img) for img in data["imagedata_list"]]
        tag_list = data["tag_list"]
        
        code = upload_images(bucket_name_list, object_name_list, image_list, tag_list)
        
        response = dict(
            code = code,
            message = "Upload images success."
        )
        logger.debug(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/upload_files")
async def upload_files_route(request: Request):
    try:
        logger.info(f"Uploading files from {request.client.host}")
        data = await request.json()
        bucket_name_list = data.get("bucket_name_list", [])
        object_name_list = data.get("object_name_list", [])
        filedata_list = data.get("filedata_list", [])
        tag_list_list = data.get("tag_list_list", [None]*len(filedata_list))
        is_base64_list = data.get("is_base64_list", [])
        
        if len(bucket_name_list) != len(object_name_list) or len(bucket_name_list) != len(filedata_list) or len(bucket_name_list) != len(tag_list_list) or len(bucket_name_list) != len(is_base64_list):
            raise ValueError(f"The length of bucket_name_list({len(bucket_name_list)}), object_name_list({len(object_name_list)}), filedata_list({len(filedata_list)}), tag_list_list({len(tag_list_list)}) and is_base64_list({len(is_base64_list)}) should be the same.")
        
        for i in range(len(filedata_list)):
            filedata = filedata_list[i].encode('utf-8')
            if is_base64_list[i]:
                filedata = base64.b64decode(filedata)
            filedata_list[i] = filedata
            
        code = upload_file_list(bucket_name_list, object_name_list, filedata_list, tag_list_list)
        
        response = dict(
            code = code,
            message = "Upload files success."
        )
        logger.debug(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/set_objects_tag")
async def set_objects_tag_route(request: Request):
    try:
        logger.info(f"/set_objects_tag from {request.client.host}")
        data = await request.json()
        bucket_name_list = data["bucket_name_list"]
        object_name_list = data["object_name_list"]
        tag_list = data["tag_list"]
        
        code = set_objects_tag(bucket_name_list, object_name_list, tag_list)
        
        response = dict(
            code = code,
            message = "Set objects tag success."
        )
        logger.debug(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/download_images")
async def download_images_route(request: Request):
    try:
        logger.info(f"/download_images from {request.client.host}")
        data = await request.json()
        bucket_name_list = data["bucket_name_list"]
        object_name_list = data["object_name_list"]
        
        result = download_images(bucket_name_list, object_name_list)
        for i in range(len(result)):
            if result[i]["image_data"] is not None:
                result[i]["image_data"] = encode_img(result[i]["image_data"])
            else:
                result.pop(i)
        
        response = dict(
            code = 0,
            message = "Download images success.",
            result = result
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            result = [],
            message = traceback.format_exc(),
        )
        
    return JSONResponse(content=response)

@app.post("/download_folder")
async def download_folder_route(request: Request):
    try:
        logger.info(f"/download_folder from {request.client.host}")
        data = await request.json()
        bucket_name = data["bucket_name"]
        src_path = data["src_path"]
        
        result = download_folder(bucket_name, src_path)
        for i in range(len(result)):
            result[i]["image_data"] = encode_img(result[i]["image_data"])
        
        response = dict(
            code = 0,
            result = result,
            message = "Download folder success.",
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            result = [],
            message = traceback.format_exc()
        )
        
    return JSONResponse(content=response)

@app.post("/download_files")
async def download_files_route(request: Request):
    try:
        logger.info(f"/download_files from {request.client.host}")
        data = await request.json()
        bucket_name_list = data["bucket_name_list"]
        object_name_list = data["object_name_list"]
        isBase64_list = data.get("isBase64_list", [True]*len(object_name_list))
        
        result = download_file_list(bucket_name_list, object_name_list)
        for i in range(len(result)):
            result[i]["file_data"] = base64.b64encode(result[i]["file_data"]).decode('utf-8') if isBase64_list[i] else result[i]["file_data"].decode('utf-8')
        
        response = dict(
            code = 0,
            message = "Download files success.",
            result = result
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc(),
            result = []
        )
        
    return JSONResponse(content=response)

@app.post("/list_objects")
async def list_objects_route(request: Request):
    try:
        data = await request.json()
        bucket_name = data["bucket_name"]
        src_path = data["src_path"]
        logger.info(f"List objects on {bucket_name}:{src_path} from {request.client.host}")
        
        result = list_objects(bucket_name, src_path)
        
        response = dict(
            code = 0,
            message = "List objects success.",
            result = result
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/delete_files")
async def delete_files_route(request: Request):
    try:
        logger.info(f"/delete_files from {request.client.host}")
        data = await request.json()
        bucket_name_list = data["bucket_name_list"]
        object_name_list = data["object_name_list"]
        
        code = delete_files(bucket_name_list, object_name_list)
        
        response = dict(
            code = code,
            message = "Delete files success."
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/delete_folder")
async def delete_folder_route(request: Request):
    try:
        logger.info(f"/delete_folder from {request.client.host}")
        data = await request.json()
        bucket_name = data["bucket_name"]
        prefix = data["src_path"]
        
        code = delete_folder(bucket_name, prefix)
        
        response = dict(
            code = code,
            message = "Delete folder success."
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/generate_folder_thumbnail")
async def generate_folder_thumbnail_route(request: Request):
    try:
        logger.info(f"/generate_thumbnail from {request.client.host}")
        data = await request.json()
        src_bucket_name = data["src_bucket_name"]
        src_path = data["src_path"]
        dst_bucket_name = data["dst_bucket_name"]
        dst_path = data["dst_path"]
        thumbnail_size = data.get("thumbnail_size", 128)
        
        code = generate_folder_thumbnail(src_bucket_name, src_path, dst_bucket_name, dst_path, thumbnail_size)
        
        response = dict(
            code = code,
            message = "Generate thumbnail success."
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

@app.post("/copy_objects")
async def copy_objects_route(request: Request):
    try:
        logger.info(f"/copy_objects from {request.client.host}")
        data = await request.json()
        src_bucket_name_list = data["src_bucket_name_list"]
        src_object_name_list = data["src_object_name_list"]
        dst_bucket_name_list = data["dst_bucket_name_list"]
        dst_object_name_list = data["dst_object_name_list"]
        
        code = copy_object_list(src_bucket_name_list, src_object_name_list, dst_bucket_name_list, dst_object_name_list)
        
        response = dict(
            code = code,
            message = "Copy objects success."
        )
        logger.success(response["message"])
    except:
        logger.error(traceback.format_exc())
        response = dict(
            code = -1,
            message = traceback.format_exc()
        )
    return JSONResponse(content=response)

def main():
    port = config.port
    logger.info(f"Starting minIO helper")
    
    if kill_port(port):
        logger.warning(f"Port {port} is killed and start a new one")
    else:
        logger.info(f"Start port {port}")
    
    uvicorn.run("rest_server:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == '__main__':
    main()
