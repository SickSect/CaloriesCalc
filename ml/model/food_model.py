from torch import nn
from torchvision.transforms import transforms


class FoodNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.fc1 = nn.Linear(128 * 64 * 64, 1024)
        self.fc2 = nn.Linear(1024, 32)  # ← ИСПРАВЛЕНО!
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
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
        x = self.pool(self.relu(self.conv1(x)))  # (N, 64, 128, 128)
        x = self.pool(self.relu(self.conv2(x)))  # (N, 128, 64, 64)
        x = x.view(x.size(0), -1)                # (N, 524288)
        x = self.dropout(self.relu(self.fc1(x))) # (N, 1024)
        x = self.fc2(x)                          # (N, 32)
        return x