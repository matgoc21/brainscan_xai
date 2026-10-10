import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights

class BrainTumorResNet(nn.Module):
    def __init__(self, num_classes=4):
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