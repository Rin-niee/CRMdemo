from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from typing import List
import os

from config import STORAGE_PATH  

# Создаем FastAPI приложение для работы с файлами
app = FastAPI()


@app.get("/files/{user_id}/{order_id}", response_model=List[str])
async def list_files(user_id: int, order_id: str):
    """
    Получает список файлов для конкретного заказа пользователя
    
    Args:
        user_id: ID пользователя (менеджера)
        order_id: ID заказа
        
    Returns:
        Список имен файлов в папке заказа
        
    Raises:
        HTTPException: Если папка не найдена
    """
    folder_path = os.path.join(STORAGE_PATH, str(user_id), order_id)
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Папка не найдена")
    
    # Получаем список файлов в папке заказа
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return files


@app.get("/files/{user_id}/{order_id}/{filename}")
async def get_file(user_id: int, order_id: str, filename: str):
    """
    Скачивает конкретный файл из заказа
    
    Args:
        user_id: ID пользователя (менеджера)
        order_id: ID заказа
        filename: Имя файла для скачивания
        
    Returns:
        Файл для скачивания
        
    Raises:
        HTTPException: Если файл не найден
    """
    file_path = os.path.join(STORAGE_PATH, str(user_id), order_id, filename)
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Возвращаем файл для скачивания
    return FileResponse(file_path, filename=filename)
