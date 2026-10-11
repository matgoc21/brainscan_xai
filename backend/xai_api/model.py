import torch
import torch.nn.functional as F
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights

class BrainTumorResNet(nn.Module):
    def __init__(self, num_classes=4, dropout_rate=0.5):
        """
        Architektura klasyfikaotra guzów na podstawie ResNet50 z transfer learningiem.
        """
        super(BrainTumorResNet, self).__init__()

        self.backbone = resnet50(weights=ResNet50_Weights.DEFAULT)

        in_features = self.backbone.fc.in_features

        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)
    def get_target_layer(self):
        return self.backbone.layer4[-1]

class CustomCNN(nn.Module):
    def __init__(self, num_classes=4):
        """
        Głęboka architektura CNN (5 bloków splotowych), wykorzystująca Batch Normalization
        """
        super(CustomCNN, self).__init__()

        #Wejście: 3 kanały, obraz 224x224
        
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride = 2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding = 1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2,2)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2,2)

        self.conv4 = nn.Conv2d(128,256, kernel_size = 3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2,2)

        self.conv5 = nn.Conv2d(256, 512, kernel_size=3, padding=1)
        self.bn5 = nn.BatchNorm2d(512)
        self.pool5 = nn.MaxPool2d(2,2)

        self.fc1 = nn.Linear(512*7*7, 1024)
        self.dropout = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(1024, num_classes)

    def forward(self, x):
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        x = self.pool5(F.relu(self.bn5(self.conv5(x))))

        x = torch.flatten(x,1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

    def get_target_layer(self):
        """
        Zwraca ostatnią warstwę splotową
        """

        return self.conv5

        