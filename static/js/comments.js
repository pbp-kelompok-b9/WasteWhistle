function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function updateBadgeCount(changeAmount) {
    const badgeElement = document.getElementById('comment-count-badge');
    if (!badgeElement) return;

    const currentCount = parseInt(badgeElement.textContent.trim(), 10) || 0;
    const newCount = Math.max(0, currentCount + changeAmount);
    badgeElement.textContent = `${newCount} Komentar`;
}

function closeAllDropdowns() {
    const dropdownMenus = document.querySelectorAll('.comment-dropdown-menu');
    dropdownMenus.forEach(function (menu) {
        menu.classList.add('hidden');
        const parentArticle = menu.closest('article');
        if (parentArticle) {
            parentArticle.style.zIndex = '';
        }
    });
}


// --- 2. Dropdown Menu Controller ---

function toggleCommentDropdown(event, menuId) {
    event.stopPropagation();
    const targetMenu = document.getElementById(menuId);
    if (!targetMenu) return;

    const isCurrentlyHidden = targetMenu.classList.contains('hidden');
    closeAllDropdowns();

    if (isCurrentlyHidden) {
        targetMenu.classList.remove('hidden');
        const parentArticle = targetMenu.closest('article');
        if (parentArticle) {
            parentArticle.style.zIndex = '40';
        }
    }
}
// Expose function globally for inline template onclick handlers
window.toggleCommentDropdown = toggleCommentDropdown;


// --- 3. HTML Component Builders ---

function buildCommentCardHtml(data) {
    const userInitial = data.username ? data.username[0].toUpperCase() : 'U';
    const isStaff = Boolean(data.is_staff || data.is_superuser);

    let staffBadgeHtml = '';
    if (isStaff) {
        staffBadgeHtml = `<span class="text-[9px] font-extrabold tracking-wider uppercase px-2 py-0.5 rounded-full bg-[#E7F0FE] text-[#1D4ED8]">Staff</span>`;
    }

    const deleteUrl = `/comment/delete/${data.id}/`;
    const csrfToken = getCsrfToken();

    return `
        <article class="relative flex gap-3 sm:gap-3.5 p-3.5 sm:p-4 min-h-[85px] rounded-[16px] bg-[#F8FBF9] border border-[#E2EDE6] transition-colors duration-150 hover:bg-[#F0F6F2]" id="comment-${data.id}">
            <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-full grid place-items-center text-white text-[11px] font-extrabold bg-gradient-to-br from-[#34C486] to-[#0E7A52] shrink-0">
                ${escapeHtml(userInitial)}
            </div>
            <div class="flex-1 min-w-0 flex flex-col gap-1">
                <div class="flex items-center justify-between gap-2 flex-wrap">
                    <div class="comment-meta-info flex items-center gap-1.5 flex-wrap text-xs">
                        <span class="font-bold text-[#101F19] text-[13px]">${escapeHtml(data.username)}</span>
                        ${staffBadgeHtml}
                        <span class="text-[11px] font-semibold text-[#8CA096]">· baru saja</span>
                    </div>
                    <div class="relative shrink-0 ml-auto dropdown-wrapper">
                        <button type="button" class="w-7 h-7 rounded-full flex items-center justify-center text-[#8CA096] hover:text-[#101F19] hover:bg-[#E2EDE6] transition-colors duration-150 cursor-pointer border-none bg-transparent outline-none focus-visible:ring-2 focus-visible:ring-[#11734F]" onclick="toggleCommentDropdown(event, 'comment-menu-${data.id}')" aria-label="Opsi komentar">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg>
                        </button>
                        <div id="comment-menu-${data.id}" class="hidden comment-dropdown-menu absolute right-0 top-8 z-50 min-w-[155px] p-1.5 bg-white border border-[#E2EDE6] rounded-[12px] shadow-[0_8px_24px_rgba(16,31,25,0.15)] origin-top-right">
                            <button type="button" class="edit-comment-btn flex items-center gap-2 w-full px-3 py-2 text-xs font-semibold rounded-[8px] transition-colors duration-150 text-left border-none bg-transparent cursor-pointer text-[#2A3B33] hover:bg-[#F0F6F2] hover:text-[#101F19]" data-id="${data.id}">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></svg>
                                Edit Komentar
                            </button>
                            <form class="delete-comment-form" method="post" action="${deleteUrl}">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                <button type="submit" class="flex items-center gap-2 w-full px-3 py-2 text-xs font-semibold rounded-[8px] transition-colors duration-150 text-left border-none bg-transparent cursor-pointer text-[#E5484D] hover:bg-[#FDECEC] hover:text-[#DC2626]">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
                                    Hapus Komentar
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                <p class="comment-text text-xs text-[#2A3B33] leading-relaxed break-words mt-0.5">${escapeHtml(data.content)}</p>
            </div>
        </article>`;
}

function buildEditFormHtml(commentId, currentText) {
    const csrfToken = getCsrfToken();
    return `
        <form class="edit-comment-form flex flex-col gap-2.5 mt-2" data-id="${commentId}" action="/comment/edit/${commentId}/">
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <textarea name="content" class="report-input text-xs p-3 rounded-[12px] min-h-[75px] focus:border-[#11734F]" required>${escapeHtml(currentText)}</textarea>
            <div class="flex items-center gap-2.5 justify-end mt-0.5">
                <button type="button" class="cancel-edit-btn px-4 py-2 text-xs font-bold rounded-full bg-[#E2EDE6] text-[#2A3B33] hover:bg-[#D4E3DA] transition-colors border-none cursor-pointer">Batal</button>
                <button type="submit" class="save-edit-btn px-5 py-2 text-xs font-extrabold rounded-full bg-[#11734F] text-white hover:bg-[#0E5E40] transition-colors border-none cursor-pointer shadow-sm">Simpan</button>
            </div>
        </form>`;
}

function buildEmptyStateHtml() {
    return `
        <div id="empty-comments-notice" class="border-[1.5px] border-dashed border-[#C4E8D3] rounded-[16px] p-8 text-center text-xs font-semibold text-[#8CA096] bg-[#F8FBF9]">
            Belum ada komentar. Jadi yang pertama berdiskusi!
        </div>`;
}


// --- 4. Core Actions & AJAX Handlers ---

async function handleAddCommentSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const textarea = document.getElementById('comment-content');
    const contentText = textarea ? textarea.value.trim() : '';

    if (!contentText) return;

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(form)
        });

        const data = await response.json();

        if (response.ok) {
            textarea.value = '';

            const emptyNotice = document.getElementById('empty-comments-notice');
            if (emptyNotice) {
                emptyNotice.remove();
            }

            const commentContainer = document.getElementById('comment-list-container');
            if (commentContainer) {
                commentContainer.insertAdjacentHTML('afterbegin', buildCommentCardHtml(data));
            }

            updateBadgeCount(1);
        } else {
            alert(data.message || 'Gagal menambahkan komentar.');
        }
    } catch (error) {
        console.error('Error adding comment:', error);
    }
}

function handleStartEditComment(editButton) {
    const commentId = editButton.dataset.id;
    const article = document.getElementById(`comment-${commentId}`);
    if (!article) return;

    closeAllDropdowns();

    if (article.querySelector('.edit-comment-form')) return;

    const commentTextElement = article.querySelector('.comment-text');
    if (!commentTextElement) return;

    const originalText = commentTextElement.textContent.trim();
    commentTextElement.classList.add('hidden');

    commentTextElement.insertAdjacentHTML('afterend', buildEditFormHtml(commentId, originalText));

    const textarea = article.querySelector('.edit-comment-form textarea');
    if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    }
}

function handleCancelEditComment(cancelButton) {
    const editForm = cancelButton.closest('.edit-comment-form');
    const article = cancelButton.closest('article');

    if (editForm && article) {
        editForm.remove();
        const commentTextElement = article.querySelector('.comment-text');
        if (commentTextElement) {
            commentTextElement.classList.remove('hidden');
        }
    }
}

async function handleSaveEditCommentSubmit(form) {
    const article = form.closest('article');
    const commentTextElement = article ? article.querySelector('.comment-text') : null;

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(form)
        });

        const data = await response.json();

        if (response.ok) {
            if (commentTextElement) {
                commentTextElement.textContent = data.content;
                commentTextElement.classList.remove('hidden');
            }

            const metaContainer = article.querySelector('.comment-meta-info');
            if (metaContainer && !metaContainer.querySelector('.edited-badge')) {
                metaContainer.insertAdjacentHTML(
                    'beforeend',
                    `<span class="edited-badge text-[10.5px] font-semibold italic text-[#8CA096]">(diedit)</span>`
                );
            }

            form.remove();
        } else {
            alert(data.message || 'Gagal memperbarui komentar.');
        }
    } catch (error) {
        console.error('Error updating comment:', error);
    }
}

async function handleDeleteCommentSubmit(form) {
    const article = form.closest('article');
    const commentContainer = document.getElementById('comment-list-container');

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(form)
        });

        if (response.ok) {
            if (article) {
                article.remove();
            }

            updateBadgeCount(-1);

            if (commentContainer && commentContainer.querySelectorAll('article').length === 0) {
                commentContainer.innerHTML = buildEmptyStateHtml();
            }
        }
    } catch (error) {
        console.error('Error deleting comment:', error);
    }
}


// --- 5. Initialization & Event Delegation ---

document.addEventListener('DOMContentLoaded', function () {
    // 1. New comment submission listener
    const addCommentForm = document.getElementById('add-comment-form');
    if (addCommentForm) {
        addCommentForm.addEventListener('submit', handleAddCommentSubmit);
    }

    // 2. Delegate events for comments list
    const commentContainer = document.getElementById('comment-list-container');
    if (commentContainer) {
        // Click actions (Edit & Cancel buttons)
        commentContainer.addEventListener('click', function (event) {
            const editButton = event.target.closest('.edit-comment-btn');
            if (editButton) {
                event.preventDefault();
                event.stopPropagation();
                handleStartEditComment(editButton);
                return;
            }

            const cancelButton = event.target.closest('.cancel-edit-btn');
            if (cancelButton) {
                event.preventDefault();
                handleCancelEditComment(cancelButton);
                return;
            }
        });

        // Form submit actions (Save edit & Delete forms)
        commentContainer.addEventListener('submit', function (event) {
            if (event.target.classList.contains('edit-comment-form')) {
                event.preventDefault();
                handleSaveEditCommentSubmit(event.target);
                return;
            }

            if (event.target.classList.contains('delete-comment-form')) {
                event.preventDefault();
                handleDeleteCommentSubmit(event.target);
                return;
            }
        });
    }

    // 3. Close open dropdown menus when clicking outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.dropdown-wrapper')) {
            closeAllDropdowns();
        }
    });
});
