import os
from PIL import Image

class ImageTools:
    @staticmethod
    def cut_bottom(local_path: str, pixels: int = 50) -> bool:
        try:
            for filename in os.listdir(local_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(local_path, filename)
                    with Image.open(file_path) as img:
                        width, height = img.size
                        crop_area = (0, 0, width, height - pixels)
                        img_cropped = img.crop(crop_area)
                        img_cropped.save(file_path)
            return True
        except Exception as e:
            print(f"处理图片时发生错误: {str(e)}")
            return False 