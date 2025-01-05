from memory_profiler import profile
import os
import json
import torch
import numpy as np
import evaluate
import matplotlib.pyplot as plt
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation, Trainer, TrainingArguments
from huggingface_hub import hf_hub_download
from datasets import Dataset
import zipfile
import torch.nn.functional as F

#Включил блокировку ошибок CUDA
export CUDA_LAUNCH_BLOCKING=1

# Отключаем использование cuDNN
torch.backends.cudnn.enabled = False

# Устанавливаем GPU, если доступен
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Используемое устройство: {device}")

# Разархивирование датасета
zip_file = '/misc/home6/s0185/segm_models/SpaceNet_sam_output.zip'
output_folder = '/misc/home6/s0185/segm_models/SpaceNet_sam_dataset'

if not os.path.exists(output_folder):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(output_folder)

# Пути к папкам
data_folders = {
    "train": {
        "images": os.path.join(output_folder, "SpaceNet_sam_output/train/img"),
        "annotations": os.path.join(output_folder, "SpaceNet_sam_output/train/gt")
    },
    "validation": {
        "images": os.path.join(output_folder, "SpaceNet_sam_output/validation/img"),
        "annotations": os.path.join(output_folder, "SpaceNet_sam_output/validation/gt")
    },
}

# Проверка наличия файлов
for split, paths in data_folders.items():
    for key, path in paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Директория {path} не существует.")
        files = os.listdir(path)
        if not files:
            raise ValueError(f"Директория {path} пуста.")
        print(f"Файлы в {split} {key}: {files[:5]}")

# Загрузка меток
repo_id = "huggingface/label-files"
filename = "ade20k-id2label.json"
file_path = hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset")

with open(file_path, "r") as f:
    id2label = json.load(f)

id2label = {int(k): v for k, v in id2label.items()}
label2id = {v: k for k, v in id2label.items()}
num_labels = len(id2label)

# Загрузка модели и процессора
checkpoint = "nvidia/mit-b0"
image_processor = AutoImageProcessor.from_pretrained(checkpoint, do_rescale=False)
model = AutoModelForSemanticSegmentation.from_pretrained(
    checkpoint, num_labels=num_labels, id2label=id2label, label2id=label2id
).to(device)

# Функция загрузки данных
def load_images_and_annotations(images_dir, annotations_dir, target_size=(512, 512)):
    images, annotations = [], []
    image_files = sorted([f for f in os.listdir(images_dir) if f.endswith(('.tif', '.png'))])
    annotation_files = sorted([f for f in os.listdir(annotations_dir) if f.endswith(('.tif', '.png'))])

    for image_file, annotation_file in zip(image_files, annotation_files):
        try:
            img = Image.open(os.path.join(images_dir, image_file)).resize(target_size, Image.LANCZOS)
            ann = Image.open(os.path.join(annotations_dir, annotation_file)).convert('L').resize(target_size, Image.NEAREST)
            images.append(np.array(img))
            annotations.append(np.array(ann))
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")

    return images, annotations

# Загрузка данных
train_images, train_annotations = load_images_and_annotations(
    data_folders["train"]["images"], data_folders["train"]["annotations"]
)
val_images, val_annotations = load_images_and_annotations(
    data_folders["validation"]["images"], data_folders["validation"]["annotations"]
)

# Создание датасета
def create_dataset(images, annotations):
    return Dataset.from_dict({"pixel_values": images, "labels": annotations})

train_dataset = create_dataset(train_images, train_annotations)
val_dataset = create_dataset(val_images, val_annotations)

# Трансформации
def train_transforms(example_batch):
    images = [torch.tensor(x, dtype=torch.float32) for x in example_batch["pixel_values"]]
    labels = [torch.tensor(x, dtype=torch.int64) for x in example_batch["labels"]]
    pixel_values = image_processor(images, return_tensors="pt").pixel_values
    labels = torch.stack(labels)
    return {"pixel_values": pixel_values, "labels": labels}

train_dataset = train_dataset.map(train_transforms, batched=True, batch_size=4)
val_dataset = val_dataset.map(train_transforms, batched=True, batch_size=4)

# Параметры обучения
training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=5,
    eval_strategy="steps",
    save_steps=10,
    eval_steps=10,
    logging_dir='./logs',
    logging_steps=10,
    remove_unused_columns=False,
)

# Метрика
metric = evaluate.load("mean_iou")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    logits = np.argmax(logits, axis=1)
    metrics = metric.compute(predictions=logits, references=labels, num_labels=num_labels, ignore_index=255)
    return metrics

# Тренер
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
)

# Обучение
try:
    trainer.train()
except RuntimeError as e:
    print(f"Ошибка при обучении: {e}")

# Визуализация
def visualize_predictions(images, predictions, annotations, n=4):
    n = min(len(images), len(predictions), len(annotations), n)
    plt.figure(figsize=(15, 6))
    for i in range(n):
        plt.subplot(3, n, i + 1)
        plt.imshow(images[i])
        plt.axis('off')
        plt.subplot(3, n, i + 1 + n)
        plt.imshow(predictions[i], cmap='gray')
        plt.axis('off')
        plt.subplot(3, n, i + 1 + 2 * n)
        plt.imshow(annotations[i], cmap='gray')
        plt.axis('off')
    plt.tight_layout()
    plt.show()

# Предсказания
model.eval()
val_predictions = []
with torch.no_grad():
    for val_image in val_images:
        inputs = image_processor(val_image, return_tensors="pt").to(device)
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_mask = logits.argmax(dim=1).squeeze(0).cpu().numpy()
        val_predictions.append(predicted_mask)

visualize_predictions(val_images, val_predictions, val_annotations, n=4)
