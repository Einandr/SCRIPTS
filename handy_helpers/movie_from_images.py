import cv2
import os


path = r'D:\SIM\2022_KTRV\01_sks4\hot_fr\pic\\'
dir = 'rot_Y_O2'
video_name = 'video.mp4'

workdir = ''.join((path, dir, '\\'))

os.chdir(workdir)

images = [img for img in os.listdir(workdir) if img.endswith('.jpeg')]
images.sort(key=lambda i: os.path.getmtime(i))



frame = cv2.imread(os.path.join(workdir, images[0]))
height, width, layers = frame.shape

video = cv2.VideoWriter(video_name, 0, 25, (width,height))

for image in images:
    video.write(cv2.imread(os.path.join(workdir, image)))

cv2.destroyAllWindows()
video.release()
