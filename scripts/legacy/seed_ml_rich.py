import asyncio
import sys
import os
sys.path.insert(0, r"c:\Users\navaneeth\Ai-placement-mentor")
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

TOPICS = [
    {
        "slug": "ml-unsupervised-learning",
        "title": "Unsupervised Learning: Clustering & Dimensionality Reduction",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "K-Means & Density-Based Clustering (DBSCAN)",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Centroid vs Density-based Clustering"},
                    {"type": "text", "value": "**K-Means** partitions data into $K$ distinct clusters by minimizing the within-cluster sum of squares (inertia). It assumes clusters are spherical and similar in size. **DBSCAN** (Density-Based Spatial Clustering of Applications with Noise) groups points that are close to each other based on a distance threshold (`eps`) and a minimum number of points (`min_samples`), making it excellent for arbitrary shapes and noise detection."},
                    {"type": "code", "language": "python", "value": "from sklearn.cluster import KMeans, DBSCAN\n\n# K-Means Centroid clustering\nkmeans = KMeans(n_clusters=3, random_state=42)\nkmeans.fit(X)\n\n# DBSCAN Density-based clustering\ndbscan = DBSCAN(eps=0.5, min_samples=5)\ndbscan.fit(X)"},
                    {"type": "callout", "kind": "warning", "title": "Interview Gotcha", "value": "K-Means is highly sensitive to outliers because outliers can significantly pull the centroids away from the true cluster centers. It also requires specifying $K$ in advance, whereas DBSCAN determines the number of clusters dynamically and flags outliers as noise (-1)."},
                    {"type": "knowledge_check", "question": "Which clustering algorithm is best suited for identifying outliers/noise?", "options": [
                        "K-Means",
                        "Hierarchical Agglomerative Clustering",
                        "DBSCAN"
                    ], "correct_index": 2, "explanation": "DBSCAN classifies low-density points that do not belong to any cluster as noise (labeled -1), making it ideal for anomaly detection."}
                ]
            },
            {
                "title": "Dimensionality Reduction: PCA & t-SNE",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Linear vs. Non-linear Projection"},
                    {"type": "text", "value": "**Principal Component Analysis (PCA)** is a linear technique that projects data into a lower-dimensional space by maximizing the variance along orthogonal axes (Principal Components). **t-SNE** (t-Distributed Stochastic Neighbor Embedding) is a non-linear, probabilistic technique that maps high-dimensional distance probabilities to low-dimensional spaces, preserving local neighborhood structures (excellent for visualization)."},
                    {"type": "code", "language": "python", "value": "from sklearn.decomposition import PCA\nfrom sklearn.manifold import TSNE\n\n# PCA: fast, linear, preserves global variance\npca = PCA(n_components=2)\nX_pca = pca.fit_transform(X)\n\n# t-SNE: slow, non-linear, preserves local structure\ntsne = TSNE(n_components=2, perplexity=30.0, random_state=42)\nX_tsne = tsne.fit_transform(X)"},
                    {"type": "callout", "kind": "info", "title": "PCA Interpretation", "value": "PCA computes the eigenvectors of the data covariance matrix. The eigenvalues represent the amount of variance explained by each principal component."},
                    {"type": "knowledge_check", "question": "Which technique is strictly linear and preserves global variance?", "options": [
                        "t-SNE",
                        "PCA",
                        "Isomap"
                    ], "correct_index": 1, "explanation": "PCA uses linear orthogonal projections to maximize variance, whereas t-SNE is a non-linear method designed primarily for visualization."}
                ]
            }
        ]
    },
    {
        "slug": "ml-model-evaluation-and-validation",
        "title": "Model Evaluation & Validation",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Classification Metrics: Beyond Accuracy",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Precision, Recall, F1-Score & ROC-AUC"},
                    {"type": "text", "value": "For imbalanced classification datasets, **Accuracy** is highly misleading. We must use specific metrics:\n- **Precision**: Of all predicted positive cases, how many were actually positive? $TP / (TP + FP)$\n- **Recall (Sensitivity)**: Of all actual positive cases, how many did we detect? $TP / (TP + FN)$\n- **F1-Score**: Harmonic mean of Precision and Recall.\n- **ROC-AUC**: The Area Under the Receiver Operating Characteristic curve, measuring the model's ability to distinguish classes across all classification thresholds."},
                    {"type": "code", "language": "python", "value": "from sklearn.metrics import classification_report, roc_auc_score\n\n# Generate precision, recall, f1-score\nprint(classification_report(y_true, y_pred))\n\n# Compute Area Under ROC Curve\nauc = roc_auc_score(y_true, y_prob)\nprint(f'ROC-AUC: {auc:.4f}')"},
                    {"type": "callout", "kind": "important", "title": "Business Trade-off", "value": "In medical diagnosis, you want high Recall (minimize false negatives). In spam filtering, you want high Precision (minimize false positives placing important mail in spam)."},
                    {"type": "knowledge_check", "question": "Which metric should you optimize if false negatives are extremely costly (e.g. failing to detect a disease)?", "options": [
                        "Precision",
                        "Recall",
                        "Accuracy"
                    ], "correct_index": 1, "explanation": "Recall measures the proportion of actual positives correctly identified. Optimizing recall minimizes False Negatives."}
                ]
            },
            {
                "title": "Cross-Validation & Data Leakage",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Cross-Validation and Overfitting Prevention"},
                    {"type": "text", "value": "To obtain a reliable estimate of model performance, we use **K-Fold Cross-Validation**. The data is split into $K$ parts; the model trains on $K-1$ folds and tests on the remaining fold, repeating this $K$ times. **Data Leakage** occurs when information from the test/validation set accidentally leaks into the training set (e.g., scaling data before splitting), causing overly optimistic validation metrics."},
                    {"type": "code", "language": "python", "value": "from sklearn.model_selection import cross_val_score\nfrom sklearn.pipeline import Pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\n\n# Pipeline prevents data leakage by scaling only within each cross-val fold\npipeline = Pipeline([\n    ('scaler', StandardScaler()),\n    ('model', LogisticRegression())\n])\nscores = cross_val_score(pipeline, X, y, cv=5)\nprint(f'Mean CV Accuracy: {scores.mean():.4f}')"},
                    {"type": "callout", "kind": "tip", "title": "Preventing Leakage", "value": "Always use scikit-learn `Pipeline` or execute preprocessing (imputation, scaling) strictly *after* splitting data into train/test splits."},
                    {"type": "knowledge_check", "question": "What is the primary cause of data leakage?", "options": [
                        "Training a model for too many epochs.",
                        "Applying preprocessing transformations (like scaling or imputation) on the entire dataset before splitting into train/test folds.",
                        "Using too many features."
                    ], "correct_index": 1, "explanation": "Pre-processing on the whole dataset introduces information from the test folds into the scaling calculations, creating data leakage."}
                ]
            }
        ]
    },
    {
        "slug": "neural-networks",
        "title": "Neural Networks & Deep Learning",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Perceptrons & Backpropagation",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Gradient Descent & Backpropagation"},
                    {"type": "text", "value": "Multi-Layer Perceptrons (MLPs) consist of input, hidden, and output layers of neurons. **Backpropagation** is the algorithm used to train neural networks. It computes the gradient of the loss function with respect to the network weights using the mathematical **chain rule** of calculus, propagating errors backward from the output layer to hidden layers to update weights via gradient descent."},
                    {"type": "diagram", "title": "Forward and Backward Pass", "value": "flowchart LR\n    Input -->|Forward: Compute Output & Loss| Output\n    Output -->|Backward: Chain Rule Error Gradients| Weights[Update Weights]"},
                    {"type": "code", "language": "python", "value": "# Simple Forward Pass simulation\nimport numpy as np\n\ndef sigmoid(x):\n    return 1 / (1 + np.exp(-x))\n\n# Inputs, Weights, Biases\nx = np.array([0.5, -0.2])\nw = np.array([[0.1, 0.5], [-0.3, 0.8]])\nb = np.array([0.1, -0.1])\n\n# Layer activation\noutput = sigmoid(np.dot(w, x) + b)\nprint('Output activations:', output)"},
                    {"type": "callout", "kind": "important", "title": "Interview Question", "value": "How does the chain rule apply in backpropagation? It calculates the partial derivative of the total loss with respect to each weight by multiplying the local gradient of the activation function with the upstream error gradient."},
                    {"type": "knowledge_check", "question": "Which mathematical concept forms the basis of backpropagation?", "options": [
                        "Matrix inversion",
                        "The chain rule of calculus",
                        "Taylor series expansion"
                    ], "correct_index": 1, "explanation": "The chain rule allows computing error gradients with respect to weights in nested multi-layer networks."}
                ]
            },
            {
                "title": "Activation Functions: ReLU, Sigmoid & Softmax",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Non-Linearity in Deep Learning"},
                    {"type": "text", "value": "Activation functions introduce non-linearity into neural networks, enabling them to learn complex non-linear relationships. Without them, any multi-layer network collapses into a single linear transformation.\n- **Sigmoid**: Outputs between 0 and 1. Prone to vanishing gradients.\n- **ReLU (Rectified Linear Unit)**: $f(x) = \\max(0, x)$. Extremely fast to compute, mitigates vanishing gradients, but can suffer from 'dying ReLU'.\n- **Softmax**: Normalizes activations into a probability distribution summing to 1 (used in output layers of multi-class classification)."},
                    {"type": "code", "language": "python", "value": "import numpy as np\n\ndef relu(x):\n    return np.maximum(0, x)\n\ndef softmax(x):\n    exp_x = np.exp(x - np.max(x)) # Subtract max for numerical stability\n    return exp_x / np.sum(exp_x, axis=0)\n\nprint('ReLU(-5):', relu(-5))\nprint('Softmax probabilities:', softmax(np.array([2.0, 1.0, 0.1])))"},
                    {"type": "callout", "kind": "warning", "title": "Vanishing Gradients", "value": "Sigmoid and Tanh activations saturate for very large or very small inputs, where their derivative is close to zero. This causes weight updates to vanish in deep networks during backpropagation."},
                    {"type": "knowledge_check", "question": "Why is ReLU preferred over Sigmoid in hidden layers of deep networks?", "options": [
                        "ReLU is bounded between 0 and 1, making computations stable.",
                        "ReLU does not saturate for positive values, preventing vanishing gradients.",
                        "ReLU is a linear function."
                    ], "correct_index": 1, "explanation": "Because ReLU's derivative is 1 for any positive input, it does not cause gradients to decay to zero when backpropagating through many layers."}
                ]
            }
        ]
    },
    {
        "slug": "ml-feature-engineering-and-data-preprocessing",
        "title": "Feature Engineering & Data Preprocessing",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Imputation, Scaling & Encoding",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Preparing Tabular Data for Models"},
                    {"type": "text", "value": "Before feeding raw data into an ML algorithm, it must be cleaned and structured:\n- **Imputation**: Filling in missing values (mean, median, mode, or using ML-based KNN Imputers).\n- **Scaling**: Standardizing features to have mean 0 and variance 1 (StandardScaler) or scaling to a range [0, 1] (MinMaxScaler). Algorithms like SVMs, KNN, and neural networks are sensitive to feature scales.\n- **Encoding**: Converting categorical labels to numbers (One-Hot Encoding for nominal variables, Ordinal Encoding for ordered variables)."},
                    {"type": "code", "language": "python", "value": "from sklearn.preprocessing import StandardScaler, OneHotEncoder\nfrom sklearn.impute import SimpleImputer\nimport numpy as np\n\n# Imputation & Scaling\nimputer = SimpleImputer(strategy='median')\nscaler = StandardScaler()\n\nX_clean = scaler.fit_transform(imputer.fit_transform(X_raw))"},
                    {"type": "callout", "kind": "info", "title": "Scaling Sensitivity", "value": "Tree-based algorithms (Random Forest, Gradient Boosting) are invariant to feature scaling since splits are calculated based on individual feature thresholds. Distance-based algorithms (KNN, K-Means) and gradient descent-based algorithms strictly require scaled data."},
                    {"type": "knowledge_check", "question": "Which of the following algorithms is invariant to feature scaling?", "options": [
                        "K-Nearest Neighbors (KNN)",
                        "Support Vector Machines (SVM)",
                        "Random Forest"
                    ], "correct_index": 2, "explanation": "Random Forest makes decisions by splitting features individually. The scale of other features does not affect the split criteria."}
                ]
            }
        ]
    },
    {
        "slug": "ml-model-deployment-and-mlops-basics",
        "title": "Model Deployment & MLOps Basics",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Model Serving & Serialization",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Serving Predictions via REST API"},
                    {"type": "text", "value": "Deploying a model involves serializing its weights and preprocessing pipelines (using libraries like `pickle` or `joblib`) and wrapping it in a web service (using FastAPI or Flask) to serve prediction requests over HTTP."},
                    {"type": "code", "language": "python", "value": "import joblib\nfrom fastapi import FastAPI\nfrom pydantic import BaseModel\n\n# Serialize pipeline\n# joblib.dump(model, 'model.joblib')\n\napp = FastAPI()\nmodel = joblib.load('model.joblib')\n\nclass PredictionRequest(BaseModel):\n    features: list[float]\n\n@app.post('/predict')\ndef predict(req: PredictionRequest):\n    prediction = model.predict([req.features])\n    return {'prediction': int(prediction[0])}"},
                    {"type": "callout", "kind": "tip", "title": "Production Tip", "value": "Avoid pickled files from untrusted sources, as loading them can execute arbitrary system code. For security and cross-framework support, utilize formats like ONNX or export weight matrices directly."},
                    {"type": "knowledge_check", "question": "What is the primary risk of using Python's `pickle` library for model serialization in production?", "options": [
                        "It makes model execution slower.",
                        "It has severe security risks (unpickling untrusted data can execute arbitrary system code).",
                        "Pickle files cannot store custom classes."
                    ], "correct_index": 1, "explanation": "Unpickling untrusted files allows arbitrary byte instructions to run on the system, which is a major security vulnerability."}
                ]
            }
        ]
    },
    {
        "slug": "transformers-deep-learning",
        "title": "Transformers & Deep Learning",
        "domain_slug": "ml",
        "difficulty": "advanced",
        "subtopics": [
            {
                "title": "Attention Mechanism & Transformers",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Self-Attention and LLMs"},
                    {"type": "text", "value": "The **Self-Attention** mechanism allows models to focus on different parts of an input sequence when processing a specific token, capturing long-range dependencies and contextual relationships without relying on sequential recurrence (like LSTMs or RNNs). This forms the core of the **Transformer** architecture used in modern Large Language Models (LLMs)."},
                    {"type": "diagram", "title": "Transformer Attention Map", "value": "flowchart TD\n    Input[Tokens: 'The', 'bank', 'of', 'river'] --> Embedding[Embeddings]\n    Embedding --> Attention[Self-Attention Layer: Calculates context weights]\n    Attention --> Output[Contextual Vectors]"},
                    {"type": "code", "language": "python", "value": "# High-level model load using HuggingFace Transformers\nfrom transformers import pipeline\n\n# Fast inference pipeline\nclassifier = pipeline('sentiment-analysis')\nres = classifier('Self-attention changed NLP completely!')\nprint(res)"},
                    {"type": "callout", "kind": "info", "title": "Transformer Advantage", "value": "Unlike recurrent networks that process tokens step-by-step, Transformers process all tokens in parallel, enabling massive training scale on GPUs."},
                    {"type": "knowledge_check", "question": "What is the main architectural advantage of Transformers over RNNs?", "options": [
                        "They consume less memory.",
                        "They can process input sequences in parallel, facilitating massive GPU scaling.",
                        "They only support linear transformations."
                    ], "correct_index": 1, "explanation": "Transformers discard recurrence in favor of self-attention, allowing parallelized sequence processing during training."}
                ]
            }
        ]
    },
    {
        "slug": "ml-math-foundations",
        "title": "Math Foundations (Linear Algebra, Probability & Stats)",
        "domain_slug": "ml",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Vectors, Matrices & Eigenvalues",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Linear Algebra Basics"},
                    {"type": "text", "value": "Machine learning algorithms treat datasets as matrices. In linear algebra:\n- **Vector**: A 1D array of numbers indicating a point in space.\n- **Matrix Multiplication**: Projects data into new spaces.\n- **Eigenvectors & Eigenvalues**: For a matrix $A$, if $Av = \\lambda v$, then $v$ is an eigenvector and $\\lambda$ is the eigenvalue. This is the foundation of Principal Component Analysis (PCA) and dimensionality reduction."},
                    {"type": "code", "language": "python", "value": "import numpy as np\n\n# Matrix multiplication\nA = np.array([[1, 2], [3, 4]])\nx = np.array([1, 2])\nprint('Ax:', np.dot(A, x))\n\n# Eigenvalues and Eigenvectors\neigenvalues, eigenvectors = np.linalg.eig(A)\nprint('Eigenvalues:', eigenvalues)"},
                    {"type": "callout", "kind": "info", "title": "Calculus in ML", "value": "Gradient descent uses **partial derivatives** and the **gradient vector** (direction of steepest ascent) to iteratively minimize cost functions by moving weights in the opposite direction of the gradient."},
                    {"type": "knowledge_check", "question": "What does an eigenvalue represent in the context of PCA?", "options": [
                        "The classification label.",
                        "The amount of variance explained along its corresponding eigenvector direction.",
                        "The rate of gradient descent."
                    ], "correct_index": 1, "explanation": "In PCA, the eigenvalues of the covariance matrix measure the amount of data variance along each principal component."}
                ]
            }
        ]
    },
    {
        "slug": "ml-python-for-ml",
        "title": "Python for ML (NumPy & Pandas)",
        "domain_slug": "ml",
        "difficulty": "beginner",
        "subtopics": [
            {
                "title": "NumPy Arrays & Vectorization",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Vectorized Computations using NumPy"},
                    {"type": "text", "value": "Python lists are generic arrays of pointers. In contrast, **NumPy arrays** are contiguous, homogeneous memory blocks, allowing calculations to bypass Python interpreter overhead and execute in compiled C code. This process is called **Vectorization**."},
                    {"type": "code", "language": "python", "value": "import numpy as np\nimport time\n\nsize = 1000000\na = list(range(size))\n\n# Vectorized addition vs loop\nstart = time.time()\narr = np.array(a)\narr = arr + 1  # Vectorized operation in C\nprint(f'NumPy took {time.time() - start:.6f}s')"},
                    {"type": "callout", "kind": "tip", "title": "Broadcasting", "value": "Broadcasting allows mathematical operations between arrays of different shapes, dynamically stretching the smaller array to match the larger one's shape without copying data in memory."},
                    {"type": "knowledge_check", "question": "Why are vectorized NumPy operations faster than standard Python loops?", "options": [
                        "They run on the GPU.",
                        "They compile code to machine instructions at runtime.",
                        "They run compiled C code over contiguous, homogeneous memory blocks without interpreter overhead."
                    ], "correct_index": 2, "explanation": "NumPy uses contiguous C arrays and vectorized operations, avoiding type checks and loop overhead of the Python interpreter."}
                ]
            },
            {
                "title": "Pandas DataFrames & Manipulation",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Data Wrangling using Pandas"},
                    {"type": "text", "value": "Pandas provides the **DataFrame** structure for handling tabular data. It allows querying, merging, grouping, handling missing values, and executing statistical aggregates on millions of rows efficiently."},
                    {"type": "code", "language": "python", "value": "import pandas as pd\n\n# Create a DataFrame\ndata = {'Name': ['Alice', 'Bob'], 'Age': [25, 30], 'Salary': [70000, 80000]}\ndf = pd.DataFrame(data)\n\n# Filter and aggregate\nrich_employees = df[df['Salary'] > 75000]\nprint(df['Salary'].mean())"},
                    {"type": "callout", "kind": "warning", "title": "loc vs iloc", "value": "`.loc` is label-based indexing (selects rows/columns by string label), while `.iloc` is integer-position-based indexing (selects by index offsets)."},
                    {"type": "knowledge_check", "question": "What is the difference between `.loc` and `.iloc` in Pandas?", "options": [
                        "`.loc` is for columns, `.iloc` is for rows.",
                        "`.loc` searches by labels/names, while `.iloc` searches strictly by integer coordinates.",
                        "`.loc` works in place, while `.iloc` returns copies."
                    ], "correct_index": 1, "explanation": "`.loc` accesses rows/columns by label names; `.iloc` accesses by exact integer position offsets."}
                ]
            }
        ]
    }
]

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]
    
    # 1. Update/Upsert the Machine Learning domain card
    ml_domain = {
        "slug": "ml",
        "title": "Machine Learning",
        "description": "Understand supervised models, neural networks, deep learning, feature engineering, and model deployment strategies."
    }
    await db.domains.update_one({"slug": "ml"}, {"$set": ml_domain}, upsert=True)
    
    # 2. Clean out duplicate / old machine learning topics to avoid UI mess
    res = await db.topics.delete_many({"domain_slug": "ml"})
    print(f"Cleared {res.deleted_count} existing ML topics to prevent duplicates.")
    
    # Clean out "machine-learning" domain topics as well, and migrate the 3 existing deep ones
    # intro-ml, linear-regression, classification
    deep_topics = ["intro-ml", "linear-regression", "classification"]
    for t_slug in deep_topics:
        existing = await db.topics.find_one({"slug": t_slug})
        if existing:
            # Rebind domain_slug to "ml"
            await db.topics.update_one({"slug": t_slug}, {"$set": {"domain_slug": "ml"}})
            print(f"Successfully migrated deep topic {t_slug} to domain 'ml'.")
    
    # 3. Seed new rich topics
    inserted_count = 0
    for topic in TOPICS:
        await db.topics.update_one({"slug": topic["slug"]}, {"$set": topic}, upsert=True)
        inserted_count += 1
        print(f"Upserted clean ML topic: {topic['slug']}")
        
    print(f"Successfully seeded {inserted_count} clean ML topics.")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
