import io
from dataclasses import dataclass

from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from .proc import select_process, ProcParam

app = FastAPI()


### ========== CORS ========== ###

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


### ========== DATACLASS ========== ###

@dataclass
class ImgConfig:
    exts: tuple = ("image/png",
                   "image/jpeg",
                   "image/webp",
                   "image/bmp",
                   "image/tiff")
    
    datasize: int = 5 * 1024 * 1024

temp_param = ProcParam(101, 1) 



### ========== FUNCTION ========== ###


def decode_byte_image(image_bytes:bytes) -> np.ndarray|None:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def check_image_extension(file: UploadFile, img_config: ImgConfig) -> bool:
    file_ext = file.content_type

    if file_ext in img_config.exts:
        return True
    else:
        return False

    


### ========== API ========== ###


@app.post("/api/process-image")
async def process_image(
    file: UploadFile = File(...),
    mode: str = Form(...)
):    
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="empty file")
    
    img_cfg = ImgConfig()
    ext_is_ok = check_image_extension(file, img_cfg)
    if  not ext_is_ok:
        raise HTTPException(status_code=400, detail="not allowed image extension")
    if len(image_bytes) > img_cfg.datasize:
        raise HTTPException(status_code=413, detail="file size is over 5MB")
    
    img = decode_byte_image(image_bytes)
    if img is None:
        raise HTTPException(status_code=400, detail="failed to decode image")
       
    #shape = img.shape

    try:
        result_image = select_process(mode, img, temp_param)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_is_ok, result_bytes_image = cv2.imencode(".png", result_image)
    if not encode_is_ok:
        raise HTTPException(status_code=500, detail="encode error: processed image")

    return Response(content=io.BytesIO(result_bytes_image).getvalue(), media_type="image/png")




