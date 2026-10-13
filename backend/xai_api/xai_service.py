import torch
import torch.nn as nn
import numpy as np
import io
import base64
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
from captum.attr import LayerGradCam, LayerAttribution

from .model import BrainTumorResNet , CustomCNN

device = torch.device("cpu")
model = CustomCNN(num_classes=4) #zmienic na CustomCNN, po wytrenowaniu

model.load_state_dict(torch.load('xai_api/best_brain_tumor_model_customCNN.pth', map_location=device))
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
        propabilities = nn.functional.softmax(outputs[0], dim=0)
        confidence, pred_class_idx = torch.max(propabilities, 0)

    predicted_class = CLASSES[pred_class_idx.item()]

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
    base64_img = base64.b64encode(buf.read()).decode('utf-8')

    return {
        "prediction": predicted_class,
        "confidence": round(confidence.item() * 100, 2),
        "heatmap_base64": f"data:image/png;base64,{base64_img}",
    }
