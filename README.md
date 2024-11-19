# MinIO Server Rest API (Port 10000)

## Index
- [MinIO Server Rest API (Port 10000)](#minio-server-rest-api-port-10000)
  - [Index](#index)
  - [API](#api)
    - [Upload Single Image](#upload-single-image)
    - [Upload Image List](#upload-image-list)
    - [Set Image Tag](#set-image-tag)
    - [List Objects](#list-objects)
    - [Download Single Image](#download-single-image)
    - [Download Image List](#download-image-list)
    - [Download Folder](#download-folder)

## API
### Upload Single Image
- **URL**
  `Host_IP:10000/upload_single_image`
  
- **Data**
  - `image`: Base64 encoded image
  - `tag`: Image tag (Dictionary)
  - `bucket_name`: Bucket name
  - `prefix`: Image save path without extension

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message

### Upload Image List
- **URL**
  `Host_IP:10000/upload_images`

- **Data**
  - `images`: List of Base64 encoded images
  - `tags`: List of image tags (List of Dictionary)
  - `bucket_names`: List of bucket name
  - `prefixes`: List of image save path without extension

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message

### Set Image Tag
- **URL**
  `Host_IP:10000/set_image_tag`

- **Data**
  - `bucket_name`: Bucket name
  - `prefix`: Image save path without extension
  - `tag`: Image tag (Dictionary)

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message

### List Objects
- **URL**
  `Host_IP:10000/list_objects`

- **Data**
  - `bucket_name`: Bucket name
  - `prefix`: Path in bucket

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message
  - `objects`: List of object names under path
  - `tags`: List of tags of objects

### Download Single Image
- **URL**
  `Host_IP:10000/download_single_image`

- **Data**
  - `bucket_name`: Bucket name
  - `prefix`: Image save path without extension
  - `isThumbnail`: Whether to download thumbnail (Boolean)

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message
  - `image`: Base64 encoded image
  - `tag`: Image tag (Dictionary)

### Download Image List
- **URL**
  `Host_IP:10000/download_images`

- **Data**
  - `bucket_names`: List of bucket name
  - `prefixes`: List of image save path without extension
  - `isThumbnail`: Whether to download thumbnail (Boolean)

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message
  - `images`: List of Base64 encoded images
  - `tags`: List of image tags (List of Dictionary)

### Download Folder
- **URL**
  `Host_IP:10000/download_folder`

- **Data**
  - `bucket_name`: Bucket name
  - `prefix`: Folder path
  - `isThumbnail`: Whether to download thumbnail (Boolean)

- **Response**
  - `code`: 0 (Success) or others (Failed)
  - `message`: "Success" or error message
  - `images`: List of Base64 encoded images
  - `tags`: List of image tags (List of Dictionary)


  