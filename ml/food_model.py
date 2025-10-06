import torchvision.models as models
import torchvision.transforms as transforms
import torch
from torch import nn


class FoodModel:
    def __init__(self, food_classes = None):
        print("🚀 Инициализируем простую модель для распознавания еды...")
            # CHECK IF CUDA IS AVAILABLE, ELSE - CPU
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            # USE PRETRAINNED MODEL
        self.model = models.efficientnet_b0(pretrained=True)
            # CLASSIFIER CLASSES
        self.food_classes = [
            'яблоко',
            'банан',
            'бутерброд',
            'морковь',
            'салат',
            'апельсин',
            'брокколи',
            'хот-дог',
            'пицца',
            'пончик'
        ]
            # CHANGE LAST LAYER TO OUT CLASSIFICATOR
        new_features = self.model.classifier[1].in_features
        num_classes = self.food_classes.__len__()
        self.model.classifier[1] = nn.Linear(new_features, num_classes)
            # MODEL CONFIGURATING
        self.model = self.model.to(self.device)
        self.transforms = transforms.Compose([
            transforms.Resize((224,224)),  # APP IMAGES WILL BE 224x224 px
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])