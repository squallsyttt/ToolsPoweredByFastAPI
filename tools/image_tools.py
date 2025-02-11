import os
from datetime import datetime
from PIL import Image

class ImageTools:
    @staticmethod
    def cut_bottom(local_path: str, pixels: int = 50) -> bool:
        try:
            for filename in os.listdir(local_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(local_path, filename)
                    with Image.open(file_path) as img:
                        # 裁剪图片
                        width, height = img.size
                        crop_area = (0, 0, width, height - pixels)
                        img_cropped = img.crop(crop_area)
                        # 获取新的文件名
                        current_date = datetime.now().strftime("%Y%m%d")
                        original_name = os.path.splitext(filename)[0][:4]  # 获取原文件名前4个字符
                        file_extension = os.path.splitext(filename)[1]
                        new_height = height - pixels
                        new_filename = f"{current_date}_{original_name}_{new_height}px{file_extension}"
                        # 保存新图片
                        new_file_path = os.path.join(local_path, new_filename)
                        img_cropped.save(new_file_path)
                        # 删除原图片
                        os.remove(file_path)
            return True
        except Exception as e:
            print(f"处理图片时发生错误: {str(e)}")
            return False   