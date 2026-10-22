document.addEventListener("DOMContentLoaded", () => {
    const editor = document.getElementById("code-editor");
    const lineNumbers = document.getElementById("line-numbers");
    const languageSelect = document.getElementById("language-select");
    const editorTitle = document.getElementById("editor-title");
    const editorLangIcon = document.getElementById("editor-lang-icon");
    const presetSelect = document.getElementById("preset-select");
    const runBtn = document.getElementById("run-btn");
    const clearBtn = document.getElementById("clear-btn");
    const copyBtn = document.getElementById("copy-btn");
    const optToggle = document.getElementById("opt-toggle");
    const stdinInput = document.getElementById("stdin-input");
    const terminalTitle = document.getElementById("terminal-title");
    
    const errorBanner = document.getElementById("error-banner");
    const errorContent = document.getElementById("error-content");
    const errorClose = document.getElementById("error-close");
    
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    
    const tokensView = document.getElementById("tokens-view");
    const astTreeView = document.getElementById("ast-tree-view");
    const symtableBody = document.getElementById("symtable-body");
    const irView = document.getElementById("ir-view");
    const optIrView = document.getElementById("opt-ir-view");
    const optBehaviorText = document.getElementById("opt-behavior-text");
    const consoleOutput = document.getElementById("console-output");

    // Centralized Language Configuration Dictionary
    const LANGUAGES = {
        sudarshan: {
            id: "sudarshan",
            name: "Sudarshan",
            title: "Sudarshan Source Code (main.mini)",
            badge: "⚡",
            icon: "⚡",
            placeholder: "// Type your Sudarshan code here...\n\nint a = 15;\nint b = a + 25;\nprint(b);",
            defaultCode: `// Welcome to Sudarshan Compiler Studio\n// Interactive Multi-Phase Compiler Laboratory\n\nint x = 10;\nint y = 20;\nint sum = 0;\n\nwhile (x > 0) {\n    sum = sum + x;\n    x = x - 1;\n}\n\nif (sum > 50) {\n    print(sum);\n} else {\n    print(y);\n}\n`,
            runtimeTitle: "sudarshan-vm --run",
            presets: {
                "valid.mini": "valid.mini (While Loop & Branches)",
                "opt_test.mini": "opt_test.mini (Constant Folding)",
                "nested_scope.mini": "nested_scope.mini (Block Scoping)",
                "algebraic.mini": "algebraic.mini (Algebraic Identities)",
                "loop_factorial.mini": "loop_factorial.mini (Factorial)",
                "error_syntax.mini": "error_syntax.mini (Syntax Error Demo)",
                "error_semantic.mini": "error_semantic.mini (Semantic Error Demo)",
                "error_lexical.mini": "error_lexical.mini (Lexer Error Demo)",
                "error_runtime.mini": "error_runtime.mini (Runtime Error Demo)",
                "custom": "✏️ Custom Program"
            }
        },
        python: {
            id: "python",
            name: "Python 3",
            title: "Python Source Code (main.py)",
            badge: "🐍",
            icon: "🐍",
            placeholder: "# Type your Python 3 code here...\n\ndef greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('World'))",
            defaultCode: `# Python 3 - Interactive Execution\ndef fibonacci(n):\n    seq = [0, 1]\n    for _ in range(2, n):\n        seq.append(seq[-1] + seq[-2])\n    return seq\n\nprint("=== Python 3 Fibonacci Generator ===")\nprint("First 10 numbers:", fibonacci(10))\n`,
            runtimeTitle: "python3 main.py",
            presets: {
                "fibonacci.py": "fibonacci.py (Fibonacci Generator)",
                "primes.py": "primes.py (Sieve of Eratosthenes)",
                "quicksort.py": "quicksort.py (Recursive Quicksort)",
                "custom": "✏️ Custom Program"
            }
        },
        c: {
            id: "c",
            name: "C (GCC 13)",
            title: "C Source Code (main.c)",
            badge: "🇨",
            icon: "🇨",
            placeholder: "// Type your C code here...\n#include <stdio.h>\n\nint main(void) {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}",
            defaultCode: `#include <stdio.h>\n\nint main(void) {\n    printf("=== C (GCC 13) Execution ===\\n");\n    int sum = 0;\n    for (int i = 1; i <= 10; i++) {\n        sum += i;\n    }\n    printf("Sum of 1..10 = %d\\n", sum);\n    return 0;\n}\n`,
            runtimeTitle: "gcc -O2 main.c && ./a.out",
            presets: {
                "hello.c": "hello.c (Loop & Standard I/O)",
                "pointers.c": "pointers.c (Pointer Swap)",
                "bubble_sort.c": "bubble_sort.c (Bubble Sort Array)",
                "custom": "✏️ Custom Program"
            }
        },
        cpp: {
            id: "cpp",
            name: "C++ (GCC 13)",
            title: "C++ Source Code (main.cpp)",
            badge: "➕",
            icon: "➕",
            placeholder: "// Type your C++ code here...\n#include <iostream>\n\nint main() {\n    std::cout << \"Hello from C++!\" << std::endl;\n    return 0;\n}",
            defaultCode: `#include <iostream>\n#include <vector>\n#include <numeric>\n\nint main() {\n    std::cout << "=== C++20 Standard Library Demo ===\\n";\n    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};\n    int sum = std::accumulate(numbers.begin(), numbers.end(), 0);\n    std::cout << "Sum: " << sum << "\\n";\n    return 0;\n}\n`,
            runtimeTitle: "g++ -O2 -std=c++20 main.cpp && ./a.out",
            presets: {
                "vectors.cpp": "vectors.cpp (STL Vectors & Sum)",
                "templates.cpp": "templates.cpp (Generic Templates)",
                "custom": "✏️ Custom Program"
            }
        },
        java: {
            id: "java",
            name: "Java (OpenJDK 21)",
            title: "Java Source Code (Main.java)",
            badge: "☕",
            icon: "☕",
            placeholder: "// Type your Java code here...\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}",
            defaultCode: `public class Main {\n    public static long factorial(int n) {\n        long result = 1;\n        for (int i = 2; i <= n; i++) result *= i;\n        return result;\n    }\n\n    public static void main(String[] args) {\n        System.out.println("=== Java 21 Execution ===");\n        int num = 8;\n        System.out.println("Factorial of " + num + " = " + factorial(num));\n    }\n}\n`,
            runtimeTitle: "javac Main.java && java Main",
            presets: {
                "Factorial.java": "Factorial.java (Factorial Calculation)",
                "BinarySearch.java": "BinarySearch.java (Binary Search Algorithm)",
                "custom": "✏️ Custom Program"
            }
        },
        javascript: {
            id: "javascript",
            name: "JavaScript (Node 20)",
            title: "JavaScript Source Code (index.js)",
            badge: "🟨",
            icon: "🟨",
            placeholder: "// Type your JavaScript code here...\nconsole.log(\"Hello from Node.js!\");",
            defaultCode: `function findPrimes(limit) {\n    const primes = [];\n    for (let i = 2; i <= limit; i++) {\n        let isPrime = true;\n        for (let j = 2; j * j <= i; j++) {\n            if (i % j === 0) { isPrime = false; break; }\n        }\n        if (isPrime) primes.push(i);\n    }\n    return primes;\n}\n\nconsole.log("=== Node.js Execution ===");\nconsole.log("Primes up to 40:", findPrimes(40));\n`,
            runtimeTitle: "node index.js",
            presets: {
                "primes.js": "primes.js (Primes Sieve)",
                "async.js": "async.js (Async/Await Promises)",
                "custom": "✏️ Custom Program"
            }
        },
        typescript: {
            id: "typescript",
            name: "TypeScript (TS 5.6)",
            title: "TypeScript Source Code (index.ts)",
            badge: "🔷",
            icon: "🔷",
            placeholder: "// Type your TypeScript code here...\ninterface User {\n    name: string;\n}\nconst u: User = { name: 'Dev' };\nconsole.log(u.name);",
            defaultCode: `interface CompilerConfig {\n    name: string;\n    version: string;\n    strict: boolean;\n    targets: string[];\n}\n\nfunction printSummary(config: CompilerConfig): void {\n    console.log(\`[\${config.name} v\${config.version}]\`);\n    console.log(\`Strict mode: \${config.strict}\`);\n    console.log(\`Targets: \${config.targets.join(", ")}\`);\n}\n\nconst studioConfig: CompilerConfig = {\n    name: "Sudarshan Studio",\n    version: "2.0.0",\n    strict: true,\n    targets: ["Python", "C", "C++", "Java", "JavaScript", "TypeScript", "Sudarshan"]\n};\n\nprintSummary(studioConfig);\n`,
            runtimeTitle: "tsc index.ts && node index.js",
            presets: {
                "interfaces.ts": "interfaces.ts (Interfaces & Config)",
                "custom": "✏️ Custom Program"
            }
        }
    };

    let currentLanguage = "sudarshan";
    const userCodeCache = {};
    let presetsData = {};
    let allPresetsCatalog = {};
    let currentAstJson = null;
    let currentAstRaw = "";

    // Sync line numbers
    function updateLineNumbers() {
        const lines = editor.value.split("\n").length;
        lineNumbers.innerHTML = Array.from({ length: lines }, (_, i) => i + 1).join("<br>");
    }

    editor.addEventListener("input", () => {
        userCodeCache[currentLanguage] = editor.value;
        updateLineNumbers();
    });

    editor.addEventListener("scroll", () => {
        lineNumbers.scrollTop = editor.scrollTop;
    });

    // Support Tab key in editor (insert 4 spaces)
    editor.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            editor.value = editor.value.substring(0, start) + "    " + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
            userCodeCache[currentLanguage] = editor.value;
            updateLineNumbers();
        }
    });

    // Populate preset dropdown for the given language
    function populatePresetsDropdown(langId) {
        if (!presetSelect) return;
        const config = LANGUAGES[langId];
        if (!config || !config.presets) return;

        presetSelect.innerHTML = "";
        Object.entries(config.presets).forEach(([val, label]) => {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = label;
            presetSelect.appendChild(opt);
        });
    }

    // Switch programming language safely without losing typed code
    function switchLanguage(newLang) {
        if (!LANGUAGES[newLang]) return;

        // 1. Save current buffer to memory cache
        userCodeCache[currentLanguage] = editor.value;

        // 2. Set active language
        currentLanguage = newLang;
        const langConfig = LANGUAGES[newLang];

        // 3. Update Title, Icon, Placeholder, Terminal title
        if (editorTitle) editorTitle.textContent = langConfig.title;
        if (editorLangIcon) editorLangIcon.textContent = langConfig.icon;
        if (terminalTitle) terminalTitle.textContent = langConfig.runtimeTitle;
        editor.placeholder = langConfig.placeholder;

        // 4. Update preset dropdown options
        populatePresetsDropdown(newLang);

        // 5. Restore user's saved code for this language or load starter/preset
        if (userCodeCache[newLang] !== undefined && userCodeCache[newLang].trim() !== "") {
            editor.value = userCodeCache[newLang];
            presetSelect.value = "custom";
        } else {
            const firstPresetKey = Object.keys(langConfig.presets)[0];
            if (firstPresetKey && firstPresetKey !== "custom" && allPresetsCatalog[newLang] && allPresetsCatalog[newLang][firstPresetKey]) {
                editor.value = allPresetsCatalog[newLang][firstPresetKey];
                presetSelect.value = firstPresetKey;
            } else {
                editor.value = langConfig.defaultCode;
                presetSelect.value = firstPresetKey || "custom";
            }
            userCodeCache[newLang] = editor.value;
        }

        updateLineNumbers();
        compileCode(false);
    }

    if (languageSelect) {
        languageSelect.addEventListener("change", (e) => {
            switchLanguage(e.target.value);
        });
    }

    // Fetch presets from Python backend
    fetch("/api/presets")
        .then(res => res.json())
        .then(data => {
            if (data["__all_presets__"]) {
                allPresetsCatalog = data["__all_presets__"];
                presetsData = data["__all_presets__"]["sudarshan"] || data;
            } else {
                presetsData = data;
            }

            populatePresetsDropdown(currentLanguage);

            const defaultKey = presetsData["valid.mini"] ? "valid.mini" : Object.keys(presetsData)[0];
            if (defaultKey && presetsData[defaultKey]) {
                presetSelect.value = defaultKey;
                editor.value = presetsData[defaultKey];
                userCodeCache["sudarshan"] = editor.value;
                updateLineNumbers();
                compileCode();
            }
        })
        .catch(err => {
            console.warn("Could not load presets from /api/presets, fallback to default code:", err);
            populatePresetsDropdown(currentLanguage);
            updateLineNumbers();
            compileCode();
        });

    // Preset dropdown selection
    presetSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val === "custom") return;

        if (allPresetsCatalog[currentLanguage] && allPresetsCatalog[currentLanguage][val]) {
            editor.value = allPresetsCatalog[currentLanguage][val];
            userCodeCache[currentLanguage] = editor.value;
            updateLineNumbers();
            compileCode(false);
        } else if (presetsData[val]) {
            editor.value = presetsData[val];
            userCodeCache[currentLanguage] = editor.value;
            updateLineNumbers();
            compileCode(false);
        }
    });

    // Clear editor
    clearBtn.addEventListener("click", () => {
        editor.value = "";
        userCodeCache[currentLanguage] = "";
        presetSelect.value = "custom";
        updateLineNumbers();
    });

    // Copy editor content
    copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(editor.value);
        copyBtn.textContent = "Copied!";
        setTimeout(() => copyBtn.textContent = "Copy", 1500);
    });

    // Close error banner
    errorClose.addEventListener("click", () => {
        errorBanner.classList.add("hidden");
    });

    // Tab switching helper
    function activateTab(target) {
        tabBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === target));
        tabPanes.forEach(p => p.classList.toggle("active", p.id === target));
        
        // Update header stepper active state
        const reverseMap = {
            "tab-tokens": "step-tokens",
            "tab-ast": "step-ast",
            "tab-symtable": "step-symtable",
            "tab-semantics": "step-semantics",
            "tab-raw-ir": "step-raw-ir",
            "tab-opt-ir": "step-opt-ir",
            "tab-opt-behavior": "step-opt-behavior",
            "tab-console": "step-console"
        };
        const activeStepId = reverseMap[target];
        document.querySelectorAll(".pipeline-step").forEach(step => {
            step.classList.toggle("active", step.id === activeStepId);
        });

        if (target === "tab-ast") {
            setTimeout(() => {
                try { renderSVGTree(currentAstJson); } catch(e) { console.error(e); }
            }, 50);
        }
    }

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            activateTab(btn.dataset.tab);
        });
    });

    // Compiler pipeline steps click navigation
    const pipelineStepMap = {
        "step-tokens": "tab-tokens",
        "step-ast": "tab-ast",
        "step-symtable": "tab-symtable",
        "step-semantics": "tab-semantics",
        "step-raw-ir": "tab-raw-ir",
        "step-opt-ir": "tab-opt-ir",
        "step-opt-behavior": "tab-opt-behavior",
        "step-console": "tab-console"
    };

    Object.keys(pipelineStepMap).forEach(stepId => {
        const stepEl = document.getElementById(stepId);
        if (stepEl) {
            stepEl.addEventListener("click", () => {
                activateTab(pipelineStepMap[stepId]);
            });
        }
    });

    // Generic copy buttons (text and icon buttons)
    document.querySelectorAll(".copy-text-btn, .copy-icon-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.dataset.target;
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                const text = targetEl.value !== undefined ? targetEl.value : (targetEl.innerText || targetEl.textContent);
                navigator.clipboard.writeText(text);
                const orig = btn.innerHTML;
                const isIcon = btn.classList.contains("copy-icon-btn");
                btn.innerHTML = isIcon ? "✓" : "Copied!";
                setTimeout(() => { btn.innerHTML = orig; }, 1500);
            }
        });
    });

    // Compile code trigger
    runBtn.addEventListener("click", () => {
        compileCode(true);
    });

    if (optToggle) {
        optToggle.addEventListener("change", () => {
            compileCode(false);
        });
    }

    function compileCode(shouldSwitchToConsole = false) {
        const code = editor.value;
        const stdin = stdinInput ? stdinInput.value : "";
        const optimize = optToggle ? optToggle.checked : true;
        const lang = currentLanguage;

        runBtn.innerHTML = `<span class="btn-icon">⏳</span> Compiling...`;
        errorBanner.classList.add("hidden");

        fetch("/api/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, language: lang, stdin, optimize })
        })
        .then(res => res.json())
        .then(data => {
            runBtn.innerHTML = `<span class="btn-icon">▶</span> Compile &amp; Run`;
            
            if (data.runtime_title && terminalTitle) {
                terminalTitle.textContent = data.runtime_title;
            }

            if (data.errors && data.errors.length > 0) {
                showErrors(data.errors);
            }

            // 1. Render Tokens
            try {
                tokensView.textContent = data.tokens || "No tokens generated.";
            } catch (e) { console.error("Error rendering tokens:", e); }

            // 2. Render AST
            try {
                renderAST(data.ast_json, data.ast);
            } catch (e) { console.error("Error rendering AST:", e); }

            // 3. Render Symbol Table (5 columns + raw text + scope notes)
            try {
                renderSymbolTable(data.symbol_table_data, data.symbol_table, data.symbol_table_notes);
            } catch (e) { console.error("Error rendering Symbol Table:", e); }

            // 4. Render Semantic Analysis (banner + passed checks list + raw text)
            try {
                const isSuccess = data.success || (data.semantic_checks && data.semantic_checks.length > 0 && (!data.errors || data.errors.length === 0));
                renderSemantics(isSuccess, data.semantic_checks, data.semantic_analysis, data.errors);
            } catch (e) { console.error("Error rendering Semantics:", e); }

            // 5. Render Raw TAC
            try {
                irView.textContent = data.raw_tac || data.llvm_ir || "; Intermediate Representation (TAC) halted or failed.";
            } catch (e) { console.error("Error rendering Raw TAC:", e); }

            // 6. Render Expected Optimized IR & Behavior
            try {
                renderOptimizedBehavior(data.optimized_behavior, data.optimized_ir);
            } catch (e) { console.error("Error rendering Optimized Behavior:", e); }

            // 7. Render Execution Console Output
            try {
                if (data.success) {
                    consoleOutput.innerHTML = `<pre class="terminal-text" style="margin:0; font-family: inherit; font-size: inherit; line-height: 1.5; white-space: pre-wrap;">${escapeHtml(data.output)}</pre>`;
                } else {
                    const errorDetail = (data.errors && data.errors.length > 0)
                        ? data.errors.join("\n")
                        : (data.output || "Compilation failed.");
                    consoleOutput.innerHTML = `<div style="color: #ef4444; font-family: var(--font-mono); white-space: pre-wrap;">[Compilation / Runtime Failed]\n\n${escapeHtml(errorDetail)}</div>`;
                }
            } catch (e) { console.error("Error rendering Console:", e); }

            // If user clicked Compile & Run, or if running non-sudarshan language, or error, switch to console output tab
            if (shouldSwitchToConsole || lang !== "sudarshan" || !data.success) {
                activateTab("tab-console");
            }
        })
        .catch(err => {
            runBtn.innerHTML = `<span class="btn-icon">▶</span> Compile &amp; Run`;
            showErrors([err.message || "Failed to reach compilation server."]);
            consoleOutput.innerHTML = `<div style="color: #ef4444; font-family: var(--font-mono); white-space: pre-wrap;">[Network / Server Error]\n${escapeHtml(err.message)}</div>`;
            if (shouldSwitchToConsole || lang !== "sudarshan") {
                activateTab("tab-console");
            }
        });
    }

    function showErrors(errors) {
        errorContent.innerHTML = errors.map(err => `<div>• ${escapeHtml(err)}</div>`).join("");
        errorBanner.classList.remove("hidden");
    }

    // AST View Toggles
    const graphBtn = document.getElementById("ast-view-graph-btn");
    const cardsBtn = document.getElementById("ast-view-cards-btn");
    const textBtn = document.getElementById("ast-view-text-btn");
    
    const astGraphContainer = document.getElementById("ast-graph-container");
    const astTextView = document.getElementById("ast-text-view");
    const astSvg = document.getElementById("ast-svg");

    if (graphBtn && cardsBtn && textBtn) {
        graphBtn.addEventListener("click", () => setAstView("graph"));
        cardsBtn.addEventListener("click", () => setAstView("cards"));
        textBtn.addEventListener("click", () => setAstView("text"));
    }

    function setAstView(mode) {
        if (graphBtn) graphBtn.classList.toggle("active", mode === "graph");
        if (cardsBtn) cardsBtn.classList.toggle("active", mode === "cards");
        if (textBtn) textBtn.classList.toggle("active", mode === "text");

        if (astGraphContainer) astGraphContainer.classList.toggle("hidden", mode !== "graph");
        if (astTreeView) astTreeView.classList.toggle("hidden", mode !== "cards");
        if (astTextView) astTextView.classList.toggle("hidden", mode !== "text");

        try {
            if (mode === "graph") renderSVGTree(currentAstJson);
            else if (mode === "cards") renderASTCards(currentAstJson, currentAstRaw);
            else if (mode === "text") astTextView.textContent = currentAstRaw || "No AST generated.";
        } catch (e) {
            console.error("View mode error:", e);
        }
    }

    function renderAST(astJson, rawAstText) {
        currentAstJson = astJson;
        currentAstRaw = rawAstText;

        try { renderSVGTree(astJson); } catch (e) { console.error(e); }
        try { renderASTCards(astJson, rawAstText); } catch (e) { console.error(e); }
        try { if (astTextView) astTextView.textContent = rawAstText || "No AST generated."; } catch (e) { console.error(e); }
    }

    // Interactive SVG Tree Layout Renderer
    function renderSVGTree(astJson) {
        if (!astJson || !astSvg) return;
        astSvg.innerHTML = "";

        // Build simplified node tree
        function buildNode(data) {
            if (!data) return null;
            let label = data.label || data.name || data.type || "Node";
            let sublabel = data.line ? `Line ${data.line}` : "";
            let category = "expr";
            let children = [];

            const t = data.type || data.name || "";

            if (t === "Program" || t === "Block" || t.includes("Program")) {
                label = t.includes("Program") ? (data.label || "Root Program") : "Block";
                sublabel = `${data.children ? data.children.length : 0} Stmts`;
                category = "root";
                if (data.children) children = data.children.map(buildNode);
            } else if (t.includes("Declaration") || t === "VarDecl" || t === "DeclarationStmt") {
                const varName = data.details?.name || data.name || data.label?.replace("Decl: ", "") || "";
                label = `Decl: int ${varName}`;
                category = "stmt";
                if (data.children) children = data.children.map(buildNode);
                else if (data.value) children = [buildNode(data.value)];
            } else if (t.includes("Assignment") || t === "Assign" || t === "AssignmentStmt") {
                const varName = data.details?.name || data.name || data.label?.replace("Assign: ", "") || "";
                label = `Assign: ${varName}`;
                category = "stmt";
                if (data.children) children = data.children.map(buildNode);
                else if (data.value) children = [buildNode(data.value)];
            } else if (t.includes("Print") || t === "PrintStmt") {
                label = "print()";
                category = "stmt";
                if (data.children) children = data.children.map(buildNode);
                else if (data.value) children = [buildNode(data.value)];
            } else if (t.includes("While") || t === "WhileStmt") {
                label = "WhileLoop";
                category = "stmt";
                if (data.children) children = data.children.map(buildNode);
            } else if (t.includes("If") || t === "IfStmt") {
                label = "IfBranch";
                category = "stmt";
                if (data.children) children = data.children.map(buildNode);
            } else if (t.includes("Binary") || t === "BinaryOp" || t === "BinaryExpr") {
                const op = data.details?.operator || data.op || "+";
                label = `Op: ${op}`;
                category = "expr";
                if (data.children) children = data.children.map(buildNode);
                else {
                    if (data.left) children.push(buildNode(data.left));
                    if (data.right) children.push(buildNode(data.right));
                }
            } else if (t.includes("Unary") || t === "UnaryOp" || t === "UnaryExpr") {
                const op = data.details?.operator || data.op || "-";
                label = `Unary: ${op}`;
                category = "expr";
                if (data.children) children = data.children.map(buildNode);
                else if (data.expr) children = [buildNode(data.expr)];
            } else if (t.includes("Literal") || t === "Integer" || t === "IntegerExpr") {
                const val = data.details?.value !== undefined ? data.details.value : (data.value !== undefined ? data.value : data.label);
                label = `Val: ${val}`;
                category = "leaf";
            } else if (t.includes("Variable") || t === "VariableExpr" || t === "Identifier") {
                const name = data.details?.name || data.name || data.label;
                label = `Var: ${name}`;
                category = "leaf";
            } else {
                if (data.children) children = data.children.map(buildNode);
            }

            return { label, sublabel, category, children: children.filter(Boolean) };
        }

        const treeRoot = buildNode(astJson);
        if (!treeRoot) return;

        // Compute Layout: Node positions (x, y)
        const NODE_WIDTH = 130;
        const NODE_HEIGHT = 44;
        const LEVEL_GAP = 70;
        const SIBLING_GAP = 20;

        function calcSubtreeWidth(node) {
            if (!node.children || node.children.length === 0) {
                node.subtreeWidth = NODE_WIDTH + SIBLING_GAP;
                return node.subtreeWidth;
            }
            let w = 0;
            node.children.forEach(c => {
                w += calcSubtreeWidth(c);
            });
            node.subtreeWidth = Math.max(w, NODE_WIDTH + SIBLING_GAP);
            return node.subtreeWidth;
        }

        calcSubtreeWidth(treeRoot);

        let maxDepth = 0;
        function assignCoords(node, leftX, depth) {
            maxDepth = Math.max(maxDepth, depth);
            node.y = 40 + depth * (NODE_HEIGHT + LEVEL_GAP);

            if (!node.children || node.children.length === 0) {
                node.x = leftX + (node.subtreeWidth) / 2;
            } else {
                let curLeft = leftX;
                node.children.forEach(c => {
                    assignCoords(c, curLeft, depth + 1);
                    curLeft += c.subtreeWidth;
                });
                const firstChild = node.children[0];
                const lastChild = node.children[node.children.length - 1];
                node.x = (firstChild.x + lastChild.x) / 2;
            }
        }

        assignCoords(treeRoot, 20, 0);

        const totalWidth = Math.max(treeRoot.subtreeWidth + 60, astGraphContainer.clientWidth || 800);
        const totalHeight = 60 + (maxDepth + 1) * (NODE_HEIGHT + LEVEL_GAP);

        astSvg.setAttribute("width", totalWidth);
        astSvg.setAttribute("height", totalHeight);

        // Draw Lines (Edges) first
        function drawEdges(node) {
            if (!node.children) return;
            node.children.forEach(child => {
                const x1 = node.x;
                const y1 = node.y + NODE_HEIGHT / 2;
                const x2 = child.x;
                const y2 = child.y - NODE_HEIGHT / 2;
                const midY = (y1 + y2) / 2;

                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                path.setAttribute("d", `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`);
                path.setAttribute("class", "tree-edge");
                astSvg.appendChild(path);

                drawEdges(child);
            });
        }
        drawEdges(treeRoot);

        // Draw Nodes
        function drawNodes(node) {
            const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
            group.setAttribute("class", "tree-node-group");
            group.setAttribute("transform", `translate(${node.x - NODE_WIDTH / 2}, ${node.y - NODE_HEIGHT / 2})`);

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("width", NODE_WIDTH);
            rect.setAttribute("height", NODE_HEIGHT);
            rect.setAttribute("class", `tree-node-rect ${node.category}`);
            group.appendChild(rect);

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", NODE_WIDTH / 2);
            text.setAttribute("y", node.sublabel ? NODE_HEIGHT / 2 - 3 : NODE_HEIGHT / 2 + 4);
            text.setAttribute("class", "tree-node-text");
            text.textContent = node.label;
            group.appendChild(text);

            if (node.sublabel) {
                const subtext = document.createElementNS("http://www.w3.org/2000/svg", "text");
                subtext.setAttribute("x", NODE_WIDTH / 2);
                subtext.setAttribute("y", NODE_HEIGHT / 2 + 11);
                subtext.setAttribute("class", "tree-node-subtext");
                subtext.textContent = node.sublabel;
                group.appendChild(subtext);
            }

            astSvg.appendChild(group);

            if (node.children) {
                node.children.forEach(drawNodes);
            }
        }
        drawNodes(treeRoot);
    }

    function renderASTCards(astJson, rawAstText) {
        if (!astJson) {
            astTreeView.innerHTML = `<pre class="code-view">${escapeHtml(rawAstText || "No AST generated.")}</pre>`;
            return;
        }

        let html = `<div class="ast-tree">`;
        html += `<div class="ast-node-card">
            <div class="ast-node-title">📁 Root Program</div>
            <div class="ast-node-detail">${astJson.children ? astJson.children.length : 0} Statements</div>
        </div>`;

        if (astJson.children) {
            astJson.children.forEach(child => {
                html += renderASTChild(child, 1);
            });
        }
        html += `</div>`;
        astTreeView.innerHTML = html;
    }

    function renderASTChild(node, depth) {
        const indent = depth * 20;
        let title = node.label || node.name || node.type;
        let detail = node.line ? `Line ${node.line}` : "";

        let html = `<div style="margin-left: ${indent}px;" class="ast-node-card">
            <div class="ast-node-title">${escapeHtml(title)}</div>
            <div class="ast-node-detail">${escapeHtml(detail)}</div>
        </div>`;

        if (node.children) {
            node.children.forEach(child => {
                html += renderASTChild(child, depth + 1);
            });
        }
        return html;
    }

    function renderSymbolTable(symbols, rawText, notes) {
        const rawEl = document.getElementById("symtable-raw-text");
        const notesEl = document.getElementById("symtable-scope-note");

        if (rawEl) {
            rawEl.textContent = rawText || "No symbols recorded.";
        }

        if (notesEl) {
            if (notes) {
                let formatted = escapeHtml(notes);
                formatted = formatted.replace(/\b(while|if|for)\b/g, '<code>$1</code>');
                formatted = formatted.replace(/\bvariable\s+([a-zA-Z_][a-zA-Z0-9_]*)/g, 'variable <code>$1</code>');
                notesEl.innerHTML = formatted;
                notesEl.style.display = "block";
            } else {
                notesEl.style.display = "none";
            }
        }

        if (!symbols || symbols.length === 0) {
            symtableBody.innerHTML = `<tr><td colspan="5" class="empty-state">No symbols recorded.</td></tr>`;
            return;
        }

        const rows = symbols.map(s => {
            return `<tr>
                <td><strong>${escapeHtml(s.name)}</strong></td>
                <td><span class="badge-type">${escapeHtml(s.type)}</span></td>
                <td><span class="badge-kind">${escapeHtml(s.kind)}</span></td>
                <td><span class="badge-scope">${escapeHtml(s.scope)}</span></td>
                <td><span class="badge-value">${escapeHtml(s.value)}</span></td>
            </tr>`;
        });
        symtableBody.innerHTML = rows.join("");
    }

    function renderSemantics(success, checks, rawText, errors) {
        const banner = document.getElementById("semantics-status-banner");
        const statusText = document.getElementById("semantics-status-text");
        const checksList = document.getElementById("semantics-checks-list");
        const rawEl = document.getElementById("semantics-raw-text");

        if (success) {
            if (banner) {
                banner.className = "status-banner success";
                if (statusText) statusText.textContent = "Semantic analysis: SUCCESS";
            }
            if (checksList) {
                if (checks && checks.length > 0) {
                    checksList.innerHTML = checks.map(c => 
                        `<li><span class="check-icon">✓</span> <span>${escapeHtml(c)}</span></li>`
                    ).join("");
                } else {
                    checksList.innerHTML = `<li><span class="check-icon">✓</span> <span>All semantic verifications passed cleanly.</span></li>`;
                }
            }
            if (rawEl) {
                rawEl.textContent = rawText || "Semantic analysis: SUCCESS";
            }
        } else {
            if (banner) {
                banner.className = "status-banner error";
                if (statusText) statusText.textContent = "Semantic analysis: FAILED";
            }
            if (checksList) {
                const errItems = (errors && errors.length > 0) ? errors : ["Semantic analysis halted with errors."];
                checksList.innerHTML = errItems.map(e => 
                    `<li><span class="check-icon error">✗</span> <span>${escapeHtml(e)}</span></li>`
                ).join("");
            }
            if (rawEl) {
                rawEl.textContent = `Semantic analysis: FAILED\n\nErrors:\n` + (errors || []).map(e => `- ${e}`).join("\n");
            }
        }
    }

    function renderOptimizedBehavior(behaviorText, optimizedIr) {
        if (optBehaviorText) {
            optBehaviorText.textContent = behaviorText || "No optimized behavior generated.";
        }
        if (optIrView) {
            optIrView.textContent = optimizedIr || "; Optimized IR not available.";
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
});
