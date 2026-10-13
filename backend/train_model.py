from ml_model import train_and_save


def main():
    print("Entraînement du modèle de détection des risques d'incendie...")
    metrics = train_and_save()
    print(f"Précision (accuracy): {metrics['accuracy'] * 100:.2f}%")
    print("Rapport de classification:")
    for cls, scores in metrics["classification_report"].items():
        if isinstance(scores, dict):
            print(f"  {cls}: precision={scores.get('precision', 0):.3f}, recall={scores.get('recall', 0):.3f}")
    print("Top features:")
    for f in metrics["feature_importance"][:5]:
        print(f"  {f['feature']}: {f['importance']}")
    print("Modèle sauvegardé dans models/")


if __name__ == "__main__":
    main()
