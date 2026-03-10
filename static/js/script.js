let activeSkillId = null;
let activeSkillLabel = "Select Skill";

const langData = {
    'EN': { 
        'role': 'Agentic Systems Architect', 
        'gallery': 'Project Gallery', 
        'certs': 'Formal Certifications', 
        'hacks': 'Hackathons & Competitions' 
    },
    'JP': { 
        'role': 'エージェンティック・システム設計者', 
        'gallery': 'プロジェクトギャラリー', 
        'certs': '正式な資格', 
        'hacks': 'ハッカソンとコンペティション' 
    },
    'CN': { 
        'role': '代理系统架构师', 
        'gallery': '项目画廊', 
        'certs': '正式认证', 
        'hacks': '黑客马拉松与竞赛' 
    }
};

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

function resetRingItem(selectedId, ringType) {
    const slice = document.getElementById('slice-' + selectedId);
    if (slice && selectedId !== activeSkillId) {
        slice.setAttribute('fill', 'var(--element-green)');
        slice.style.transform = 'scale(1)';
    }
    const centerText = document.getElementById(ringType + '-center-label');
    if (centerText) {
        centerText.textContent = activeSkillLabel;
    }
}

function clickRingItem(selectedId, categoryLabel, ringType, highlightColor) {
    activeSkillId = selectedId;
    activeSkillLabel = categoryLabel;
    const allSlices = document.querySelectorAll(`.${ringType}-donut-slice`);
    allSlices.forEach(slice => {
        slice.setAttribute('fill', 'var(--element-green)');
        slice.style.transform = 'scale(1)';
    });
    const allContents = document.querySelectorAll(`.${ringType}-category`);
    allContents.forEach(content => {
        content.style.display = 'none';
    });
    const activeSlice = document.getElementById('slice-' + selectedId);
    if (activeSlice) {
        activeSlice.setAttribute('fill', highlightColor);
        activeSlice.style.transform = 'scale(1.05)';
    }
    const activeContent = document.getElementById('content-' + selectedId);
    if (activeContent) {
        activeContent.style.display = 'block';
    }
    const centerText = document.getElementById(ringType + '-center-label');
    if (centerText) {
        centerText.textContent = categoryLabel;
    }
}

function openModal(hiddenContentId) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('universal-modal');
    const modalContentArea = document.getElementById('modal-content-area');
    const sourceContent = document.getElementById(hiddenContentId);
    if (sourceContent) {
        modalContentArea.innerHTML = sourceContent.innerHTML;
        overlay.style.display = 'block';
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; 
    }
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('universal-modal').style.display = 'none';
    document.getElementById('modal-content-area').innerHTML = '';
    document.body.style.overflow = 'auto'; 
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('universal-modal');
        if (modal && modal.style.display === 'block') {
            closeModal();
        }
    }
});

const langOpts = document.querySelectorAll('.lang-opt');
langOpts.forEach(opt => {
    opt.addEventListener('click', function() {
        langOpts.forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        const selectedLang = this.innerText;
        const roleHeader = document.querySelector('#information-block h2');
        if (roleHeader) roleHeader.innerText = langData[selectedLang].role;
        const galleryHeader = document.querySelector('#project-dashboard h2');
        if (galleryHeader) galleryHeader.innerText = langData[selectedLang].gallery;
        const certsHeader = document.querySelector('#certifications-dashboard h2');
        if (certsHeader) certsHeader.innerText = langData[selectedLang].certs;
        const hacksHeader = document.querySelector('#hackathons-dashboard h2');
        if (hacksHeader) hacksHeader.innerText = langData[selectedLang].hacks;
    });
});