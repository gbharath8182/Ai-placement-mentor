import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    topic = {
        "domain_slug": "machine-learning",
        "slug": "classification",
        "title": "Classification",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Why Not Linear Regression for Classification?",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "The Response Variable Is Now Qualitative"},
                    {"type": "text", "value": "Classification problems predict a **qualitative** response (e.g. spam/not-spam, disease A/B/C) rather than a continuous number. It might seem tempting to just encode categories as numbers (0, 1, 2) and run linear regression, but this fails for two reasons."},
                    {"type": "list", "ordered": True, "items": [
                        "For a response with more than 2 categories, encoding as 0/1/2 imposes a false **ordering and equal spacing** between categories that usually doesn't exist (is 'stroke' really twice as far from 'drug overdose' as 'seizure'?)",
                        "Even for a 2-category response encoded as 0/1, linear regression can produce predictions **outside the [0,1] range**, which can't be sensibly interpreted as a probability"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "The clean answer to 'why not just use linear regression here?' is: linear regression assumes an ordered, equally-spaced numeric response and can output values outside a valid probability range -- classification methods are built specifically to respect the 0-to-1, unordered nature of class labels."},
                    {"type": "text", "value": "This motivates a family of methods -- logistic regression, LDA, and KNN among them -- that directly model either the probability of class membership or a decision boundary between classes."}
                ]
            },
            {
                "title": "Logistic Regression",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Modeling Probability with the Logistic Function"},
                    {"type": "text", "value": "Logistic regression models the probability that Y belongs to a class, using the **logistic (sigmoid) function**, which is guaranteed to output a value between 0 and 1 for any input:\n\np(X) = e^(b0 + b1*X) / (1 + e^(b0 + b1*X))"},
                    {"type": "code", "language": "python", "value": "import math\n\ndef sigmoid(z):\n    return 1 / (1 + math.exp(-z))\n\ndef predict_proba(x, b0, b1):\n    z = b0 + b1 * x\n    return sigmoid(z)"},
                    {"type": "text", "value": "Rearranging the logistic function gives the **log-odds (logit)**:\n\nlog(p(X) / (1 - p(X))) = b0 + b1*X\n\nThis is linear in X -- so logistic regression is, underneath, a linear model of the log-odds, not of the probability itself. Coefficients are estimated via **maximum likelihood**, not least squares, since there's no closed-form solution."},
                    {"type": "callout", "kind": "important", "title": "Interpreting Coefficients", "value": "A one-unit increase in X changes the **log-odds** by b1, not the probability by b1. This is a common interview trap: b1 does NOT mean 'a one-unit increase in X increases the probability of the outcome by b1'."},
                    {"type": "list", "ordered": False, "items": [
                        "A typical decision rule: classify as positive if p(X) > 0.5, though this threshold can be tuned",
                        "Logistic regression naturally extends to multiple predictors (multiple logistic regression)",
                        "For more than 2 classes, multinomial logistic regression or softmax regression generalizes the same idea"
                    ]}
                ]
            },
            {
                "title": "Linear Discriminant Analysis (LDA)",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "An Alternative Approach via Bayes' Theorem"},
                    {"type": "text", "value": "LDA models the distribution of the predictors X **separately for each class**, then uses Bayes' theorem to flip these into estimates of P(Y=k | X=x). Unlike logistic regression, which directly models P(Y|X), LDA models P(X|Y) and P(Y), then derives P(Y|X) indirectly."},
                    {"type": "text", "value": "LDA assumes the predictors within each class follow a (multivariate) normal distribution with a **class-specific mean but a shared covariance matrix** across all classes. This shared-covariance assumption is what makes the resulting decision boundary linear."},
                    {"type": "list", "ordered": False, "items": [
                        "LDA tends to outperform logistic regression when classes are well-separated, where logistic regression's parameter estimates can become unstable",
                        "LDA is more stable than logistic regression when n is small and predictors X are approximately normally distributed within each class",
                        "LDA extends naturally to more than 2 response classes, which plain logistic regression does not do as cleanly",
                        "Quadratic Discriminant Analysis (QDA) relaxes the shared-covariance assumption, allowing each class its own covariance matrix, at the cost of more parameters to estimate"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "If asked 'LDA vs. logistic regression -- when would you pick one over the other?', lead with the well-separated-classes and normality assumptions -- that's the crux of the comparison, not just 'they're both linear classifiers.'"}
                ]
            },
            {
                "title": "K-Nearest Neighbors (KNN)",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "A Non-Parametric Alternative"},
                    {"type": "text", "value": "KNN takes a completely different approach: given a test point x0 and a chosen K, it finds the K training points closest to x0 (typically by Euclidean distance), then classifies x0 as the **majority class** among those K neighbors. There is no model to fit -- KNN is a **non-parametric** method that makes no assumption about the shape of the decision boundary."},
                    {"type": "code", "language": "python", "value": "def knn_predict(x0, X_train, y_train, k):\n    distances = [(sum((x0[i] - xt[i]) ** 2 for i in range(len(x0))) ** 0.5, label)\n                 for xt, label in zip(X_train, y_train)]\n    distances.sort(key=lambda pair: pair[0])\n    k_nearest_labels = [label for _, label in distances[:k]]\n    return max(set(k_nearest_labels), key=k_nearest_labels.count)"},
                    {"type": "list", "ordered": False, "items": [
                        "**Small K** (e.g. K=1): low bias, high variance -- a very flexible, wiggly decision boundary that can overfit",
                        "**Large K**: high bias, low variance -- an increasingly smooth, near-linear decision boundary that can underfit",
                        "K is typically chosen via cross-validation, not guessed",
                        "KNN's performance degrades sharply in high dimensions (the 'curse of dimensionality') since 'nearest' neighbors stop being meaningfully close as feature count grows"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "Interview Trap", "value": "Don't say 'a smaller K is always more accurate.' K controls a bias-variance tradeoff just like model flexibility elsewhere in this curriculum -- too small overfits, too large underfits, and the right K is data-dependent."}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print("Inserted topic with id:", result.inserted_id)

asyncio.run(main())
