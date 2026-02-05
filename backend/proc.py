from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ProcParam:
    ksize: int
    direction: int


def gray_img(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray

def blur_img(img: np.ndarray, ksize: int) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (ksize, ksize), 0)
    return blur

def flip_img(img: np.ndarray, direction: int ) -> np.ndarray:
    flip = cv2.flip(img, direction)
    return flip

def select_process(proc_type: str, img: np.ndarray, param: ProcParam) -> np.ndarray:
    if proc_type == "gray":
        proc_img = gray_img(img)
    
    elif proc_type == "blur":
        proc_img = blur_img(img, param.ksize)
    
    elif proc_type == "flip":
        proc_img = flip_img(img, param.direction)
    
    else :
        raise ValueError(f"unknown proc_type: {proc_type}")

    return proc_img


def main():
    img_dir = "./Sample_1.png"
    img_src = cv2.imread(img_dir)

    P = ProcParam(51, 1)
    #print(type(P.ksize))
    proc_type = "blur"

    result_img = select_process(proc_type, img_src, P)

    cv2.imwrite("result.png", result_img)


if __name__ == "__main__":
    main()