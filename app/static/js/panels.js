let allPanels = { uk: [], aus: [] };
let currentAPI = 'uk';

function fetchPanels(apiSource) {
    const url = `/api/panels?source=${apiSource}`;
    fetch(url)
        .then(r => r.json())
        .then(data => {
            allPanels[apiSource] = data;
            if (apiSource === currentAPI) {
                populateAll();
            }
        });
}

function switchAPI(apiSource) {
    currentAPI = apiSource;
    // Update tab styling
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${apiSource}-tab`).classList.add('active');
    // Update panel lists
    populateAll();
}

// list all the string fields you want to search
const fieldsToSearch = [
    'display_name',
    'description',
    'disease_group',
    'disease_sub_group',
];

function matches(panel, term) {
    const txt = term.toLowerCase();
    return fieldsToSearch.some(key => {
        const val = panel[key];
        if (!val) return false;
        // if it's an array, check each element:
        if (Array.isArray(val)) {
            return val.some(item => item.toLowerCase().includes(txt));
        }
        // otherwise treat it as a string
        return String(val).toLowerCase().includes(txt);
    });
}

function populateAll() {
    const term = document.getElementById("search_term_input")
        .value.trim().toLowerCase();

    const filtered = allPanels[currentAPI].filter(p => matches(p, term));

    for (let i = 1; i <= maxPanels; i++) {
        const select = document.getElementById(`panel_id_${i}`);
        const current = select.value || "None";
        
        // Keep current selection if it's from any source
        const currentPanel = ((current !== "None") &&
            (allPanels.uk.concat(allPanels.aus)).find(p => (String(p.id) + '-' + p.api_source) === current));
        
        updateSelectOptions(select, filtered, current, currentPanel);
    }
}

function updateSelectOptions(select, list, current, currentPanel) {
    // start with a "None" option
    const options = [{ id: "None", display_name: "None" }];
    const seen = new Set(["None"]);

    // add all filtered
    list.forEach(p => {
        options.push(p);
        seen.add(String(p.id) + '-' + p.api_source); // Combine ID + source
    });

    // if current selection was cleared but isn't in filtered, re-include it
    if (currentPanel && !seen.has(current)) {
        options.push(currentPanel);
        seen.add(current);
    }

    // sort ("None" stays first)
    options.sort((a, b) => {
        if (a.id === "None") return -1;
        if (b.id === "None") return 1;
        return a.display_name.localeCompare(b.display_name);
    });

    // rebuild DOM
    select.innerHTML = "";
    options.forEach(opt => {
        const o = document.createElement("option");
        if (opt.id === "None") {
            o.value = "None";
            o.textContent = "None";
        } else {
            o.value = `${opt.id}-${opt.api_source}`; // Combine ID + source
            o.textContent = opt.display_name;
        }
        o.dataset.source = opt.api_source;            
        if (String(o.value) === String(current)) {
            o.selected = true;
            // Add a visual indicator of the source and update the hidden source input
            select.classList.remove('panel-source-uk', 'panel-source-aus');
            if (opt.api_source) {
                select.classList.add(`panel-source-${opt.api_source}`);
                // Update the hidden source input
                const panelNumber = select.id.replace('panel_id_', '');
                document.getElementById(`api_source_${panelNumber}`).value = opt.api_source;
            }
        }
        select.append(o);
    });
}

function clearPanel(i) {
    const sel = document.getElementById(`panel_id_${i}`);
    const sel2 = document.getElementById(`list_type_${i}`);
    sel.value = "None";
    sel2.value = listTypeOptions[0];
    sel.classList.remove('panel-source-uk', 'panel-source-aus');
}

function clearAll() {
    // Clear search input
    document.getElementById('search_term_input').value = '';
    
    // Clear all panel selections
    for (let i = 1; i <= maxPanels; i++) {
        clearPanel(i);
    }
    
    // Refresh the panel list without any filters
    populateAll();
}

function debounce(fn, delay) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), delay);
    };
}

document.addEventListener("DOMContentLoaded", () => {
    // Fetch UK panels initially
    fetchPanels('uk');
    // Fetch Australian panels in the background
    fetchPanels('aus');

    document.getElementById("search_term_input")
        .addEventListener("input", debounce(populateAll, 300));
});