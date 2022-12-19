import os  
import cv2 
import numpy as np
import subprocess
from pathlib import Path
from PIL import Image
import math 
from subprocess import DEVNULL

def get_image_names(data_path):
    files = os.listdir(data_path)
    files = [i \
        if not (i.startswith('Mask') and not i.startswith('R_mirror')) \
        else os.remove(os.path.join(data_path,i)) \
        for i in files ]
    frame_numbers = [int(i.split('.')[0]) for i in files]
    sort_id = np.argsort(frame_numbers)
    files = [os.path.join(data_path,files[i]) for i in sort_id]
    return files

def make_movies_out_of_images(images, video_name,folderi,left_led_postion,center_led_position,right_led_position):
    stimulus = []
    xL,yL,wL,hL = left_led_postion
    xC,yC,wC,hC = center_led_position
    xR,yR,wR,hR = right_led_position
    if len(images)==0:
        return
    frame = cv2.imread(images[0])
    height, width, _ = frame.shape
    video = cv2.VideoWriter(video_name, 0, 40, (width, height))
    for idx, _ in enumerate(images):
        frame = cv2.imread(images[idx])
        video.write(frame)
        cropped_l = frame[yL:yL + hL, xL:xL + wL]  # both opencv and numpy are "row-major", so y goes first
        cropped_r = frame[yR:yR + hR, xR:xR + wR]  # both opencv and numpy are "row-major", so y goes first
        cropped_c = frame[yC:yC + hC, xC:xC + wC]  # both opencv and numpy are "row-major", so y goes first
        stimulus.append([np.mean(cropped_l),np.mean(cropped_c),np.mean(cropped_r)])
    video.release()
    return np.array(stimulus)
    
def convert_video(video_input, video_output):
    cmds = ['ffmpeg', '-i', video_input, video_output,'-hide_banner','-loglevel','error']
    subprocess.Popen(cmds, shell=False, stdout=DEVNULL)  

def Mask(frame2,sigma):
    [x1,x2,_]=frame2.shape
    center = [x1 ,x1/2]
    x = np.arange(0, x1, 1, float)
    y = x[:,np.newaxis]
    if center is None:
        x0 = y0 = x1 // 2
    else:
        x0 = center[0]
        y0 = center[1]
    g=np.exp(-4*np.log(2) * ((x-x0)**2 + (y-y0)**2) / sigma**2) 
    g=np.delete(g, list(range(x1-x2)), 1)
    y = np.expand_dims(g, axis=3)
    y=np.repeat(y,3,axis=2)
    a = np.array(frame2, dtype=float)
    a = a*(1-y)
    img = a.astype(np.uint8)
    return(img)

   
def get_mask_mirror_names(mainfolder):
    Xfiles = [os.path.join(mainfolder,f) for f in os.listdir(mainfolder) if f.endswith('L.avi') and not f.startswith('Mask') and not f.startswith('Mirror') ] # find all files with R.avi as file name
    Xfiles2 = [Path(f) for f in Xfiles] # make each file name path to extract the parents and anme
    XfilesL = [os.path.join(f.parents[0],'Mask'+f.name) for f in Xfiles2] # creat a same as files but with Mirror added to the file names
    Xfiles = [os.path.join(mainfolder,f) for f in os.listdir(mainfolder) if f.endswith('R.avi') and not f.startswith('Mask') and not f.startswith('Mirror') ] # find all files with R.avi as file name
    Xfiles2 = [Path(f) for f in Xfiles] # make each file name path to extract the parents and anme
    XfilesR = [os.path.join(f.parents[0],'Mirror'+f.name) for f in Xfiles2] # creat a same as files but with Mirror added to the file names
    return XfilesL,XfilesR

def Copyvideodata(source, destination):
    cmds = ['rsync', '-avz','--exclude','*.avi', source,'/',destination,'/']
    subprocess.Popen(cmds)     

def make_movies_out_of_imagesNocropp(images, video_name,folderi):
    frame = cv2.imread(images[0])
    height, width, _ = frame.shape
    video = cv2.VideoWriter(video_name, 0, 40, (width, height))
    for idx, _ in enumerate(images):
        frame = cv2.imread(images[idx])
        video.write(frame)
    video.release()
    cv2.destroyAllWindows()

def smooth_data_convolve_my_average(arr, span):
    import numpy as np
    re = np.convolve(arr, np.ones(span * 2 + 1) / (span * 2 + 1), mode="same")
    re[0] = np.average(arr[:span])
    for i in range(1, span + 1):
        re[i] = np.average(arr[:i + span])
        re[-i] = np.average(arr[-i - span:])
    return re
    
def crop_rotated(rotated,frame,Angle,i,df):
    def add_margin(pil_img, top, right, bottom, left, color):
        width, height = pil_img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(pil_img.mode, (new_width, new_height), color)
        result.paste(pil_img, (left, top))
        return result
    img = Image.fromarray(rotated, 'RGB')
    Newrotated=np.uint8(add_margin(img, 400, 400, 400, 400, (0,0,0)))
    Alpharad = math.radians(math.degrees(Angle[i])-90+180);
    P = [df.Nosey[i] ,df.Nosex[i]]
    c, s = np.cos(Alpharad),np.sin(Alpharad)
    RotMatrix = np.array(((c, -s), (s, c)))
    ImCenterA = np.array(frame.shape[0:2])/2       # Center of the main image
    ImCenterB = np.array(Newrotated.shape[0:2])/2  # Center of the transformed image
    RotatedP =RotMatrix.dot(P-ImCenterA)+ImCenterB;
    midpoint= 350;
    sizetotal = 700;
    ratsiosize = 1.1;
    y= int(RotatedP[0]-midpoint);
    x= int(RotatedP[1]-midpoint*ratsiosize);
    h = sizetotal
    w = int(sizetotal*ratsiosize)
    crop_img = Newrotated[y:y+h, x:x+w]
    return crop_img

def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

