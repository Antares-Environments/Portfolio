/**
 * Handles the interactive Skillset Donut Ring
 * Resets all segments to green and highlights the selected category in orange.
 */
// Global variables to track the locked-in active state
let activeSkillId = null;
let activeSkillLabel = "Select Skill";

/**
 * HOVER: Temporarily highlights the slice and changes center text
 */
function hoverRingItem(selectedId, categoryLabel, ringType, highlightColor) {
    const slice = document.getElementById('slice-' + selectedId);
    if (slice) {
        slice.setAttribute('fill', highlightColor);
        slice.style.transform = 'scale(1.05)';
    }
    
    const centerText = document.getElementById(ringType + '-center-label');
    if (centerText) {
        centerText.textContent = categoryLabel;
    }
}

/**
 * LEAVE: Restores the slice to base green IF it isn't the actively clicked one
 */
function resetRingItem(selectedId, ringType) {
    const slice = document.getElementById('slice-' + selectedId);
    
    // Only revert the visual if this slice hasn't been permanently clicked
    if (slice && selectedId !== activeSkillId) {
        slice.setAttribute('fill', '#4CAF50'); // Base green
        slice.style.transform = 'scale(1)';
    }
    
    // Restore the center text to whatever is currently locked in
    const centerText = document.getElementById(ringType + '-center-label');
    if (centerText) {
        centerText.textContent = activeSkillLabel;
    }
}

/**
 * CLICK: Locks in the selection and reveals the skill details container
 */
function clickRingItem(selectedId, categoryLabel, ringType, highlightColor) {
    // 1. Update the tracking variables to the new selection
    activeSkillId = selectedId;
    activeSkillLabel = categoryLabel;

    // 2. Reset ALL slices to base green to clear previous clicks
    const allSlices = document.querySelectorAll(`.${ringType}-donut-slice`);
    allSlices.forEach(slice => {
        slice.setAttribute('fill', '#4CAF50');
        slice.style.transform = 'scale(1)';
    });

    // 3. Hide ALL skill detail lists
    const allContents = document.querySelectorAll(`.${ringType}-category`);
    allContents.forEach(content => {
        content.style.display = 'none';
    });

    // 4. Lock in the new active slice visuals
    const activeSlice = document.getElementById('slice-' + selectedId);
    if (activeSlice) {
        activeSlice.setAttribute('fill', highlightColor);
        activeSlice.style.transform = 'scale(1.05)';
    }

    // 5. Reveal the specific skill list for this category
    const activeContent = document.getElementById('content-' + selectedId);
    if (activeContent) {
        activeContent.style.display = 'block';
    }

    // 6. Ensure center text matches the locked choice
    const centerText = document.getElementById(ringType + '-center-label');
    if (centerText) {
        centerText.textContent = categoryLabel;
    }
}

/**
 * Universal Modal Logic
 * Pulls hidden HTML content (READMEs or Event details) into a focused overlay.
 */
function openModal(hiddenContentId) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('universal-modal');
    const modalContentArea = document.getElementById('modal-content-area');
    const sourceContent = document.getElementById(hiddenContentId);
    
    if (sourceContent) {
        // Inject the pre-rendered HTML (Markdown-to-HTML) into the modal
        modalContentArea.innerHTML = sourceContent.innerHTML;
        overlay.style.display = 'block';
        modal.style.display = 'block';
        
        // Prevent background scrolling while reading
        document.body.style.overflow = 'hidden'; 
    }
}

/**
 * Closes the modal and restores page scroll
 */
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('universal-modal').style.display = 'none';
    document.getElementById('modal-content-area').innerHTML = '';
    document.body.style.overflow = 'auto'; 
}