const questions = [
    {
        id: 1,
        question: "A train running at the speed of 60 km/hr crosses a pole in 9 seconds. What is the length of the train?",
        options: {
            A: "120 meters",
            B: "150 meters",
            C: "324 meters",
            D: "180 meters"
        },
        correct: "B",
        explanation: "Speed of train = 60 * (5/18) m/sec = 50/3 m/sec.\nLength of train = Speed * Time = (50/3) * 9 = 150 meters."
    },
    {
        id: 2,
        question: "Find the odd one out from the following list of numbers: 3, 5, 11, 14, 17, 21, 23",
        options: {
            A: "14",
            B: "21",
            C: "17",
            D: "5"
        },
        correct: "A",
        explanation: "All numbers in the sequence are odd integers except 14, which is an even integer."
    },
    {
        id: 3,
        question: "What is the worst-case time complexity of searching for an element in a Balanced Binary Search Tree (such as an AVL Tree or Red-Black Tree)?",
        options: {
            A: "O(1)",
            B: "O(n)",
            C: "O(log n)",
            D: "O(n log n)"
        },
        correct: "C",
        explanation: "In a balanced Binary Search Tree, the height of the tree is restricted to O(log n). Therefore, searching, insertion, and deletion operations take O(log n) time in the worst case."
    },
    {
        id: 4,
        question: "A compiler converts code written in a high-level language into machine code. Which phase of the compiler is responsible for checking if the code conforms to grammatical rules?",
        options: {
            A: "Lexical Analyzer",
            B: "Syntax Analyzer (Parser)",
            C: "Semantic Analyzer",
            D: "Code Generator"
        },
        correct: "B",
        explanation: "The Syntax Analyzer (Parser) groups tokens from the lexical analyzer into grammatical structures (syntax trees) and verifies that the syntax rules of the language are followed."
    }
];

let userAnswers = {};
let score = 0;

document.addEventListener("DOMContentLoaded", () => {
    // Set user info in navbar
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        const expBadge = document.getElementById("user-exp-badge");
        expBadge.textContent = user.profile.experience_level;
        expBadge.className = `experience-tag exp-${user.profile.experience_level}`;
    }

    renderQuiz();
    
    document.getElementById("reset-quiz-btn").addEventListener("click", resetQuiz);
});

function renderQuiz() {
    const wrapper = document.getElementById("questions-wrapper");
    wrapper.innerHTML = "";
    
    questions.forEach((q, idx) => {
        const qCard = document.createElement("div");
        qCard.className = "aptitude-card glass-panel";
        qCard.id = `q-card-${q.id}`;
        
        let optionsHtml = "";
        for (const [letter, text] of Object.entries(q.options)) {
            optionsHtml += `
                <div class="aptitude-option-item" data-qid="${q.id}" data-opt="${letter}" id="opt-${q.id}-${letter}">
                    <span class="option-letter">${letter}</span>
                    <span>${text}</span>
                </div>
            `;
        }
        
        qCard.innerHTML = `
            <div class="aptitude-header">
                <span style="font-weight: 700; color: var(--accent-secondary);">Question #${idx + 1}</span>
                <span class="experience-tag exp-intermediate" style="font-size: 0.7rem;">General Aptitude</span>
            </div>
            <div class="aptitude-question">${q.question}</div>
            <div class="aptitude-options-list">
                ${optionsHtml}
            </div>
            <div class="aptitude-result" id="result-${q.id}"></div>
        `;
        
        wrapper.appendChild(qCard);
    });
    
    // Add click listeners to option items
    document.querySelectorAll(".aptitude-option-item").forEach(item => {
        item.addEventListener("click", () => {
            const qid = parseInt(item.getAttribute("data-qid"));
            const selectedOpt = item.getAttribute("data-opt");
            handleOptionSelect(qid, selectedOpt);
        });
    });
}

function handleOptionSelect(qid, selectedOpt) {
    // Return early if question already answered
    if (userAnswers[qid]) return;
    
    userAnswers[qid] = selectedOpt;
    
    const q = questions.find(item => item.id === qid);
    const resultBox = document.getElementById(`result-${qid}`);
    const selectedItem = document.getElementById(`opt-${qid}-${selectedOpt}`);
    
    selectedItem.classList.add("selected");
    
    // Disable all options for this question
    document.querySelectorAll(`.aptitude-option-item[data-qid="${qid}"]`).forEach(opt => {
        opt.style.cursor = "default";
        opt.style.opacity = "0.7";
    });
    
    // Verify answer
    const isCorrect = (selectedOpt === q.correct);
    resultBox.style.display = "block";
    
    if (isCorrect) {
        score++;
        resultBox.className = "aptitude-result aptitude-result-correct";
        resultBox.innerHTML = `🎉 <strong>Correct!</strong> ${q.explanation.replace(/\n/g, "<br>")}`;
    } else {
        resultBox.className = "aptitude-result aptitude-result-incorrect";
        resultBox.innerHTML = `❌ <strong>Incorrect.</strong> The correct answer is <strong>${q.correct}</strong>.<br><br>${q.explanation.replace(/\n/g, "<br>")}`;
        
        // Highlight correct option as glow-text or outline
        const correctItem = document.getElementById(`opt-${qid}-${q.correct}`);
        correctItem.style.borderColor = "var(--accent-green)";
        correctItem.style.background = "rgba(63, 185, 80, 0.05)";
    }
    
    // Update score counter
    document.getElementById("score-counter").textContent = `${score} / ${questions.length}`;
}

function resetQuiz() {
    userAnswers = {};
    score = 0;
    document.getElementById("score-counter").textContent = `0 / ${questions.length}`;
    renderQuiz();
}
