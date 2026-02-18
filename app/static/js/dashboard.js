document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const ocrSpinner = document.getElementById('ocrSpinner');
    const resetUploadBtn = document.getElementById('resetUploadBtn');
    const extractedSection = document.getElementById('extractedSection');
    const medicineList = document.getElementById('medicineList');
    const diseaseTags = document.getElementById('diseaseTags');
    const symptomInput = document.getElementById('symptomInput');
    const addSymptomBtn = document.getElementById('addSymptomBtn');
    const symptomList = document.getElementById('symptomList');
    const riskPercentage = document.getElementById('riskPercentage');
    const riskLabel = document.getElementById('riskLabel');
    const gaugeFill = document.getElementById('gaugeFill');
    const alertContainer = document.getElementById('alertContainer');
    const saveBtn = document.getElementById('saveAnalysisBtn');
    const historyList = document.getElementById('historyList');

    // State
    let currentMedicines = [];
    let currentSymptoms = []; //{name, severity:5, duration:1}
    let currentDiseases = [];

    // --- Init ---
    fetchHistory();

    // --- Upload Logic ---
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', handleUpload);

    async function handleUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        // UI Updates
        const reader = new FileReader();
        reader.onload = (e) => imagePreview.src = e.target.result;
        reader.readAsDataURL(file);

        dropZone.classList.add('hidden');
        previewArea.classList.remove('hidden');
        ocrSpinner.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.success) {
                currentMedicines = data.medicines;
                currentDiseases = data.inferred_diseases;
                renderMedicines();
                renderDiseases();

                // Unlock Interface
                extractedSection.classList.remove('opacity-50', 'pointer-events-none');
                document.getElementById('ocrSuccessBadge').classList.remove('hidden');

                triggerRealtimeAnalysis();
            } else {
                alert('OCR Failed: ' + data.error);
                resetUpload();
            }
        } catch (err) {
            console.error(err);
            alert('Upload error');
            resetUpload();
        } finally {
            ocrSpinner.classList.add('hidden');
        }
    }

    resetUploadBtn.addEventListener('click', resetUpload);

    function resetUpload() {
        fileInput.value = '';
        previewArea.classList.add('hidden');
        dropZone.classList.remove('hidden');
        extractedSection.classList.add('opacity-50', 'pointer-events-none');
        currentMedicines = [];
        currentDiseases = [];
        renderMedicines();
        renderDiseases();
        triggerRealtimeAnalysis();
    }

    // --- Rendering Data ---
    function renderMedicines() {
        if (currentMedicines.length === 0) {
            medicineList.innerHTML = '<p class="text-slate-400 italic text-sm text-center py-4">Upload an image to detect medicines.</p>';
            return;
        }
        medicineList.innerHTML = currentMedicines.map(med => `
            <div class="flex justify-between items-center bg-white p-3 rounded border border-slate-200 shadow-sm">
                <div>
                    <div class="font-bold text-slate-700">${med.name}</div>
                    <div class="text-xs text-slate-500">${med.dosage} • ${med.frequency}</div>
                </div>
                <i class="fa-solid fa-pills text-blue-300"></i>
            </div>
        `).join('');
    }

    function renderDiseases() {
        if (currentDiseases.length === 0) {
            diseaseTags.innerHTML = '<span class="text-slate-400 text-xs">None inferred</span>';
            return;
        }
        diseaseTags.innerHTML = currentDiseases.map(d => `
            <span class="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs font-bold border border-indigo-200">${d}</span>
        `).join('');
    }

    // --- Symptom Logic ---
    addSymptomBtn.addEventListener('click', addSymptom);
    symptomInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') addSymptom() });

    function addSymptom() {
        const name = symptomInput.value.trim();
        if (!name) return;

        currentSymptoms.push({ name, severity: 5, duration: 1 }); // Default values
        symptomInput.value = '';
        renderSymptoms();
        triggerRealtimeAnalysis();
    }

    function renderSymptoms() {
        if (currentSymptoms.length === 0) {
            symptomList.innerHTML = '<div class="text-center text-slate-400 text-sm py-2">No symptoms added.</div>';
            return;
        }
        symptomList.innerHTML = currentSymptoms.map((s, idx) => `
            <div class="bg-white p-2 rounded border border-slate-200 flex justify-between items-center animate-fadeIn">
                <span class="text-sm font-medium text-slate-700">${s.name}</span>
                <div class="flex items-center gap-2">
                     <input type="range" min="1" max="10" value="${s.severity}" class="w-16 accent-blue-500 h-1" 
                            onchange="updateSymptomSev(${idx}, this.value)" title="Severity">
                     <button onclick="removeSymptom(${idx})" class="text-red-400 hover:text-red-600 text-xs">
                        <i class="fa-solid fa-times"></i>
                     </button>
                </div>
            </div>
        `).join('');
    }

    window.removeSymptom = (idx) => {
        currentSymptoms.splice(idx, 1);
        renderSymptoms();
        triggerRealtimeAnalysis();
    };

    window.updateSymptomSev = (idx, val) => {
        currentSymptoms[idx].severity = parseInt(val);
        triggerRealtimeAnalysis();
    };

    // --- Realtime Analysis ---
    async function triggerRealtimeAnalysis() {
        // If no meds and no symptoms, reset
        if (currentMedicines.length === 0 && currentSymptoms.length === 0) {
            updateGauge(0, 'Waiting', []);
            return;
        }

        const payload = {
            medicines: currentMedicines,
            symptoms: currentSymptoms
        };

        try {
            const res = await fetch('/api/analyze_realtime', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                updateGauge(data.risk_percentage, data.classification, data.alerts);

                // Enable save if we have data
                saveBtn.onclick = () => {
                    sessionStorage.setItem('reportData', JSON.stringify({ report: data, inferred_diseases: currentDiseases }));
                    window.location.href = '/report';
                };
            }
        } catch (err) {
            console.error(err);
        }
    }

    function updateGauge(pct, label, alerts) {
        // Update Text
        riskPercentage.textContent = Math.round(pct) + '%';
        riskLabel.textContent = label;

        // Update Gauge Rotation
        // 0% -> 45deg (start)
        // 100% -> 225deg (end) -> 180deg range
        const rotation = 45 + (1.8 * pct);
        gaugeFill.style.transform = `rotate(${rotation}deg)`;

        // Color
        let colorClass = 'border-slate-200';
        let bgClass = 'bg-slate-100 text-slate-500';

        if (label === 'High') {
            gaugeFill.classList.replace('border-blue-500', 'border-red-500') || gaugeFill.classList.add('border-red-500');
            bgClass = 'bg-red-100 text-red-600';
        } else if (label === 'Moderate') {
            gaugeFill.classList.replace('border-blue-500', 'border-yellow-500') || gaugeFill.classList.add('border-yellow-500');
            bgClass = 'bg-yellow-100 text-yellow-600';
        } else if (label === 'Low') {
            gaugeFill.classList.replace('border-red-500', 'border-green-500') || gaugeFill.classList.add('border-green-500');
            bgClass = 'bg-green-100 text-green-600';
        }

        riskLabel.className = `inline-block px-3 py-1 rounded-full text-sm font-bold ${bgClass}`;

        // Alerts
        if (alerts && alerts.length > 0) {
            alertContainer.innerHTML = alerts.map(a => `
                <div class="text-xs bg-red-50 text-red-600 p-2 rounded border border-red-100 flex items-start">
                    <i class="fa-solid fa-triangle-exclamation mr-2 mt-0.5"></i> ${a}
                </div>
            `).join('');
        } else {
            alertContainer.innerHTML = '';
        }
    }

    // --- History ---
    async function fetchHistory() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();

            historyList.innerHTML = data.map(item => `
                <div class="p-3 bg-slate-50 rounded hover:bg-white hover:shadow transition-all border border-slate-100 cursor-pointer">
                    <div class="flex justify-between items-center mb-1">
                        <span class="font-bold text-slate-700 text-sm">Patient #${item.id}</span>
                        <span class="text-xs text-slate-400">${new Date(item.date).toLocaleDateString()}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-xs font-bold text-slate-500">Risk: ${Math.round(item.risk_score)}%</span>
                        <i class="fa-solid fa-chevron-right text-xs text-slate-300"></i>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            console.error('Failed to load history');
        }
    }
});
