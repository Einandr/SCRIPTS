# importing libraries
import os
import cv2
from PIL import Image

path = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\QUBIQ\T1000K_freq10000_comb_v0.0ms_pmfr0.00000179\movies\y_cp'
workdir = 'resized'
video_name = 'video.mp4'

# crop_xmin_persent = 15
# crop_xmax_persent = 92
# crop_ymin_persent = 55
# crop_ymax_persent = 85

# (crop_xmin_persent, crop_xmax_persent, crop_ymin_persent, crop_ymax_persent) = (15, 92, 55, 88)
# (crop_xmin_persent, crop_xmax_persent, crop_ymin_persent, crop_ymax_persent) = (22, 88, 59, 78)
(crop_xmin_persent, crop_xmax_persent, crop_ymin_persent, crop_ymax_persent) = (0, 100, 0, 100)

# (crop_xmin_persent, crop_xmax_persent, crop_ymin_persent, crop_ymax_persent) = (20, 92, 36, 56)


os.chdir(path)
if not os.path.exists(workdir):
    os.mkdir(workdir)

mean_height = 0
mean_width = 0
num_of_images = 0

for file in os.listdir('.'):
    if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith("png"):
        num_of_images += 1
        im = Image.open(os.path.join(path, file))
        width, height = im.size
        mean_width += width
        mean_height += height

mean_width = int(mean_width / num_of_images)
mean_height = int(mean_height / num_of_images)


for file in os.listdir('.'):
    if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith("png"):
        im = Image.open(os.path.join(path, file))
        width, height = im.size
        crop_xmin_picsels = width * crop_xmin_persent // 100
        crop_xmax_picsels = width * crop_xmax_persent // 100
        crop_ymin_picsels = height * crop_ymin_persent // 100
        crop_ymax_picsels = height * crop_ymax_persent // 100
        # print(crop_xmin_picsels, crop_xmax_picsels, crop_ymin_picsels, crop_ymax_picsels)
        # print(width, height)
        im = im.resize((mean_width, mean_height), Image.Resampling.LANCZOS)
        im = im.crop((crop_xmin_picsels, crop_ymin_picsels, crop_xmax_picsels, crop_ymax_picsels))
        im.save(''.join((path, '\\', workdir, '\\', file)), 'JPEG', quality=95)  # setting quality


def generate_video():
    image_folder = ''.join((path, '\\', workdir))  # make sure to use your folder
    os.chdir(image_folder)
    images = [img for img in os.listdir(image_folder)
              if img.endswith(".jpg") or
              img.endswith(".jpeg") or
              img.endswith("png")]
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video = cv2.VideoWriter(video_name, fourcc, 25, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))
    cv2.destroyAllWindows()
    video.release()


generate_video()
