import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    new_subtopics = [
        {
            "title": "Simple Linear Regression",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Formulating Simple Linear Regression"},
                {"type": "text", "value": "Simple linear regression models the relationship between one predictor X and a response Y as a straight line:\n\nY = b0 + b1*X + e\n\nwhere b0 is the intercept, b1 is the slope, and e is irreducible random error. Given b0 and b1, we predict y-hat = b0 + b1*x for any new x."},
                {"type": "text", "value": "We choose b0 and b1 to minimize the **Residual Sum of Squares (RSS)** -- the sum of squared differences between each observed yi and the model's prediction. The values that minimize RSS are called the **least squares coefficient estimates**, and they have a closed-form solution derived from calculus (no iteration required for simple linear regression)."},
                {"type": "code", "language": "python", "value": "def least_squares_fit(x, y):\n    n = len(x)\n    x_mean = sum(x) / n\n    y_mean = sum(y) / n\n    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))\n    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))\n    b1 = numerator / denominator\n    b0 = y_mean - b1 * x_mean\n    return b0, b1"},
                {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "If asked to derive the least squares formula, remember it minimizes RSS = sum((yi - b0 - b1*xi)^2). Taking partial derivatives with respect to b0 and b1 and setting them to zero gives the closed-form solution -- no gradient descent needed for the simple case."},
                {"type": "resource_link", "label": "Free Textbook: Elements of Statistical Learning (Hastie et al.) PDF", "url": "https://hastie.su.domains/ElemStatLearn/printings/ESLII_print12_toc.pdf"}
            ]
        },
        {
            "title": "Estimating Coefficients: Least Squares & Gradient Descent",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Two Ways to Find the Best-Fit Line"},
                {"type": "text", "value": "For simple and multiple linear regression, least squares has a closed-form (analytical) solution. But as models grow more complex (thousands of features, or models beyond linear regression like logistic regression and neural networks), there is often no closed-form solution -- this is where **gradient descent** comes in."},
                {"type": "text", "value": "Gradient descent is an iterative optimization algorithm. It starts with an initial guess for the parameters, computes the gradient (direction of steepest increase) of the cost function, and takes a small step in the *opposite* direction, repeating until convergence."},
                {"type": "code", "language": "python", "value": "def gradient_descent(x, y, learning_rate=0.01, iterations=1000):\n    n = len(x)\n    b0, b1 = 0.0, 0.0\n    for _ in range(iterations):\n        y_pred = [b0 + b1 * xi for xi in x]\n        error = [y_pred[i] - y[i] for i in range(n)]\n        grad_b0 = (2 / n) * sum(error)\n        grad_b1 = (2 / n) * sum(error[i] * x[i] for i in range(n))\n        b0 -= learning_rate * grad_b0\n        b1 -= learning_rate * grad_b1\n    return b0, b1"},
                {"type": "list", "ordered": False, "items": [
                    "**Learning rate too high**: the algorithm overshoots the minimum and can diverge",
                    "**Learning rate too low**: convergence is extremely slow",
                    "**Closed-form (normal equations)**: exact, but computationally expensive for very large feature counts (matrix inversion is O(p^3))",
                    "**Gradient descent**: approximate, but scales to large datasets and generalizes to models with no closed-form solution"
                ]},
                {"type": "callout", "kind": "warning", "title": "Interview Trap", "value": "Don't say gradient descent is 'better' than least squares in general -- for simple/multiple linear regression with a small number of features, the closed-form solution is exact and typically faster. Gradient descent earns its keep at scale or when no closed form exists."}
            ]
        },
        {
            "title": "Multiple Linear Regression",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Extending to Multiple Predictors"},
                {"type": "text", "value": "Multiple linear regression extends the simple case to p predictors:\n\nY = b0 + b1*X1 + b2*X2 + ... + bp*Xp + e\n\nEach bj is interpreted as the average effect on Y of a one-unit increase in Xj, **holding all other predictors fixed**. This 'holding fixed' clause is the key difference from running p separate simple regressions."},
                {"type": "callout", "kind": "important", "title": "Why Not Just Run Separate Simple Regressions?", "value": "Running one simple regression per predictor ignores relationships between predictors and can produce misleading, even sign-flipped, coefficients. Classic example: shoe size alone might appear to 'predict' reading ability in children, but that's because both are driven by age -- a confounding variable multiple regression can control for by including age as a predictor."},
                {"type": "text", "value": "Once we fit a multiple regression model, we need to answer: **is at least one predictor useful for predicting Y?** This is tested with the **F-statistic**, which compares a model with all predictors against the null model (intercept only). A small p-value on the F-statistic indicates at least one predictor has a real effect -- crucially, this is different from looking at individual predictor p-values, especially when p (number of predictors) is large, since by chance some individual p-values will appear significant even with no real effect."},
                {"type": "list", "ordered": False, "items": [
                    "Individual predictor t-tests: is this specific bj significantly different from zero?",
                    "Overall F-test: is the model, taken as a whole, better than no model at all?",
                    "With many predictors, always check the F-statistic first before trusting individual p-values"
                ]}
            ]
        },
        {
            "title": "Assessing Model Fit: R-squared, RSE & F-Statistic",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "How Good Is the Fit?"},
                {"type": "text", "value": "Two related but distinct quantities measure how well a linear model fits the data:"},
                {"type": "list", "ordered": True, "items": [
                    "**Residual Standard Error (RSE)** -- an estimate of the standard deviation of the irreducible error e, measured in the units of Y. Roughly, the average amount the response deviates from the true regression line.",
                    "**R-squared** -- the proportion of variance in Y explained by the model, always between 0 and 1. Unlike RSE, R-squared is unitless, making it easier to interpret and compare across different response variables."
                ]},
                {"type": "code", "language": "python", "value": "def r_squared(y_true, y_pred):\n    y_mean = sum(y_true) / len(y_true)\n    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))\n    ss_tot = sum((yt - y_mean) ** 2 for yt in y_true)\n    return 1 - (ss_res / ss_tot)"},
                {"type": "callout", "kind": "warning", "title": "Interview Trap: R-squared Always Increases", "value": "Adding *any* additional predictor to a multiple regression model will never decrease R-squared, even if that predictor is pure noise -- R-squared can only go up or stay flat. This is why R-squared alone is a poor tool for comparing models with different numbers of predictors; adjusted R-squared, AIC, BIC, or cross-validated error should be used instead."},
                {"type": "divider"},
                {"type": "text", "value": "In simple linear regression with one predictor, R-squared is exactly equal to the squared correlation coefficient between X and Y -- a useful sanity check when validating an implementation."}
            ]
        },
        {
            "title": "Extensions: Qualitative Predictors & Interaction Terms",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Beyond the Additive, Linear Assumption"},
                {"type": "text", "value": "Standard linear regression assumes predictors are quantitative and that their effects are **additive** and **linear**. Both assumptions can be relaxed."},
                {"type": "heading", "level": 3, "value": "Qualitative (Categorical) Predictors"},
                {"type": "text", "value": "A categorical predictor with two levels (e.g. gender) can be encoded as a single **dummy variable** (0 or 1). A categorical predictor with more than two levels (e.g. region: North/South/East) requires multiple dummy variables -- generally, a variable with k levels needs k-1 dummy variables, with one level acting as the baseline that the coefficients are interpreted relative to."},
                {"type": "code", "language": "python", "value": "# One-hot encoding categorical predictors (k levels -> k-1 dummies)\nimport pandas as pd\ndf = pd.get_dummies(df, columns=['region'], drop_first=True)"},
                {"type": "heading", "level": 3, "value": "Interaction Terms"},
                {"type": "text", "value": "The additive assumption states that the effect of X1 on Y is independent of the value of X2. This is often unrealistic -- e.g. spending more on TV advertising might increase the effectiveness of radio advertising too. An **interaction term** (X1 * X2) relaxes this assumption:\n\nY = b0 + b1*X1 + b2*X2 + b3*(X1*X2) + e\n\nNow the effect of X1 on Y depends on the value of X2."},
                {"type": "callout", "kind": "important", "title": "The Hierarchy Principle", "value": "If an interaction term (X1*X2) is included in a model, both main effects X1 and X2 should generally be kept in the model too, even if their individual p-values look insignificant. Removing a main effect while keeping its interaction term changes the meaning of the interaction coefficient and is considered poor practice."},
                {"type": "list", "ordered": False, "items": [
                    "Interaction terms let one predictor's effect depend on another's value",
                    "The hierarchy principle: keep main effects when their interaction is in the model",
                    "Polynomial terms (X^2, X^3) similarly relax the strict linearity assumption within a single predictor"
                ]}
            ]
        }
    ]

    result = await db.topics.update_one(
        {"slug": "linear-regression"},
        {"$set": {"subtopics": new_subtopics}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

asyncio.run(main())
