import os

import torch
from torchvision.transforms import transforms
from PIL import Image

from ml.food_model import FoodNet


class Predictor:
    def __init__(self, model_path, class_names, device = None):
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.class_names = class_names

        # Создаём модель
        self.model = FoodNet(num_classes=len(class_names))
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        # Трансформации
        self.train_transform = transforms.Compose([
            transforms.Resize(256),  # Сохраняем пропорции
            transforms.CenterCrop(224),  # ← Берём центр — там почти всегда сам продукт
            transforms.ColorJitter(brightness=0.2, contrast=0.2),  # ← Только цвет/контраст
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.val_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image_path, model):
        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                return {'success': False, 'error': 'Файл не найден'}

            # Загружаем и предобрабатываем изображение
            image = Image.open(image_path).convert('RGB')

            print("=== ОТЛАДКА УСТРОЙСТВ ===")
            print(f"Модель на устройстве: {next(model.parameters()).device}")
            print(f"Устройство по умолчанию: {self.device}")

            # ... загрузка изображения ...
            input_tensor = self.val_transform(image).unsqueeze(0)
            print(f"Изображение до переноса: {input_tensor.device}")

            input_tensor = input_tensor.to(self.device)
            print(f"Изображение после переноса: {input_tensor.device}")
            print("=== КОНЕЦ ОТЛАДКИ ===")

            input_tensor = self.val_transform(image).unsqueeze(0).to(self.device)
            print(f'DEVICE: {self.device}')
            # Делаем предсказание
            with torch.no_grad():
                output = model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                confidence, predicted_idx = torch.max(probabilities, dim=1)

                predicted_class = self.class_names[predicted_idx.item()]
                confidence_percent = round(confidence.item() * 100, 2)

            return {
                'success': True,
                'food_class': predicted_class,
                'confidence': confidence_percent,
                'message': 'Успешно распознано!'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}