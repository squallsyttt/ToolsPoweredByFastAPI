import os
from datetime import datetime
from PIL import Image

class ImageTools:
    @staticmethod
    def cut_bottom(local_path: str, pixels: int = 50) -> bool:
        try:
            processed_files = []
            # 创建一个新的文件夹来存放处理后的图片
            output_dir = os.path.join(local_path, "processed")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
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
                        original_name = os.path.splitext(filename)[0][:2]
                        file_extension = os.path.splitext(filename)[1]
                        new_height = height - pixels
                        new_filename = f"{current_date}_{original_name}_{new_height}px_{len(processed_files)+1}{file_extension}"
                        
                        # 保存新图片到processed文件夹
                        new_file_path = os.path.join(output_dir, new_filename)
                        img_cropped.save(new_file_path)
                        processed_files.append(new_filename)
            
            print(f"成功处理的文件: {', '.join(processed_files)}")
            print(f"处理后的文件保存在: {output_dir}")
            return True
        except Exception as e:
            print(f"处理图片时发生错误: {str(e)}")
            return False   