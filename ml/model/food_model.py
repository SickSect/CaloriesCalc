from torch import nn

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

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))  # (N, 64, 128, 128)
        x = self.pool(self.relu(self.conv2(x)))  # (N, 128, 64, 64)
        x = x.view(x.size(0), -1)                # (N, 524288)
        x = self.dropout(self.relu(self.fc1(x))) # (N, 1024)
        x = self.fc2(x)                          # (N, 32)
        return x