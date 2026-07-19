from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/education_platform")
db = client.education_platform

doc = {
    "domain_slug": "ml",
    "overview": "Machine Learning covers the discipline of building systems that learn patterns from data rather than being explicitly programmed with rules -- spanning classical statistical learning (regression, classification, clustering) through modern deep learning and the neural network architectures (including Transformers) behind today's most capable AI systems. This domain focuses on both the mathematical foundations and the practical, hands-on skill of building, evaluating, and deploying real models.",
    "why_important": "Machine Learning is one of the fastest-growing and highest-paid specializations in tech, driven by demand across nearly every industry for prediction, recommendation, and automation systems, and accelerated further by the current wave of generative AI. Companies increasingly expect even non-ML engineers to have working fluency with ML concepts, while dedicated ML roles (ML Engineer, Data Scientist, Applied Scientist) command some of the highest compensation in the industry.",
    "industries_using": [
        "Big Tech and AI-first startups",
        "Fintech (fraud detection, credit scoring, algorithmic trading)",
        "Healthcare (diagnostics, drug discovery)",
        "E-commerce and recommendation systems",
        "Autonomous vehicles and robotics",
        "Natural language processing and conversational AI"
    ],
    "future_scope": "Demand for ML talent continues to outpace supply, especially at the intersection of classical ML fundamentals and modern deep learning/Transformer architectures. As more companies move from experimenting with AI to deploying it in production, MLOps and deployment skills are becoming as valuable as model-building skills themselves -- a candidate who can both build and ship a model end-to-end is significantly more employable than one who can only do research-style notebook work.",
    "average_salary": "Rs 6-15 LPA entry-level (India, ML/Data Science roles at product companies), Rs 15-40+ LPA for experienced ML Engineers -- 100k-220k USD+ entry-level in the US, significantly higher at top AI labs",
    "skills_required": [
        "Python and core data libraries (NumPy, Pandas, scikit-learn)",
        "Linear algebra, probability, and statistics fundamentals",
        "Supervised and unsupervised learning algorithms",
        "Model evaluation and validation techniques",
        "Neural network fundamentals and at least one deep learning framework (PyTorch or TensorFlow)",
        "Feature engineering and data preprocessing",
        "Basic understanding of deploying and monitoring models in production"
    ],
    "prerequisites": [
        "Python programming fundamentals",
        "Basic linear algebra and statistics (or willingness to learn alongside)",
        "Comfort with Jupyter notebooks and data manipulation"
    ],
    "roadmap": [
        {
            "tier": "beginner",
            "items": [
                "Python for data: NumPy arrays, Pandas DataFrames",
                "Data visualization: Matplotlib, Seaborn",
                "Math foundations: linear algebra basics, probability, descriptive statistics",
                "Supervised learning: linear regression, logistic regression",
                "Train/test splits and basic model evaluation metrics"
            ]
        },
        {
            "tier": "intermediate",
            "items": [
                "Classification algorithms: decision trees, random forests, SVMs, k-NN",
                "Unsupervised learning: k-means clustering, PCA",
                "Model evaluation: cross-validation, confusion matrix, ROC-AUC, precision/recall",
                "Feature engineering and handling missing/categorical data",
                "Regularization: L1/L2, bias-variance tradeoff"
            ]
        },
        {
            "tier": "advanced",
            "items": [
                "Neural network fundamentals: perceptrons, backpropagation, activation functions",
                "Deep learning frameworks: PyTorch or TensorFlow/Keras",
                "CNNs for vision, RNNs/Transformers for sequence data",
                "Hyperparameter tuning and experiment tracking",
                "Model deployment basics: serving a model via an API, monitoring drift"
            ]
        }
    ],
    "topics": [
        {
            "name": "Python for ML (NumPy & Pandas)",
            "description": "The core data manipulation stack for ML work: NumPy for numerical arrays and vectorized operations, Pandas for tabular data manipulation and cleaning.",
            "importance": "Nearly every ML workflow starts with loading and cleaning data in Pandas and doing numerical operations in NumPy; fluency here is assumed before any modeling begins.",
            "difficulty": "beginner",
            "estimated_time": "1-1.5 weeks",
            "prerequisites": ["Basic Python programming"],
            "resources": {
                "documentation": "https://pandas.pydata.org/docs/user_guide/10min.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLeo1K3hjS3usJuxZZUBdjAcilgfQXFmC1",
                "articles": [
                    "https://www.geeksforgeeks.org/pandas-tutorial/"
                ],
                "notes": "Practice vectorized NumPy operations instead of Python for-loops -- understanding why vectorization is faster is a common interview question.",
                "practice_platform": "Kaggle Learn (Pandas micro-course)",
                "cheat_sheet": "NumPy: vectorized array math, broadcasting; Pandas: DataFrame = table, Series = column, groupby/merge/pivot for aggregation"
            },
            "practice_questions": [
                "Load a CSV, handle missing values, and compute summary statistics using Pandas",
                "Explain what broadcasting means in NumPy with an example",
                "Write a groupby operation to compute average value per category",
                "What is the difference between .loc and .iloc in Pandas?",
                "Why is a vectorized NumPy operation faster than a Python for-loop?"
            ],
            "projects": [
                "Clean and explore a real messy dataset (e.g. a Kaggle CSV), producing summary stats and 3 visualizations"
            ],
            "interview_questions": [
                "How would you handle missing data in a dataset -- what are your options and tradeoffs?",
                "Explain the difference between a Pandas Series and DataFrame",
                "What is the difference between merge, join, and concat in Pandas?",
                "How do you efficiently apply a custom function across a large DataFrame?"
            ]
        },
        {
            "name": "Math Foundations (Linear Algebra, Probability & Statistics)",
            "description": "The mathematical toolkit underlying ML: vectors/matrices and their operations, probability distributions, and statistical concepts like mean/variance/hypothesis testing.",
            "importance": "Nearly every ML algorithm is a direct application of linear algebra and probability; understanding the math is what separates someone who can tune a model from someone who understands why it works or fails.",
            "difficulty": "beginner",
            "estimated_time": "2-3 weeks",
            "prerequisites": [],
            "resources": {
                "documentation": "https://www.khanacademy.org/math/linear-algebra",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
                "articles": [
                    "https://www.geeksforgeeks.org/probability-and-statistics-for-machine-learning/"
                ],
                "notes": "Focus on building geometric intuition for vectors/matrices (3Blue1Brown's Essence of Linear Algebra series is excellent for this) rather than pure formula memorization.",
                "practice_platform": "Khan Academy Linear Algebra & Statistics",
                "cheat_sheet": "Dot product = similarity/projection, matrix multiplication = composed linear transformations, variance = spread, Bayes' theorem = updating belief with evidence"
            },
            "practice_questions": [
                "Explain what a dot product represents geometrically",
                "What is the difference between covariance and correlation?",
                "State Bayes' theorem and explain each term in words",
                "Why does ML use gradient descent instead of solving equations directly for most models?",
                "What is the difference between population and sample variance?"
            ],
            "projects": [
                "Implement matrix multiplication and a basic gradient descent optimizer from scratch using only NumPy"
            ],
            "interview_questions": [
                "Explain eigenvalues and eigenvectors and where they show up in ML (hint: PCA)",
                "What is the Central Limit Theorem and why does it matter for ML?",
                "Explain the difference between Type I and Type II error",
                "Why do we normalize/standardize features before training many ML models?"
            ]
        },
        {
            "name": "Supervised Learning: Regression & Classification",
            "description": "Learning to predict a target variable from labeled examples -- linear/logistic regression, decision trees, random forests, SVMs, and k-NN -- the core toolkit for most real-world ML problems.",
            "importance": "The most commonly used category of ML in production; nearly every ML interview includes questions on when and why to choose one supervised algorithm over another.",
            "difficulty": "intermediate",
            "estimated_time": "3 weeks",
            "prerequisites": ["Python for ML (NumPy & Pandas)", "Math Foundations (Linear Algebra, Probability & Statistics)"],
            "resources": {
                "documentation": "https://scikit-learn.org/stable/supervised_learning.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/supervised-machine-learning/"
                ],
                "notes": "Implement linear regression from scratch with gradient descent once, then use scikit-learn for everything after -- the from-scratch version builds real intuition that using a library alone won't.",
                "practice_platform": "Kaggle competitions (start with Titanic / House Prices)",
                "cheat_sheet": "Regression predicts continuous values, classification predicts categories; decision trees split on feature thresholds; random forests average many trees to reduce variance"
            },
            "practice_questions": [
                "Explain the difference between linear regression and logistic regression",
                "How does a decision tree decide which feature to split on?",
                "What is the bias-variance tradeoff and how does it relate to overfitting?",
                "When would you choose a random forest over a single decision tree?",
                "Explain how k-NN makes predictions and its main weakness"
            ],
            "projects": [
                "Build and compare 3 classifiers (logistic regression, random forest, SVM) on a real dataset, reporting accuracy/precision/recall for each"
            ],
            "interview_questions": [
                "Why is accuracy a misleading metric for an imbalanced classification dataset?",
                "Explain regularization (L1 vs L2) and why it helps prevent overfitting",
                "What is the kernel trick in SVMs, at a high level?",
                "How would you handle a classification problem with 100+ features and only 500 rows?"
            ]
        },
        {
            "name": "Unsupervised Learning: Clustering & Dimensionality Reduction",
            "description": "Finding structure in unlabeled data -- clustering algorithms like k-means and hierarchical clustering, and dimensionality reduction techniques like PCA.",
            "importance": "Essential for exploratory data analysis, customer segmentation, anomaly detection, and as a preprocessing step (dimensionality reduction) before supervised learning on high-dimensional data.",
            "difficulty": "intermediate",
            "estimated_time": "1.5-2 weeks",
            "prerequisites": ["Math Foundations (Linear Algebra, Probability & Statistics)"],
            "resources": {
                "documentation": "https://scikit-learn.org/stable/modules/clustering.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLblh5JKOoLUIzaEkCLIUxQFjPIlapw8nU",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/clustering-in-machine-learning/"
                ],
                "notes": "Run k-means on a 2D dataset and plot the clusters visually before trusting it on real high-dimensional data -- visualizing the algorithm's behavior builds real intuition.",
                "practice_platform": "Kaggle Learn Unsupervised Learning micro-course",
                "cheat_sheet": "k-means: partition into k clusters by minimizing within-cluster distance; PCA: project onto directions of maximum variance to reduce dimensions"
            },
            "practice_questions": [
                "How does the k-means algorithm work, step by step?",
                "How would you choose the right value of k for k-means (elbow method)?",
                "What does PCA actually do, and why does it help with high-dimensional data?",
                "What's the difference between k-means and hierarchical clustering?",
                "When would unsupervised learning be more appropriate than supervised learning?"
            ],
            "projects": [
                "Perform customer segmentation on a retail dataset using k-means, then visualize clusters after PCA reduction to 2D"
            ],
            "interview_questions": [
                "What are the limitations of k-means (e.g. assumes spherical clusters)?",
                "Explain the difference between PCA and t-SNE at a high level",
                "How would you evaluate clustering quality without ground-truth labels?",
                "What is the curse of dimensionality and how does it affect distance-based algorithms?"
            ]
        },
        {
            "name": "Model Evaluation & Validation",
            "description": "Rigorously measuring model performance: train/validation/test splits, cross-validation, and metrics beyond accuracy (precision, recall, F1, ROC-AUC) for different problem types.",
            "importance": "A model that looks good on training data but hasn't been properly validated is one of the most common and costly mistakes in applied ML; interviewers heavily probe this to separate candidates who can build a real, trustworthy model from those who can only fit one.",
            "difficulty": "intermediate",
            "estimated_time": "1-1.5 weeks",
            "prerequisites": ["Supervised Learning: Regression & Classification"],
            "resources": {
                "documentation": "https://scikit-learn.org/stable/modules/model_evaluation.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLblh5JKOoLUIcdlgu78MnlATeyx4cEVeR",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/machine-learning-model-evaluation/"
                ],
                "notes": "Always compute a confusion matrix by hand at least once for a real classifier -- it makes precision/recall/F1 intuitive rather than memorized formulas.",
                "practice_platform": "Practice on any Kaggle classification dataset, focus on metrics not just accuracy",
                "cheat_sheet": "Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = harmonic mean of both; use recall-focused metrics when false negatives are costly (e.g. disease detection)"
            },
            "practice_questions": [
                "Explain precision and recall and give a real scenario where you'd prioritize one over the other",
                "What is k-fold cross-validation and why is it more reliable than a single train/test split?",
                "What does an ROC curve show, and what does AUC mean?",
                "Why would you never evaluate a model on the same data it was trained on?",
                "What is data leakage and give an example of how it happens accidentally"
            ],
            "projects": [
                "Build a fraud-detection classifier on an imbalanced dataset and report precision/recall/F1/ROC-AUC, explaining tradeoffs"
            ],
            "interview_questions": [
                "How would you evaluate a model for a highly imbalanced classification problem (e.g. 1% fraud rate)?",
                "Explain stratified k-fold cross-validation and why it matters for imbalanced data",
                "What is the difference between validation set and test set, and why do you need both?",
                "How would you detect if your model is overfitting versus underfitting?"
            ]
        },
        {
            "name": "Neural Networks & Deep Learning Fundamentals",
            "description": "The building blocks of deep learning: perceptrons, activation functions, backpropagation, and how these compose into the networks (CNNs, RNNs, Transformers) behind modern AI.",
            "importance": "Deep learning powers nearly all current state-of-the-art AI systems, from image recognition to large language models; understanding backpropagation and network architecture is essential for any ML role beyond purely classical statistics.",
            "difficulty": "advanced",
            "estimated_time": "3-4 weeks",
            "prerequisites": ["Math Foundations (Linear Algebra, Probability & Statistics)", "Supervised Learning: Regression & Classification"],
            "resources": {
                "documentation": "https://pytorch.org/tutorials/beginner/basics/intro.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/introduction-to-artificial-neutral-networks/"
                ],
                "notes": "Implement a tiny neural network with forward and backward passes using only NumPy before switching to PyTorch -- it makes backpropagation genuinely understood rather than a black box the framework handles.",
                "practice_platform": "PyTorch official tutorials + Kaggle deep learning competitions",
                "cheat_sheet": "Forward pass: compute predictions; backward pass (backprop): compute gradients via chain rule; activation functions (ReLU, sigmoid) add non-linearity"
            },
            "practice_questions": [
                "Explain backpropagation in your own words, step by step",
                "Why do neural networks need non-linear activation functions?",
                "What is the vanishing gradient problem and how do modern architectures address it?",
                "Explain the difference between a CNN and a standard fully-connected network, and why CNNs work well for images",
                "What is an epoch, batch, and learning rate, and how do they interact during training?"
            ],
            "projects": [
                "Build and train an image classifier (e.g. digits or fashion items) using a CNN in PyTorch or TensorFlow, reporting accuracy on a held-out test set"
            ],
            "interview_questions": [
                "What is dropout and why does it help prevent overfitting?",
                "Explain the difference between batch, mini-batch, and stochastic gradient descent",
                "At a high level, what problem does the attention mechanism in Transformers solve compared to RNNs?",
                "What is transfer learning and why is it useful when you have limited training data?"
            ]
        },
        {
            "name": "Feature Engineering & Data Preprocessing",
            "description": "Transforming raw data into model-ready inputs: handling missing values, encoding categorical variables, scaling/normalization, and creating new predictive features from existing data.",
            "importance": "Widely considered to have more impact on real-world model performance than algorithm choice -- 'garbage in, garbage out' is especially true in ML, and this is where most of the practical time in real projects actually goes.",
            "difficulty": "intermediate",
            "estimated_time": "1.5-2 weeks",
            "prerequisites": ["Python for ML (NumPy & Pandas)"],
            "resources": {
                "documentation": "https://scikit-learn.org/stable/modules/preprocessing.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLblh5JKOoLUJJpBNfk8_YadPwDTO2SCbx",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/feature-engineering-for-machine-learning/"
                ],
                "notes": "Always fit any scaler/encoder only on training data, then transform both train and test with it -- fitting on the full dataset before splitting is a subtle but very common source of data leakage.",
                "practice_platform": "Kaggle Learn Feature Engineering micro-course",
                "cheat_sheet": "One-hot encoding for nominal categories, ordinal encoding for ordered categories, StandardScaler for zero-mean/unit-variance, MinMaxScaler for bounded ranges"
            },
            "practice_questions": [
                "What's the difference between one-hot encoding and label encoding, and when would you use each?",
                "Why do you fit a scaler only on training data, not the full dataset?",
                "How would you handle a categorical feature with 10,000 unique values?",
                "Explain feature scaling and why some algorithms (like k-NN, SVM) need it more than others (like decision trees)",
                "What is a common technique for creating new features from a date/timestamp column?"
            ],
            "projects": [
                "Take a raw, messy real-world dataset and build a complete preprocessing pipeline (missing values, encoding, scaling) using scikit-learn Pipelines"
            ],
            "interview_questions": [
                "What is target leakage, and how does it differ from ordinary data leakage?",
                "How would you engineer features from free-text data without deep learning (e.g. TF-IDF)?",
                "What's the risk of using mean imputation for missing values, and what alternatives exist?",
                "Why might you create interaction features between two variables?"
            ]
        },
        {
            "name": "Model Deployment & MLOps Basics",
            "description": "Taking a trained model from a notebook to production: serving predictions via an API, containerization, and basic monitoring for model/data drift over time.",
            "importance": "A model that never leaves a Jupyter notebook delivers zero business value; deployment and monitoring skills increasingly distinguish employable ML engineers from those who can only do research-style experimentation.",
            "difficulty": "advanced",
            "estimated_time": "2 weeks",
            "prerequisites": ["Supervised Learning: Regression & Classification", "Model Evaluation & Validation"],
            "resources": {
                "documentation": "https://scikit-learn.org/stable/model_persistence.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLblh5JKOoLUL3IJ4-yor0yzUwZgTSDdt2",
                "articles": [
                    "https://www.geeksforgeeks.org/machine-learning/mlops-machine-learning-operations/"
                ],
                "notes": "Deploy at least one real model behind a REST endpoint (even a toy one) -- serialization, loading, and serving a model raises practical issues that reading about MLOps alone won't surface.",
                "practice_platform": "Build and deploy a personal project end-to-end (e.g. on Render, Railway, or a free-tier cloud VM)",
                "cheat_sheet": "pickle/joblib to serialize a scikit-learn model; FastAPI to serve predictions; Docker to containerize; monitor for data drift (input distribution changing) over time"
            },
            "practice_questions": [
                "How would you serve a trained scikit-learn model as a REST API?",
                "What is model drift, and how would you detect it in production?",
                "Why is it risky to retrain a model without any validation before deploying it?",
                "What's the difference between batch inference and real-time (online) inference?",
                "How would you version a model so you can roll back to a previous version if needed?"
            ],
            "projects": [
                "Deploy a trained classification model as a FastAPI endpoint, containerize it with Docker, and write a basic health-check/monitoring script"
            ],
            "interview_questions": [
                "Walk through the full lifecycle of an ML model from training to production monitoring",
                "What is A/B testing in the context of ML model deployment, and why is it used?",
                "How would you design a system to retrain a model automatically as new data arrives?",
                "What are the risks of deploying a model without a rollback plan?"
            ]
        }
    ],
    "skills": [
        {
            "name": "Data Manipulation (NumPy/Pandas)",
            "description": "Cleaning, transforming, and analyzing tabular data efficiently in Python.",
            "importance": "The foundational daily skill for any ML or data role.",
            "level": "beginner",
            "estimated_hours": 20
        },
        {
            "name": "Classical ML Algorithms",
            "description": "Applying and reasoning about regression, classification, and clustering algorithms.",
            "importance": "Core to the majority of real-world, production ML use cases.",
            "level": "intermediate",
            "estimated_hours": 35
        },
        {
            "name": "Model Evaluation",
            "description": "Rigorously measuring and validating model performance using the right metrics for the problem.",
            "importance": "Distinguishes a trustworthy model from one that only looks good on paper.",
            "level": "intermediate",
            "estimated_hours": 15
        },
        {
            "name": "Deep Learning",
            "description": "Building and training neural networks, including CNNs and Transformer-based architectures.",
            "importance": "Required for state-of-the-art performance on vision, language, and generative AI tasks.",
            "level": "advanced",
            "estimated_hours": 50
        },
        {
            "name": "MLOps & Deployment",
            "description": "Serving, monitoring, and maintaining ML models in production environments.",
            "importance": "Increasingly required to turn ML work into actual business value.",
            "level": "advanced",
            "estimated_hours": 20
        }
    ],
    "practice_platforms": [
        "Kaggle",
        "Google Colab (free GPU access)",
        "GeeksforGeeks",
        "Papers with Code",
        "Hugging Face (for modern NLP/Transformers)"
    ],
    "projects": [
        {
            "title": "House Price Predictor",
            "description": "A regression model predicting housing prices from structured features, including a full feature engineering and evaluation pipeline.",
            "skills_learned": ["Regression", "Feature engineering", "Model evaluation"],
            "technologies_used": ["Python", "scikit-learn", "Pandas"],
            "github_ideas": ["house-price-predictor"],
            "tier": "beginner"
        },
        {
            "title": "Customer Churn Classifier",
            "description": "A classification model predicting customer churn on an imbalanced dataset, with proper precision/recall/F1 evaluation.",
            "skills_learned": ["Classification", "Imbalanced data handling", "Model evaluation"],
            "technologies_used": ["Python", "scikit-learn"],
            "github_ideas": ["customer-churn-predictor"],
            "tier": "intermediate"
        },
        {
            "title": "Image Classifier with CNN",
            "description": "A convolutional neural network trained from scratch (or via transfer learning) to classify images into multiple categories.",
            "skills_learned": ["Deep learning", "CNNs", "Transfer learning"],
            "technologies_used": ["Python", "PyTorch or TensorFlow"],
            "github_ideas": ["cnn-image-classifier"],
            "tier": "advanced"
        },
        {
            "title": "End-to-End Deployed ML Model",
            "description": "A trained model served via a FastAPI endpoint, containerized with Docker, with a basic monitoring/health-check script -- covering the full lifecycle from training to production.",
            "skills_learned": ["Model deployment", "API design", "Basic MLOps"],
            "technologies_used": ["Python", "FastAPI", "Docker", "scikit-learn"],
            "github_ideas": ["ml-model-deployment-demo"],
            "tier": "advanced"
        }
    ],
    "interview_prep": {
        "important_topics": [
            "Bias-variance tradeoff and overfitting",
            "Model evaluation metrics for classification and regression",
            "Neural network fundamentals and backpropagation",
            "Feature engineering and data preprocessing",
            "Deployment and monitoring of ML models in production"
        ],
        "frequently_asked_questions": [
            "Walk me through an ML project you've built end-to-end, from data to deployment",
            "How did you validate that your model actually generalizes to new data?",
            "Describe a time your model underperformed and how you debugged it"
        ],
        "coding_questions": [
            "Implement linear regression using gradient descent from scratch with NumPy",
            "Implement k-means clustering from scratch",
            "Write code to compute precision, recall, and F1 score without using a library",
            "Implement a simple k-NN classifier from scratch"
        ],
        "hr_questions": [
            "Tell me about a time you had to explain a technical ML concept to a non-technical stakeholder",
            "How do you stay current with the fast pace of ML research?",
            "Describe a project where the data quality was poor -- what did you do?"
        ],
        "system_design_questions": [
            "Design a recommendation system for an e-commerce platform",
            "Design a real-time fraud detection system",
            "Design a system to retrain and redeploy a model automatically as new data arrives"
        ]
    },
    "resume_tips": [
        "List specific frameworks/libraries used (PyTorch, scikit-learn, XGBoost) rather than just 'Machine Learning'",
        "Quantify model performance and impact where possible (e.g. 'improved F1 score from 0.71 to 0.86')",
        "Include at least one project that goes beyond a notebook -- ideally something deployed or served via an API",
        "Mention the specific evaluation metrics used and why, not just 'built a model'",
        "If applicable, mention exposure to MLOps tools (Docker, MLflow, model versioning) -- this is increasingly a differentiator"
    ],
    "certifications": [
        "Andrew Ng's Machine Learning Specialization on Coursera (Paid, financial aid available, widely respected)",
        "fast.ai Practical Deep Learning for Coders (Free)",
        "Google Machine Learning Crash Course (Free)",
        "TensorFlow Developer Certificate (Paid)"
    ],
    "company_prep": [
        {
            "group_name": "Product / AI-first Companies",
            "example_companies": ["Google", "Meta", "Microsoft", "OpenAI", "Amazon"],
            "focus_areas": ["ML fundamentals depth", "Deep learning", "System design for ML systems", "Statistics", "Coding (Python/DSA)"]
        },
        {
            "group_name": "Traditional / Service Companies with ML teams",
            "example_companies": ["TCS", "Infosys", "Accenture", "Wipro", "Cognizant"],
            "focus_areas": ["Basic ML concepts", "SQL", "Python fundamentals", "Communication", "Business understanding of ML use cases"]
        }
    ]
}

result = db.domain_details.update_one(
    {"domain_slug": "ml"},
    {"$set": doc},
    upsert=True
)

print(f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}")