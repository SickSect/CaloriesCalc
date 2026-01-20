import os

import PIL
import torch
from PIL.Image import Image
from torch import nn
from torchvision.transforms import transforms


class FoodNet(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.is_trained = False
        self.device = torch.device('cuda')
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.fc1 = nn.Linear(256 * 28 * 28, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
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

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = self.pool(self.relu(self.conv3(x)))

        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return x

    def predict(self, image_path, model):
        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                return {'success': False, 'error': 'Файл не найден'}

            # Загружаем и предобрабатываем изображение
            image = PIL.Image.open(image_path).convert('RGB')

            input_tensor = self.val_transform(image).unsqueeze(0).to(self.device)

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