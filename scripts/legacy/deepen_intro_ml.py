import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    new_subtopics = [
        {
            "title": "What Is Statistical Learning?",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "The Statistical Learning Framework"},
                {"type": "text", "value": "Machine Learning (ML) is a subset of AI that allows systems to learn patterns from data rather than following hand-written rules. Formally, we assume there is some true relationship between a set of input variables X and an output Y, written as **Y = f(X) + e**, where f is an unknown function and e is random error independent of X with mean zero. Statistical learning is the collection of approaches for estimating f."},
                {"type": "text", "value": "ML problems are primarily split into two paradigms:\n1. **Supervised Learning** -- the training data includes the true output Y for each observation, so the model learns to map X to Y (e.g. regression, classification).\n2. **Unsupervised Learning** -- there is no labeled Y at all; the model instead looks for structure or grouping in X alone (e.g. clustering, dimensionality reduction)."},
                {"type": "list", "ordered": False, "items": [
                    "Supervised: predicting house prices from square footage (regression)",
                    "Supervised: classifying an email as spam or not spam (classification)",
                    "Unsupervised: grouping customers into segments with no predefined labels (clustering)",
                    "Unsupervised: reducing hundreds of features down to a handful that explain most of the variance (dimensionality reduction / PCA)"
                ]},
                {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "If asked 'why do we even try to estimate f?', the answer is always one of two reasons: **prediction** (we only care about the output Y, not the mechanics) or **inference** (we care about how each X affects Y). Naming this distinction immediately signals you understand the goal of the model, not just the mechanics -- see the next subtopic."},
                {"type": "resource_link", "label": "Paper: A Few Useful Things to Know About Machine Learning (Domingos)", "url": "https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf"}
            ]
        },
        {
            "title": "Prediction vs. Inference",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Two Different Reasons to Estimate f"},
                {"type": "text", "value": "There are two distinct goals when estimating f, and confusing them leads to picking the wrong kind of model:"},
                {"type": "list", "ordered": True, "items": [
                    "**Prediction** -- we treat f as a black box. We only care that our estimate f-hat produces accurate predictions of Y given new X values. Interpretability doesn't matter; accuracy does.",
                    "**Inference** -- we want to understand *how* Y changes as a function of X1, X2, ... Xp. Which predictors matter? Is the relationship positive or negative? Linear or more complex? Here interpretability matters as much as, or more than, raw accuracy."
                ]},
                {"type": "text", "value": "This distinction directly drives model choice. A hospital predicting whether a patient will be readmitted (prediction) can use a complex, less interpretable model like a boosted tree if it improves accuracy. A hospital trying to understand *which* factors drive readmission so it can change policy (inference) needs a simpler, interpretable model like linear or logistic regression, even if it's slightly less accurate."},
                {"type": "callout", "kind": "warning", "title": "Interview Trap", "value": "Don't default to 'the most accurate model wins.' If the interviewer's scenario is about understanding *why* something happens (inference), a highly flexible black-box model is often the *wrong* answer even if it scores higher on a leaderboard metric."},
                {"type": "code", "language": "python", "value": "# Prediction-oriented: black box is fine\nfrom sklearn.ensemble import GradientBoostingClassifier\nmodel = GradientBoostingClassifier()\nmodel.fit(X_train, y_train)\ny_pred = model.predict(X_new)  # we only care that this is accurate\n\n# Inference-oriented: interpretability matters\nimport statsmodels.api as sm\nmodel = sm.OLS(y_train, sm.add_constant(X_train)).fit()\nprint(model.summary())  # we care about the coefficients themselves"}
            ]
        },
        {
            "title": "Assessing Model Accuracy",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Measuring How Good f-hat Really Is"},
                {"type": "text", "value": "In regression, the most common way to measure how well predictions match observed data is the **Mean Squared Error (MSE)**: the average of the squared differences between actual and predicted values. A small training MSE means the model fits the training data closely."},
                {"type": "code", "language": "python", "value": "def mse(y_true, y_pred):\n    n = len(y_true)\n    return sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / n"},
                {"type": "text", "value": "The critical insight: **we don't actually care about training MSE.** We care about how well the model predicts on *unseen* test data, because that's what the model will face in production. A model can achieve near-zero training MSE by memorizing the training set, yet perform terribly on new data."},
                {"type": "list", "ordered": False, "items": [
                    "Training MSE always decreases (or stays flat) as model flexibility increases",
                    "Test MSE typically decreases at first, then increases again once the model starts overfitting",
                    "The gap between training MSE and test MSE is itself a signal of overfitting",
                    "Cross-validation exists specifically because we usually don't have a true, separate test set available during development"
                ]},
                {"type": "callout", "kind": "important", "title": "The Core Tension", "value": "There is no single model that minimizes test MSE across every dataset -- this is why model selection and cross-validation exist, and why 'just use the most flexible model' is never the right interview answer."}
            ]
        },
        {
            "title": "The Bias-Variance Tradeoff",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Decomposing Expected Test Error"},
                {"type": "text", "value": "The expected test MSE at a point x0, averaged over many training sets, can be decomposed into three terms:\n\n**E[(y0 - f-hat(x0))^2] = Var(f-hat(x0)) + [Bias(f-hat(x0))]^2 + Var(e)**\n\nThat is: **Variance + Bias-squared + Irreducible Error**. To minimize expected test error, a method must simultaneously achieve *low variance* and *low bias*."},
                {"type": "text", "value": "**Bias** is the error introduced by approximating a real-world, possibly complex relationship with a simpler model (e.g. assuming a nonlinear relationship is linear). **Variance** is how much f-hat would change if estimated using a different training dataset -- a high-variance model overreacts to small fluctuations in the training data."},
                {"type": "list", "ordered": False, "items": [
                    "Inflexible methods (e.g. linear regression): high bias, low variance",
                    "Highly flexible methods (e.g. deep decision trees, high-degree polynomials): low bias, high variance",
                    "As flexibility increases, bias tends to decrease while variance tends to increase -- this is the tradeoff",
                    "Test error typically forms a U-shape as flexibility increases: it improves as bias drops, then worsens as variance dominates"
                ]},
                {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "When asked to explain overfitting vs. underfitting, the bias-variance tradeoff is the underlying mechanism: **underfitting = high bias**, **overfitting = high variance**. Naming this decomposition explicitly is a strong signal in an ML interview."},
                {"type": "divider"},
                {"type": "text", "value": "This tradeoff is why techniques like regularization (ridge, lasso), pruning, and cross-validation exist -- they exist specifically to manage variance without letting bias grow unacceptably large."}
            ]
        }
    ]

    result = await db.topics.update_one(
        {"slug": "intro-ml"},
        {"$set": {"subtopics": new_subtopics}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

asyncio.run(main())
