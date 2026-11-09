import torch
import torch.nn as nn
import numpy as np
import io
import base64
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
from captum.attr import LayerGradCam, LayerAttribution
from django.core.files.base import ContentFile

from .model import BrainTumorResNet , CustomCNN, ResidualCustomCNN

device = torch.device("cpu")
model = ResidualCustomCNN(num_classes=4) #zmienic na CustomCNN, po wytrenowaniu

model.load_state_dict(torch.load('xai_api/best_brain_tumor_model_customCNN_glioma15.pth', map_location=device))
model.eval()

CLASSES = ['glioma', 'meningioma', 'notumor', 'pituitary']

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def generate_gradcam_and_predict(image_file):
    """
    Przyjmuje plik graficzny z żądania, zwraca predykcję modelu i mapę GRAD_CAM w Base64
    """

    img = Image.open(image_file).convert('RGB')
    input_tensor = preprocess(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = nn.functional.softmax(outputs[0], dim=0)
        confidence, pred_class_idx = torch.max(probabilities, 0)

    predicted_class = CLASSES[pred_class_idx.item()]

    all_probs = {
        CLASSES[i]: round(probabilities[i].item() * 100, 2)
        for i in range(len(CLASSES))
    }

    layer_gc = LayerGradCam(model, model.get_target_layer())

    attributions = layer_gc.attribute(input_tensor, target=pred_class_idx)

    upsampled_attr = LayerAttribution.interpolate(attributions, input_tensor.shape[2:])
    attr_np = upsampled_attr.squeeze().cpu().detach().numpy()

    #Post processing mapy

    attr_np = np.maximum(attr_np, 0)
    if np.max(attr_np) > 0:
        attr_np = attr_np / np.max(attr_np)

    img_resized = img.resize((224, 224))
    img_np = np.array(img_resized) / 255.0

    fig, ax = plt.subplots(figsize=(4,4))
    ax.imshow(img_np)
    ax.imshow(attr_np, cmap='jet', alpha=0.5)
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    # base64_img = base64.b64encode(buf.read()).decode('utf-8')
    # check if this works good, change to saving after a button click, not after prediction
    heatmap_file = ContentFile(buf.read(), name = f"heatmap_{predicted_class}.png")

    return {
        "prediction": predicted_class,
        "confidence": round(confidence.item() * 100, 2),
        "probabilities": all_probs,
        #"heatmap_base64": f"data:image/png;base64,{base64_img}",
        "heatmap_file": heatmap_file,
    }
