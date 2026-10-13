/**
 * Advanced RAG Pipelines & Intelligent Q&A Bot - Frontend Engine
 * End-to-End Ingest, Embed, Retrieve, Re-Rank, Ground & Evaluate
 * Port: 8195
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Navigation Tabs
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            navTabs.forEach(t => t.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    const charts = {};

    function renderChart(canvasId, config) {
        if (charts[canvasId]) {
            charts[canvasId].destroy();
        }
        const ctx = document.getElementById(canvasId);
        if (ctx) {
            charts[canvasId] = new Chart(ctx, config);
        }
    }

    // Chart.js Theme Defaults
    Chart.defaults.color = "#626260";
    Chart.defaults.borderColor = "#e4dfd8";
    Chart.defaults.font.family = "'Inter', sans-serif";

    // ==============================================================
    // 2. Load Documents Catalog
    // ==============================================================
    async function loadDocuments() {
        try {
            const res = await fetch("/api/documents");
            const data = await res.json();
            const listContainer = document.getElementById("documentCatalogList");
            const badge = document.getElementById("docCountBadge");

            if (badge) badge.textContent = `${data.total_documents} Docs`;
            if (listContainer) {
                listContainer.innerHTML = "";
                data.documents.forEach(doc => {
                    const item = document.createElement("div");
                    item.className = "doc-item";
                    item.innerHTML = `
                        <div class="doc-title">${doc.title}</div>
                        <div class="doc-meta">
                            <span>${doc.category}</span>
                            <span>${doc.total_chunks} chunks</span>
                        </div>
                    `;
                    listContainer.appendChild(item);
                });
            }
        } catch (err) {
            console.error("Failed to load documents:", err);
        }
    }
    loadDocuments();

    // Document Upload
    const btnUpload = document.getElementById("btnUploadDoc");
    const fileInput = document.getElementById("fileUploadInput");
    if (btnUpload && fileInput) {
        btnUpload.addEventListener("click", async () => {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select a file to upload.");
                return;
            }
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append("file", file);

            btnUpload.disabled = true;
            btnUpload.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...`;

            try {
                const res = await fetch("/api/documents/upload", {
                    method: "POST",
                    body: formData
                });
                const result = await res.json();
                alert(result.message);
                loadDocuments();
                fileInput.value = "";
            } catch (err) {
                alert("Upload failed: " + err);
            } finally {
                btnUpload.disabled = false;
                btnUpload.innerHTML = `<i class="fa-solid fa-upload"></i> Upload & Ingest`;
            }
        });
    }

    // ==============================================================
    // 3. Interactive Q&A Chat Engine
    // ==============================================================
    const chatInput = document.getElementById("chatInput");
    const btnSendChat = document.getElementById("btnSendChat");
    const chatMessages = document.getElementById("chatMessages");
    const sourcesContainer = document.getElementById("sourcesContainer");
    const sourceCountBadge = document.getElementById("sourceCountBadge");
    const contrastiveBox = document.getElementById("contrastiveBox");
    const hallucinationText = document.getElementById("hallucinationText");

    async function handleChatSubmit() {
        const query = chatInput.value.trim();
        if (!query) return;

        // 1. Append User Message
        appendMessage("user", query);
        chatInput.value = "";

        // 2. Append Loading Placeholder
        const loadingId = "loading-" + Date.now();
        appendMessage("assistant", `<i class="fa-solid fa-spinner fa-spin"></i> Retrieving non-parametric evidence & synthesizing answer...`, loadingId);

        try {
            const useHyde = document.getElementById("toggleHyde") ? document.getElementById("toggleHyde").checked : true;
            const useReranker = document.getElementById("toggleReranker") ? document.getElementById("toggleReranker").checked : true;

            const res = await fetch("/api/qa/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    use_hyde: useHyde,
                    use_reranker: useReranker,
                    top_k: 3
                })
            });
            const data = await res.json();

            // Replace loading with final formatted response
            const loadEl = document.getElementById(loadingId);
            if (loadEl) {
                const formattedAnswer = highlightCitations(data.answer);
                loadEl.querySelector(".bubble-body").innerHTML = `
                    ${formattedAnswer}
                    <div class="mt-2 text-xs text-muted font-mono">
                        ⚡ Latency: ${data.latency.total_ms}ms (Retrieval: ${data.latency.retrieval_ms}ms | Re-Rank: ${data.latency.rerank_ms}ms) | Faithfulness: ${(data.evaluation.faithfulness * 100).toFixed(1)}%
                    </div>
                `;
            }

            // Populate Source Drawer
            populateSources(data.citations);

            // Populate Contrastive Hallucination
            if (contrastiveBox && hallucinationText) {
                contrastiveBox.style.display = "block";
                hallucinationText.textContent = `"${data.hallucinated_answer}"`;
            }

        } catch (err) {
            console.error("Chat error:", err);
            const loadEl = document.getElementById(loadingId);
            if (loadEl) {
                loadEl.querySelector(".bubble-body").innerHTML = `<span class="text-danger">Error: ${err}</span>`;
            }
        }
    }

    function appendMessage(sender, text, id = null) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${sender}`;
        if (id) bubble.id = id;

        const icon = sender === "user" ? "fa-user" : "fa-robot";
        const title = sender === "user" ? "You" : "Grounded RAG Assistant";

        bubble.innerHTML = `
            <div class="bubble-header"><i class="fa-solid ${icon}"></i> ${title}</div>
            <div class="bubble-body">${text}</div>
        `;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function highlightCitations(text) {
        return text.replace(/\[(Source \d+)\]/g, `<span class="citation-tag">[$1]</span>`);
    }

    function populateSources(citations) {
        if (!sourcesContainer) return;
        sourcesContainer.innerHTML = "";
        if (sourceCountBadge) sourceCountBadge.textContent = `${citations.length} Sources`;

        citations.forEach(c => {
            const card = document.createElement("div");
            card.className = "source-card";
            card.innerHTML = `
                <div class="source-tag">${c.tag}: ${c.doc_title}</div>
                <div class="source-bcrumb">${c.breadcrumbs}</div>
                <div class="source-text">${c.snippet}</div>
            `;
            sourcesContainer.appendChild(card);
        });
    }

    if (btnSendChat) btnSendChat.addEventListener("click", handleChatSubmit);
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleChatSubmit();
        });
    }

    // Quick Sample Buttons
    document.querySelectorAll(".sample-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            chatInput.value = btn.getAttribute("data-q");
            handleChatSubmit();
        });
    });

    // ==============================================================
    // 4. Pipeline Trace Inspector
    // ==============================================================
    const btnRunTrace = document.getElementById("btnRunTrace");
    const traceInput = document.getElementById("traceInput");

    async function executeTrace(query) {
        if (!query) return;
        if (btnRunTrace) {
            btnRunTrace.disabled = true;
            btnRunTrace.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Tracing Pipeline...`;
        }

        try {
            const res = await fetch("/api/pipeline/trace", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, use_hyde: true, use_reranker: true })
            });
            const data = await res.json();
            renderTraceSteps(data.pipeline_trace);
        } catch (err) {
            console.error("Trace error:", err);
            alert("Trace failed: " + err);
        } finally {
            if (btnRunTrace) {
                btnRunTrace.disabled = false;
                btnRunTrace.innerHTML = `<i class="fa-solid fa-play"></i> Inspect Pipeline Execution`;
            }
        }
    }

    function renderTraceSteps(steps) {
        // Step 1: Input
        const rawEl = document.getElementById("traceRawQuery");
        if (rawEl) rawEl.textContent = steps[0].data.raw_query;

        // Step 2: Transformations
        const s2El = document.getElementById("traceStep2");
        if (s2El) {
            const d = steps[1].data;
            s2El.innerHTML = `
                <div class="mb-2"><strong>Multi-Query Formulations:</strong></div>
                <ul class="feature-list mb-3">
                    ${d.multi_queries.map(q => `<li>${q}</li>`).join("")}
                </ul>
                <div class="mb-1"><strong>HyDE Synthesized Passage:</strong></div>
                <div class="math-box text-left font-sans text-xs">${d.hyde_synthesized_passage}</div>
            `;
        }

        // Step 3: Hybrid Retrieval
        const s3El = document.getElementById("traceStep3");
        if (s3El) {
            const d = steps[2].data;
            s3El.innerHTML = `
                <div class="mb-1 text-xs text-muted">Retrieved in <strong>${d.retrieval_latency_ms}ms</strong> via Dense HNSW + Sparse BM25 + Reciprocal Rank Fusion:</div>
                <div class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>RRF Rank</th>
                                <th>Chunk ID</th>
                                <th>Breadcrumb Context</th>
                                <th>Dense Sim</th>
                                <th>BM25</th>
                                <th>RRF Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${d.fused_rrf_candidates.map(c => `
                                <tr>
                                    <td class="font-bold text-accent">#${c.rank}</td>
                                    <td class="font-mono text-xs">${c.chunk_id}</td>
                                    <td class="text-xs text-muted">${c.breadcrumbs}</td>
                                    <td class="font-mono text-xs">${c.dense_score.toFixed(3)}</td>
                                    <td class="font-mono text-xs">${c.sparse_score.toFixed(2)}</td>
                                    <td class="font-mono text-xs text-success">${c.rrf_score.toFixed(5)}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Step 4: Re-Ranking
        const s4El = document.getElementById("traceStep4");
        if (s4El) {
            const d = steps[3].data;
            s4El.innerHTML = `
                <div class="mb-1 text-xs text-muted">Re-ranked in <strong>${d.rerank_latency_ms}ms</strong> using cross-encoder/ms-marco-MiniLM-L-6-v2:</div>
                <div class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Final Rank</th>
                                <th>Chunk ID</th>
                                <th>Cross-Score Logit</th>
                                <th>Initial RRF Rank</th>
                                <th>Rank Shift</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${d.reranked_chunks.map(c => `
                                <tr>
                                    <td class="font-bold text-accent">#${c.final_rank}</td>
                                    <td class="font-mono text-xs">${c.chunk_id}</td>
                                    <td class="font-mono text-xs font-bold ${c.cross_score > 0 ? 'text-success' : 'text-muted'}">${c.cross_score.toFixed(4)}</td>
                                    <td class="font-mono text-xs">#${c.initial_rank}</td>
                                    <td class="font-mono text-xs ${c.rank_shift > 0 ? 'text-success' : (c.rank_shift < 0 ? 'text-danger' : 'text-muted')}">
                                        ${c.rank_shift > 0 ? `+${c.rank_shift} ▲` : (c.rank_shift < 0 ? `${c.rank_shift} ▼` : '0 -')}
                                    </td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Step 5: Grounded Output
        const s5El = document.getElementById("traceStep5");
        if (s5El) {
            const d = steps[4].data;
            s5El.innerHTML = `
                <div class="chat-bubble assistant mb-3">
                    <div class="bubble-header"><i class="fa-solid fa-circle-check text-success"></i> Attributed Answer</div>
                    <div class="bubble-body">${highlightCitations(d.grounded_answer)}</div>
                </div>
                <div class="grid-4">
                    <div class="stat-pill"><span class="stat-label">Context Relevancy:</span> <strong>${(d.evaluation_triad.context_relevancy * 100).toFixed(1)}%</strong></div>
                    <div class="stat-pill"><span class="stat-label">Faithfulness:</span> <strong class="text-success">${(d.evaluation_triad.faithfulness * 100).toFixed(1)}%</strong></div>
                    <div class="stat-pill"><span class="stat-label">Answer Relevancy:</span> <strong>${(d.evaluation_triad.answer_relevancy * 100).toFixed(1)}%</strong></div>
                    <div class="stat-pill"><span class="stat-label">Overall RAG Triad:</span> <strong class="text-accent">${(d.evaluation_triad.overall_rag_score * 100).toFixed(1)}%</strong></div>
                </div>
            `;
        }
    }

    if (btnRunTrace) {
        btnRunTrace.addEventListener("click", () => {
            executeTrace(traceInput.value.trim());
        });
    }

    // ==============================================================
    // 5. Advanced Retrieval Arena
    // ==============================================================
    const btnRunArena = document.getElementById("btnRunArena");
    const arenaQueryInput = document.getElementById("arenaQueryInput");

    async function executeArena(query) {
        if (!query) return;
        if (btnRunArena) {
            btnRunArena.disabled = true;
            btnRunArena.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Arena...`;
        }

        try {
            const res = await fetch("/api/pipeline/trace", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, use_hyde: true, use_reranker: true })
            });
            const data = await res.json();
            const rrfCandidates = data.pipeline_trace[2].data.fused_rrf_candidates;
            const reranked = data.pipeline_trace[3].data.reranked_chunks;

            // Populate RRF Table
            const rrfTbody = document.querySelector("#arenaRRFTable tbody");
            if (rrfTbody) {
                rrfTbody.innerHTML = rrfCandidates.slice(0, 6).map(c => `
                    <tr>
                        <td class="font-bold text-accent">#${c.rank}</td>
                        <td class="font-mono text-xs">${c.chunk_id}</td>
                        <td class="font-mono text-xs">${c.dense_score.toFixed(3)}</td>
                        <td class="font-mono text-xs">${c.sparse_score.toFixed(2)}</td>
                        <td class="font-mono text-xs text-success">${c.rrf_score.toFixed(5)}</td>
                    </tr>
                `).join("");
            }

            // Populate Re-Ranked Table
            const rerankTbody = document.querySelector("#arenaRerankTable tbody");
            if (rerankTbody) {
                rerankTbody.innerHTML = reranked.map(c => `
                    <tr>
                        <td class="font-bold text-accent">#${c.final_rank}</td>
                        <td class="font-mono text-xs">${c.chunk_id}</td>
                        <td class="font-mono text-xs font-bold text-success">${c.cross_score.toFixed(4)}</td>
                        <td class="font-mono text-xs ${c.rank_shift > 0 ? 'text-success' : 'text-muted'}">
                            ${c.rank_shift > 0 ? `+${c.rank_shift} ▲` : '0 -'}
                        </td>
                    </tr>
                `).join("");
            }

            // Rank Shift Chart
            renderChart("chartRankShift", {
                type: "bar",
                data: {
                    labels: reranked.map(c => c.chunk_id),
                    datasets: [
                        {
                            label: "Initial RRF Rank",
                            data: reranked.map(c => c.initial_rank),
                            backgroundColor: "#d3cec6",
                            borderRadius: 4
                        },
                        {
                            label: "Final Re-Ranked Position",
                            data: reranked.map(c => c.final_rank),
                            backgroundColor: "#2c6ecb",
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            reverse: true, // Lower rank is better!
                            min: 1,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });

        } catch (err) {
            console.error("Arena error:", err);
        } finally {
            if (btnRunArena) {
                btnRunArena.disabled = false;
                btnRunArena.innerHTML = `<i class="fa-solid fa-bolt"></i> Run Retrieval Comparison`;
            }
        }
    }

    if (btnRunArena) {
        btnRunArena.addEventListener("click", () => {
            executeArena(arenaQueryInput.value.trim());
        });
    }

    // ==============================================================
    // 6. Query Transformation Studio
    // ==============================================================
    const btnRunTransform = document.getElementById("btnRunTransform");
    const transformInput = document.getElementById("transformInput");

    async function executeTransform(query) {
        if (!query) return;
        try {
            const res = await fetch("/api/transform/preview", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query })
            });
            const data = await res.json();

            const mqList = document.getElementById("multiQueryList");
            if (mqList) {
                mqList.innerHTML = data.multi_queries.map((q, i) => `<li><strong>Q${i+1}:</strong> ${q}</li>`).join("");
            }

            const hydeBox = document.getElementById("hydePassageBox");
            if (hydeBox) {
                hydeBox.textContent = `"${data.hyde_passage}"`;
            }

            const subList = document.getElementById("subQueryList");
            if (subList) {
                subList.innerHTML = data.sub_queries.map((q, i) => `<li><strong>Sub-task ${i+1}:</strong> ${q}</li>`).join("");
            }
        } catch (err) {
            console.error("Transform error:", err);
        }
    }

    if (btnRunTransform) {
        btnRunTransform.addEventListener("click", () => {
            executeTransform(transformInput.value.trim());
        });
    }

    // ==============================================================
    // 7. Automated Evaluation Benchmark
    // ==============================================================
    async function loadEvaluationBenchmark() {
        try {
            const res = await fetch("/api/evaluation/benchmark");
            const data = await res.json();

            // Radar Comparison Chart
            renderChart("chartRAGEval", {
                type: "radar",
                data: {
                    labels: ["Context Relevancy", "Faithfulness", "Answer Relevancy", "Top-3 Recall"],
                    datasets: [
                        {
                            label: "Naive RAG (Dense Only, No Rerank)",
                            data: [
                                data.naive_rag.context_relevancy * 100,
                                data.naive_rag.faithfulness * 100,
                                data.naive_rag.answer_relevancy * 100,
                                data.naive_rag.top_3_recall * 100
                            ],
                            borderColor: "#e0559a",
                            backgroundColor: "rgba(224, 85, 154, 0.15)",
                            borderWidth: 2
                        },
                        {
                            label: "Advanced RAG (HyDE + Hybrid + Re-Rank)",
                            data: [
                                data.advanced_rag.context_relevancy * 100,
                                data.advanced_rag.faithfulness * 100,
                                data.advanced_rag.answer_relevancy * 100,
                                data.advanced_rag.top_3_recall * 100
                            ],
                            borderColor: "#1d9e5f",
                            backgroundColor: "rgba(29, 158, 95, 0.15)",
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            min: 50,
                            max: 100,
                            ticks: { stepSize: 10 }
                        }
                    }
                }
            });

            // Recall & Latency Bar Chart
            renderChart("chartRecallLatency", {
                type: "bar",
                data: {
                    labels: ["Naive RAG", "Advanced RAG"],
                    datasets: [
                        {
                            label: "Top-3 Recall (%)",
                            data: [data.naive_rag.top_3_recall * 100, data.advanced_rag.top_3_recall * 100],
                            backgroundColor: "#2c6ecb",
                            borderRadius: 4
                        },
                        {
                            label: "End-to-End Latency (ms)",
                            data: [data.naive_rag.mean_latency_ms, data.advanced_rag.mean_latency_ms],
                            backgroundColor: "#a4c639",
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "top" } }
                }
            });

        } catch (err) {
            console.error("Evaluation load error:", err);
        }
    }

    // Trigger initial state loads
    executeTrace("What is the failover RPO and RTO for Aurora Global Database?");
    executeArena("What is the maximum chargeback window and CVV storage rule under PCI DSS?");
    executeTransform("What is the first-line medication and dose for acute STEMI triage?");
    loadEvaluationBenchmark();
});
