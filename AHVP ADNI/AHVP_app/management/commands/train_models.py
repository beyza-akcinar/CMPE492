import os
import pickle
from django.core.management.base import BaseCommand
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from AHVP_app.models import Muayene, MRISonuc
from django.conf import settings
import pandas as pd
import shap

class Command(BaseCommand):
    help = 'Train, optimize, and save multiple ML models using data from the database'

    def handle(self, *args, **kwargs):
        # ml_models klasör yolunu belirle
        ML_MODELS_DIR = os.path.join(settings.BASE_DIR, 'ml_models')
        if not os.path.exists(ML_MODELS_DIR):
            os.makedirs(ML_MODELS_DIR)

        # Veritabanından verileri çek
        muayene_data = Muayene.objects.all().values(
            'id', 'tani_encoding', 'CDRSB', 'ADAS11', 'ADAS13', 
            'RAVLT_immediate', 'RAVLT_learning', 'RAVLT_forgetting', 
            'FAQ'
        )
        mri_data = MRISonuc.objects.all().values(
            'muayene_id', 'ventricles', 'hippocampus', 'whole_brain', 
            'entorhinal', 'fusiform', 'mid_temp'
        )
        muayene_df = pd.DataFrame(muayene_data)
        mri_df = pd.DataFrame(mri_data)
        data = muayene_df.merge(mri_df, left_on='id', right_on='muayene_id')
        data.drop(columns=['id', 'muayene_id'], inplace=True)

        # Sınıf etiketlerini yeniden düzenlemek için bir mapping oluştur
        class_mapping = {2: 0, 3: 1, 5: 2}
        data['tani_encoding'] = data['tani_encoding'].map(class_mapping)

        # Hedef ve özellikleri ayır
        target_column = 'tani_encoding'
        features_columns = [
            'CDRSB', 'ADAS11', 'ADAS13', 'RAVLT_immediate', 
            'RAVLT_learning', 'RAVLT_forgetting', 'FAQ', 
            'ventricles', 'hippocampus', 'whole_brain', 
            'entorhinal', 'fusiform', 'mid_temp'
        ]
        X = data[features_columns]
        y = data[target_column]

        # Eğitim ve test setine ayır
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Modelleri ve hiperparametreleri tanımla
        models = {
            "logistic_regression": (LogisticRegression(max_iter=1000, random_state=42), {
                "C": [0.1, 1, 10],
                "solver": ["lbfgs", "liblinear"]
            }),
            "random_forest": (RandomForestClassifier(random_state=42), {
                "n_estimators": [100, 200, 300],
                "max_depth": [None, 10, 20],
                "min_samples_split": [2, 5, 10]
            }),
            "svm": (SVC(probability=True, random_state=42), {
                "C": [0.1, 1, 10],
                "kernel": ["linear", "rbf"],
                "gamma": [0.001, 0.01, 0.1, 1]  # Gamma için aralık

            }),
            "xgboost": (XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42), {
                "n_estimators": [100, 200, 300],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 6, 9]
            })
        }
        
        # Her bir modeli optimize et, eğit ve kaydet
        for model_name, (model, param_grid) in models.items():
            self.stdout.write(self.style.SUCCESS(f"{model_name} hiperparametre optimizasyonu yapılıyor..."))
            grid_search = GridSearchCV(model, param_grid, cv=3, scoring="accuracy", n_jobs=-1)
            grid_search.fit(X_train, y_train)

            # En iyi modeli al
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_

            # Hiperparametreleri kaydet
            params_path = os.path.join(ML_MODELS_DIR, f"{model_name}_params.pkl")
            with open(params_path, 'wb') as f:
                pickle.dump(best_params, f)

            # Modeli kaydet
            model_path = os.path.join(ML_MODELS_DIR, f"{model_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(best_model, f)

            # Model doğruluğunu yazdır
            accuracy = best_model.score(X_test, y_test)
            self.stdout.write(self.style.SUCCESS(f"{model_name} başarıyla optimize edildi ve eğitildi. Doğruluk: {accuracy:.2f}"))
            self.stdout.write(self.style.SUCCESS(f"Model şu dosyaya kaydedildi: {model_path}"))
            self.stdout.write(self.style.SUCCESS(f"{model_name} için seçilen hiperparametreler: {best_params}"))

            # SHAP değerlerini hesaplama
            self.stdout.write(self.style.SUCCESS(f"{model_name} için SHAP değerleri hesaplanıyor..."))
            background_sample = shap.sample(X_train, 3)

            if model_name == "svm":
                explainer = shap.KernelExplainer(best_model.predict_proba, background_sample)
                shap_values = explainer.shap_values(X_train)
            elif model_name == "logistic_regression":
                explainer = shap.LinearExplainer(best_model, X_train)
                shap_values = explainer.shap_values(X_train)
            else:
                explainer = shap.TreeExplainer(best_model)
                shap_values = explainer.shap_values(X_train, check_additivity=False)

            # SHAP değerlerini kaydet
            shap_values_path = os.path.join(ML_MODELS_DIR, f"{model_name}_shap_values.pkl")
            with open(shap_values_path, 'wb') as f:
                pickle.dump(shap_values, f)

            self.stdout.write(self.style.SUCCESS(f"{model_name} için SHAP değerleri şu dosyaya kaydedildi: {shap_values_path}"))
        
        X_train_path = os.path.join(ML_MODELS_DIR, "X_train.pkl")
        with open(X_train_path, 'wb') as f:
            pickle.dump(X_train, f)