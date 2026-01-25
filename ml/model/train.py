import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision.transforms import transforms

from log.log_writer import log


def train_model(model, device):
    # Создание датасетов
    # Трансформации
    train_transform = transforms.Compose([
        transforms.Resize(256),  # Сохраняем пропорции
        transforms.CenterCrop(224),  # ← Берём центр — там почти всегда сам продукт
        transforms.ColorJitter(brightness=0.2, contrast=0.2),  # ← Только цвет/контраст
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    train_dataset = ImageFolder(root='ml/loader/train_images', transform=train_transform)
    test_dataset = ImageFolder(root='ml/loader/test_images', transform=val_transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4)
    # Вывод и изменение слоя в модели
    train_num_classes = len(train_dataset.classes)
    print('Всего классов: ', train_num_classes)
    model.fc2 = nn.Linear(in_features=512, out_features=train_num_classes)
    # Обучение
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    print('Training started.')
    # Проверка 1: Размеры
    print("Train samples:", len(train_dataset))
    print("Classes:", len(train_dataset.classes))

    # Проверка 2: Первый батч
    images, labels = next(iter(train_loader))
    print("Batch shape:", images.shape)  # [32, 3, 224, 224]?
    print("Labels:", labels[:5])  # [0, 1, 2, ...]?

    # Проверка 3: Модель
    print("Model fc2:", model.fc2.out_features)  # = числу классов?
    for epoch in range(35):
        model.train()
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        # Валидация
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        print(f'Epoch {epoch + 1}, Test Accuracy: {100 * correct / total:.2f}%')
    torch.save(model.state_dict(), 'food_model_weights.pth')
    model.is_trained = True
    return model