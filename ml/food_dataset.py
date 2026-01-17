from PIL.Image import Image
from datasets import Dataset


class FoodDataset(Dataset):
    def __init__(self, data_list, transform=None):
        """
            data_list: список кортежей [(путь, класс), ...]
        """
        self.data_list = data_list
        self.transform = transform
        self.classes = sorted(list(label for _, label in data_list))
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}

        def __len__(self):
            return len(self.data)

        def __getitem__(self, idx):
            img_path, class_name = self.data[idx]
            image = Image.open(img_path).convert('RGB')

            if self.transform:
                image = self.transform(image)

            label = self.class_to_idx[class_name]
            return image, label