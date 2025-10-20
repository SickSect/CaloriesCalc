import torchvision.transforms as transforms
import torch
import torchvision.models as models
import os
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from log.log_writer import log
from ml.data_loader import product_lists, product_classes_idx


class FoodDataset(Dataset):
    """Датасет для обучения на собранных фото"""

    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.class_to_idx = product_classes_idx

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        try:
            image = Image.open(self.image_paths[idx]).convert('RGB')
            label = self.class_to_idx.get(self.labels[idx], 5)  # 'другое' по умолчанию

            if self.transform:
                image = self.transform(image)

            return image, label
        except Exception as e:
            # Возвращаем заглушку в случае ошибки
            image = Image.new('RGB', (224, 224), color='gray')
            if self.transform:
                image = self.transform(image)
            return image, 5  # Класс 'другое'

class FoodModel:
    def __init__(self, food_classes = None):
        log('debug',"🚀 Инициализируем обучаемую модель...")

        self.ml_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.ml_dir, "trained_model.pth")

        # Устройство
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        log('debug',f"📱 Устройство: {self.device}")

        # Классы (совпадают с DataCollector)
        self.class_names = product_lists
        self.class_to_idx = {name: i for i, name in enumerate(self.class_names)}

        # Трансформации
        self.train_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.RandomCrop((224,224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(25),
            transforms.ColorJitter(0.3, 0.3, 0.3, 0.1),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # Инициализируем модель
        self.model = self._create_model()
        self.is_trained = False

        # Пробуем загрузить обученную модель
        if os.path.exists(self.model_path):
            self.load_model()
            log('debug',"✅ Загружена обученная модель")
        else:
            log('error',"🆕 Модель не обучена. Нужно собрать данные и обучить.")

    def _create_model(self):
        """Создаёт модель с предобученными весами"""
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        for param in model.parameters():
            param.requires_grad = False

        num_features = model.classifier[1].in_features
        classes_amount = len(self.class_names)
        model.classifier[1] = nn.Linear(num_features, classes_amount)

        return model.to(self.device)

    def train(self, data_collector, epochs=5, batch_size=8):
        """Обучает модель на собранных данных"""
        log('debug',"🎯 Начинаем обучение модели...")
        # Получаем данные для обучения
        labeled_data = data_collector.get_labeled_data()
        if len(labeled_data) < 10:
            log('error',f"❌ Недостаточно данных: {len(labeled_data)} образцов (нужно минимум 10)")
            return False
        # Разделяем на пути и метки
        image_paths, labels = zip(*labeled_data)
        # Создаём датасет и загрузчик
        dataset = FoodDataset(image_paths, labels, transform=self.train_transform)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        # Оптимизатор и функция потерь
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        # Обучение
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            correct = 0
            total = 0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

            accuracy = 100 * correct / total
            log('debug',
                f'📊 Эпоха [{epoch + 1}/{epochs}], Loss: {total_loss / len(dataloader):.4f}, Accuracy: {accuracy:.2f}%')

        # Сохраняем модель
        self.save_model()
        self.is_trained = True

        log('info',f"✅ Обучение завершено! Обучено на {len(labeled_data)} образцах")
        return True

    def predict(self, image_path):
        """Предсказание для изображения"""
        if not self.is_trained:
            return {
                'success': False,
                'error': 'Модель не обучена',
                'message': 'Сначала обучите модель на собранных данных'
            }

        try:
            # Загружаем и обрабатываем изображение
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.val_transform(image).unsqueeze(0).to(self.device)

            # Предсказание
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                predicted_idx = torch.argmax(probabilities).item()
                confidence = probabilities[predicted_idx].item()

            predicted_class = self.class_names[predicted_idx]

            return {
                'success': True,
                'food_class': predicted_class,
                'confidence': round(confidence * 100, 2),
                'message': 'Предсказание обученной модели',
                'all_probabilities': {
                    cls: round(prob.item() * 100, 2)
                    for cls, prob in zip(self.class_names, probabilities)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при предсказании'
            }

    def save_model(self):
        """Сохраняет модель"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'class_names': self.class_names,
            'is_trained': True
        }, self.model_path)
        log('info',f"💾 Модель сохранена: {self.model_path}")

    def load_model(self):
        """Загружает модель"""
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.class_names = checkpoint.get('class_names', self.class_names)
            self.is_trained = checkpoint.get('is_trained', False)
            return True
        except Exception as e:
            log('error',f"❌ Ошибка загрузки модели: {e}")
            return False

    def get_model_info(self):
        """Информация о модели"""
        return {
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'device': str(self.device),
            'class_names': self.class_names,
            'status': 'Обучена' if self.is_trained else 'Не обучена'
        }