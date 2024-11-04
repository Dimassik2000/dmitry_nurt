
# Установка необходимых библиотек
!pip install transformers datasets evaluate huggingface_hub

import os
import json
import torch
import numpy as np
import evaluate
import matplotlib.pyplot as plt
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation, Trainer, TrainingArguments
from huggingface_hub import hf_hub_url, cached_download, notebook_login
from datasets import Dataset
from google.colab import files
import zipfile
# Загрузка файла
uploaded = files.upload()
zip_file = 'train.zip'

with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall('/content/dataset')
# Указываем пути к папкам с изображениями и аннотациями
train_images_folder = '/content/dataset/train/images'
train_annotations_folder = '/content/dataset/train/gt'
val_images_folder = '/content/dataset/val/images'
val_annotations_folder = '/content/dataset/val/gt'
# Загрузка меток
repo_id = "huggingface/label-files"
filename = "ade20k-id2label.json"
file_path = cached_download(hf_hub_url(repo_id, filename, repo_type="dataset"))

with open(file_path, "r") as f:
    id2label = json.load(f)

id2label = {int(k): v for k, v in id2label.items()}
label2id = {v: k for k, v in id2label.items()}
num_labels = len(id2label)

# Загрузка процессора изображений и модели
checkpoint = "nvidia/mit-b0"
image_processor = AutoImageProcessor.from_pretrained(checkpoint)
model = AutoModelForSemanticSegmentation.from_pretrained(checkpoint, id2label=id2label, label2id=label2id)
# Функция загрузки изображений и аннотаций
def load_images_and_annotations(images_dir, annotations_dir):
    images = []
    annotations = []

    for filename in os.listdir(images_dir):
        if filename.endswith('.tif'):
            img = Image.open(os.path.join(images_dir, filename)).convert('RGB')
            images.append(np.array(img))

    for filename in os.listdir(annotations_dir):
        if filename.endswith('.tif'):
            ann = Image.open(os.path.join(annotations_dir, filename)).convert('L')
            annotation_array = np.array(ann)
            annotation_array[annotation_array == 192] = 1
            annotations.append(annotation_array)

    return images, annotations

train_images, train_annotations = load_images_and_annotations(train_images_folder, train_annotations_folder)
val_images, val_annotations = load_images_and_annotations(val_images_folder, val_annotations_folder)

# Создание датасета с правильными именами ключей
train_dataset = Dataset.from_dict({"pixel_values": train_images, "labels": train_annotations})
val_dataset = Dataset.from_dict({"pixel_values": val_images, "labels": val_annotations})
# Трансформации для тренировки (без one-hot кодирования меток)
def train_transforms(example_batch):
    images = [torch.tensor(x) for x in example_batch["pixel_values"]]
    labels = [torch.tensor(x) for x in example_batch["labels"]]
    pixel_values = image_processor(images, return_tensors="pt").pixel_values
    labels = torch.stack(labels)  # Оставляем метки в формате (N, H, W)
    return {"pixel_values": pixel_values, "labels": labels}

# Трансформации для валидации (без one-hot кодирования меток)
def val_transforms(example_batch):
    images = [torch.tensor(x) for x in example_batch["pixel_values"]]
    labels = [torch.tensor(x) for x in example_batch["labels"]]
    pixel_values = image_processor(images, return_tensors="pt").pixel_values
    labels = torch.stack(labels)  # Оставляем метки в формате (N, H, W)
    return {"pixel_values": pixel_values, "labels": labels}
# Применяем трансформации к датасетам
train_dataset = train_dataset.map(train_transforms, batched=True)
val_dataset = val_dataset.map(val_transforms, batched=True)

# Параметры обучения
training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    evaluation_strategy="steps",
    save_steps=10,
    eval_steps=10,
    logging_dir='./logs',
    logging_steps=10,
    remove_unused_columns=False,
)
# Загрузка метрики
metric = evaluate.load("mean_iou")

# Функция для вычисления метрик
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    logits_tensor = torch.from_numpy(logits).argmax(dim=1).detach().cpu().numpy()
    metrics = metric.compute(predictions=logits_tensor, references=labels, num_labels=num_labels, ignore_index=255)
    return metrics
# Создание тренера
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)
# Запуск обучения
trainer.train()
def show_images(images, annotations, n=4):
    n = min(len(images), len(annotations), n)
    for i in range(n):
        plt.subplot(2, n, i + 1)
        plt.imshow(images[i])  # Изображение как PIL
        plt.axis('off')

        plt.subplot(2, n, i + 1 + n)
        plt.imshow(annotations[i], cmap='gray')  # Аннотация как NumPy
        plt.axis('off')

    plt.show()
# Отображение изображений перед обучением
show_images(train_images, train_annotations, n=4)
# Указываем пути к изображениям и аннотациям для обучения
train_images_folder = '/content/dataset/train/images'
train_annotations_folder = '/content/dataset/train/gt'

# Загрузка одного изображения и аннотации
test_image_path = os.path.join(train_images_folder, os.listdir(train_images_folder)[0])
test_annotation_path = os.path.join(train_annotations_folder, os.listdir(train_annotations_folder)[0])

# Открытие изображения и аннотации
test_image = Image.open(test_image_path).convert("RGB")
test_annotation = Image.open(test_annotation_path).convert("L")

# Преобразуем аннотацию в массив NumPy и задаем класс 1 для значений 192
annotation_array = np.array(test_annotation)
annotation_array[annotation_array == 192] = 1

# Предобработка изображения и аннотации для модели
inputs = image_processor(test_image, return_tensors="pt")
inputs = inputs.to(model.device)  # Отправка на устройство
labels = torch.tensor(annotation_array, dtype=torch.long).unsqueeze(0).to(model.device)  # Добавляем измерение для батча

# Создаем мини-датасет с одним изображением и аннотацией
single_train_dataset = [{"pixel_values": inputs["pixel_values"].squeeze(), "labels": labels.squeeze()}]

# Настройка тренера для одного шага обучения
training_args = TrainingArguments(
    output_dir="./output_single_image",
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    num_train_epochs=1,
    logging_dir='./logs',
    logging_steps=1,
    evaluation_strategy="no"
)

# Функция для подготовки данных, возвращающая "pixel_values" и "labels"
def data_collator(features):
    pixel_values = torch.stack([f["pixel_values"] for f in features])
    labels = torch.stack([f["labels"] for f in features])
    return {"pixel_values": pixel_values, "labels": labels}

# Создаем новый тренер для обучения на одном изображении
trainer_single_image = Trainer(
    model=model,
    args=training_args,
    train_dataset=single_train_dataset,
    data_collator=data_collator,
)

# Запуск обучения на одном изображении
trainer_single_image.train()

# Предсказание на обученной картинке
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_mask = torch.argmax(logits, dim=1).squeeze().cpu().numpy()

# Визуализация предсказанной маски
plt.imshow(predicted_mask, cmap="gray")
plt.title("Предсказанная маска сегментации")
plt.axis("off")
plt.show()
