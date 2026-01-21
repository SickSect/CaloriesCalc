import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder


def train_model(model, device):
    # Создание датасетов
    train_dataset = ImageFolder(root='ml/loader/train_images', transform=model.train_transform)
    test_dataset = ImageFolder(root='ml/loader/test_images', transform=model.val_transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4)
    # Вывод и изменение слоя в модели
    train_num_classes = len(train_dataset.classes)
    model.fc2 = nn.Linear(in_features=512, out_features=train_num_classes)
    # Обучение
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    for epoch in range(10):
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
    torch.save(model, 'food_model_full.pth')
    model.is_trained = True
    return model