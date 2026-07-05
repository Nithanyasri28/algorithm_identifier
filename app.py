from flask import Flask, render_template, request, send_file
import pandas as pd

from report_generator import generate_report

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

app = Flask(__name__)

# Store latest analysis results
latest_results = {}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dashboard')
def dashboard():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/report')
def report():

    return render_template(
        'report.html',
        dataset_name=latest_results.get("dataset_name", ""),
        rows=latest_results.get("rows", 0),
        cols=latest_results.get("columns", 0),
        missing=latest_results.get("missing_values", 0),
        best_algorithm=latest_results.get("best_algorithm", ""),
        best_accuracy=latest_results.get("best_accuracy", 0),
        ranked_results=latest_results.get("ranked_results", []),
        insights=latest_results.get("insights", []),
        reason=latest_results.get("reason", "")
    )


@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['file']

    if file.filename == '':
        return "No file selected"

    try:

        data = pd.read_csv(file)

        preview = data.head().to_html(
            classes='preview-table',
            index=False
        )

        # Dataset Information
        rows = data.shape[0]
        cols = data.shape[1]
        missing_values = data.isnull().sum().sum()

        # Features and Target
        X = data.iloc[:, :-1]
        y = data.iloc[:, -1]

        # Encode Target
        le = LabelEncoder()
        y = le.fit_transform(y)

        # Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.3,
            random_state=42
        )

        # Models
        models = {
            "Decision Tree": DecisionTreeClassifier(),
            "Random Forest": RandomForestClassifier(),
            "KNN": KNeighborsClassifier(),
            "SVM": SVC()
        }

        results = {}

        for name, model in models.items():

            model.fit(X_train, y_train)

            predictions = model.predict(X_test)

            accuracy = accuracy_score(y_test, predictions)

            results[name] = round(accuracy * 100, 2)

        # Best Model
        best_algorithm = max(results, key=results.get)

        best_accuracy = results[best_algorithm]

        ranked_results = sorted(
            results.items(),
            key=lambda x: x[1],
            reverse=True
        )

        reason = (
            f"{best_algorithm} achieved the highest accuracy of "
            f"{best_accuracy}% on the uploaded dataset."
        )

        duplicates = data.duplicated().sum()

        insights = [
            "Problem Type : Classification",
            f"Dataset contains {rows} records and {cols} columns.",
            f"Missing Values Found : {missing_values}",
            f"Duplicate Rows Found : {duplicates}",
            f"Best Performing Algorithm : {best_algorithm}",
            f"Highest Accuracy : {best_accuracy}%"
        ]

        # Save for Report Page & PDF
        latest_results["dataset_name"] = file.filename
        latest_results["rows"] = rows
        latest_results["columns"] = cols
        latest_results["missing_values"] = missing_values
        latest_results["best_algorithm"] = best_algorithm
        latest_results["best_accuracy"] = best_accuracy
        latest_results["ranked_results"] = ranked_results
        latest_results["reason"] = reason
        latest_results["insights"] = insights

        latest_results["accuracies"] = {
            "Decision Tree": f"{results['Decision Tree']}%",
            "Random Forest": f"{results['Random Forest']}%",
            "KNN": f"{results['KNN']}%",
            "SVM": f"{results['SVM']}%"
        }

        return render_template(
            'result.html',
            rows=rows,
            cols=cols,
            missing=missing_values,
            results=results,
            ranked_results=ranked_results,
            best_algorithm=best_algorithm,
            reason=reason,
            preview=preview,
            insights=insights
        )

    except Exception as e:
        return f"Error : {str(e)}"


@app.route('/download_report')
def download_report():

    filename = "ML_Report.pdf"

    generate_report(
        filename=filename,
        dataset_name=latest_results.get("dataset_name", ""),
        rows=latest_results.get("rows", ""),
        columns=latest_results.get("columns", ""),
        best_algorithm=latest_results.get("best_algorithm", ""),
        accuracies=latest_results.get("accuracies", {})
    )

    return send_file(
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)