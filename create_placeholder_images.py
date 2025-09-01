#!/usr/bin/env python3
"""
Create placeholder images for the course detail page
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(width, height, text, filename, bg_color=(45, 56, 120), text_color=(255, 255, 255)):
    """Create a placeholder image with text"""
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", size=min(width, height) // 10)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    
    # Save the image
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)
    print(f"Created: {filename}")

def main():
    """Create all placeholder images"""
    
    # Course cover images
    create_placeholder_image(800, 450, "软件工程导论", "app/static/images/course_1.jpg")
    create_placeholder_image(800, 450, "数据结构与算法", "app/static/images/course_2.jpg", bg_color=(120, 45, 56))
    create_placeholder_image(800, 450, "软件项目管理", "app/static/images/course_3.jpg", bg_color=(56, 120, 45))
    create_placeholder_image(800, 450, "Web开发技术", "app/static/images/course_4.jpg", bg_color=(120, 90, 45))
    create_placeholder_image(800, 450, "移动应用开发", "app/static/images/course_5.jpg", bg_color=(90, 45, 120))
    
    # Instructor profile images
    create_placeholder_image(200, 200, "张教授", "app/static/images/instructor_1.jpg", bg_color=(80, 80, 80))
    create_placeholder_image(200, 200, "李博士", "app/static/images/instructor_2.jpg", bg_color=(80, 80, 80))
    create_placeholder_image(200, 200, "王老师", "app/static/images/instructor_3.jpg", bg_color=(80, 80, 80))
    
    # Course gallery images
    for i in range(1, 6):
        create_placeholder_image(600, 400, f"课程截图 {i}", f"app/static/images/gallery_{i}.jpg", bg_color=(60, 70, 90))
    
    print("All placeholder images created successfully!")

if __name__ == "__main__":
    main()
