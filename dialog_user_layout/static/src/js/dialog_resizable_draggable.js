/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { onMounted, onWillUnmount, onRendered } from '@odoo/owl';
import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

function dbg(scope, ...args) {
    console.log(`[odoo-dialog:${scope}]`, ...args);
}

function sleepFrame() {
    return new Promise((resolve) => requestAnimationFrame(resolve));
}

function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
}

patch(SelectCreateDialog.prototype, {
    setup() {
        if (typeof super.setup === 'function') {
            super.setup(...arguments);
        }

        this._drag = null;
        this._resize = null;
        this._handleObserver = null;
        this._onMove = null;
        this._onUp = null;
        this._onHeaderDown = null;
        this._onResizeDown = null;
        this._resizeHandle = null;
        this._isMounted = false;

        dbg('SelectCreateDialog', 'setup', this.props);
        onMounted(() => {
            this._isMounted = true;
            this._initDialog();
        });
        onRendered(() => this._ensureResizeHandle());
        onWillUnmount(() => this._cleanup());
    },

    async _waitForDialogRoot(retries = 30) {
        for (let i = 0; i < retries; i++) {
            const found = document.querySelector('.modal-content.o_select_create_dialog_content')
                || document.querySelector('.modal-content')
                || document.querySelector('.modal-dialog');
            if (found) return found;
            await sleepFrame();
        }
        return null;
    },

    async _fetchLayout(key) {
        return await rpc('/odoo_dialog_user_layout/get', { key });
    },

    async _saveLayout(key, values) {
        return await rpc('/odoo_dialog_user_layout/set', { key, values });
    },

    async _resetLayout(key) {
        return await rpc('/odoo_dialog_user_layout/reset', { key });
    },

    async _initDialog() {
        if (!this._isMounted) return;

        dbg('SelectCreateDialog', '_initDialog start', this.el);

        this.dialogEl = await this._waitForDialogRoot();
        this.contentEl = this.dialogEl;

        dbg('SelectCreateDialog', '_initDialog found', {
            dialogEl: !!this.dialogEl,
            contentEl: !!this.contentEl,
            dialogClass: this.dialogEl?.className,
        });

        if (!this.dialogEl) return;

        this.dialogEl.classList.add('odoo-dialog-resizable');
        this.dialogEl.style.position = 'relative';
        this.dialogEl.style.margin = '0';
        this.dialogEl.style.maxWidth = 'none';
        this.dialogEl.style.overflow = 'visible';

        const key = layoutKey(this.props);
        const layout = await this._fetchLayout(key);
        const v = layout && layout[key];

        if (v && !v.maximized) {
            const vpW = window.innerWidth;
            const vpH = window.innerHeight;
            if (v.width) this.dialogEl.style.width = `${v.width}px`;
            if (v.height) this.dialogEl.style.height = `${v.height}px`;
            if (v.left != null) this.dialogEl.style.left = `${clamp(v.left, 0, Math.max(0, vpW - 50))}px`;
            if (v.top != null) this.dialogEl.style.top = `${clamp(v.top, 0, Math.max(0, vpH - 50))}px`;
        }

        if (v?.maximized) this._maximize();

        this._ensureHeaderBindings();
        this._ensureResizeHandle();

        if (this._handleObserver) this._handleObserver.disconnect();
        this._handleObserver = new MutationObserver(() => this._ensureResizeHandle());
        this._handleObserver.observe(this.dialogEl, { childList: true, subtree: false });
    },

    _ensureHeaderBindings() {
        const header = document.querySelector('.modal-header');
        if (!header || this._onHeaderDown) return;

        header.style.cursor = 'move';
        this._onHeaderDown = (ev) => this._startDrag(ev);
        header.addEventListener('pointerdown', this._onHeaderDown);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-secondary btn-sm odoo-dialog-reset-btn';
        btn.textContent = '↺';
        btn.title = 'Reset layout';
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const key = layoutKey(this.props);
            await this._resetLayout(key);
            location.reload();
        });
        header.appendChild(btn);
    },

    _ensureResizeHandle() {
        if (!this.dialogEl) return;

        let host = this.dialogEl;
        let footer = this.dialogEl.querySelector('.modal-footer');

        if (!footer) {
            footer = document.createElement('div');
            footer.className = 'modal-footer odoo-dialog-resize-footer';
            this.dialogEl.appendChild(footer);
        }
        host = footer;

        const existing = host.querySelector('.odoo-dialog-resize-handle');
        if (existing) {
            this._resizeHandle = existing;
            return;
        }

        this._resizeHandle = document.createElement('div');
        this._resizeHandle.className = 'odoo-dialog-resize-handle';
        this._resizeHandle.textContent = '↘';
        host.appendChild(this._resizeHandle);

        this._onResizeDown = (ev) => this._startResize(ev);
        this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);
    },

    _maximize() {
        this.dialogEl.style.left = '0px';
        this.dialogEl.style.top = '0px';
        this.dialogEl.style.width = '100vw';
        this.dialogEl.style.height = '100vh';
    },

    _cleanup() {
        const header = document.querySelector('.modal-header');
        if (header && this._onHeaderDown) header.removeEventListener('pointerdown', this._onHeaderDown);
        if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
        if (this._handleObserver) this._handleObserver.disconnect();
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
    },

    _startDrag(ev) {
        if (ev.target.closest('button,a,input,textarea,select,.odoo-dialog-resize-handle')) return;
        const r = this.dialogEl.getBoundingClientRect();
        this._drag = { x: ev.clientX, y: ev.clientY, left: r.left, top: r.top };
        this._resize = null;
        ev.preventDefault();
        this._bindMove();
    },

    _startResize(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation?.();
        const r = this.dialogEl.getBoundingClientRect();
        this._resize = { x: ev.clientX, y: ev.clientY, width: r.width, height: r.height };
        this._drag = null;
        this._bindMove();
    },

    _bindMove() {
        if (this._onMove) return;
        this._onMove = (e) => this._move(e);
        this._onUp = () => this._stop();
        document.addEventListener('pointermove', this._onMove);
        document.addEventListener('pointerup', this._onUp, { once: true });
    },

    _move(ev) {
        if (!this.dialogEl) return;

        if (this._drag) {
            const x = this._drag.left + (ev.clientX - this._drag.x);
            const y = this._drag.top + (ev.clientY - this._drag.y);
            this.dialogEl.style.left = `${Math.max(0, x)}px`;
            this.dialogEl.style.top = `${Math.max(0, y)}px`;
        }

        if (this._resize) {
            this.dialogEl.style.width = `${Math.max(420, this._resize.width + (ev.clientX - this._resize.x))}px`;
            this.dialogEl.style.height = `${Math.max(180, this._resize.height + (ev.clientY - this._resize.y))}px`;
        }
    },

    async _stop() {
        if (this.dialogEl && (this._drag || this._resize)) {
            const r = this.dialogEl.getBoundingClientRect();
            const key = layoutKey(this.props);
            await this._saveLayout(key, {
                left: Math.round(Math.max(0, r.left)),
                top: Math.round(Math.max(0, r.top)),
                width: Math.round(r.width),
                height: Math.round(r.height),
                maximized: false,
            });
        }

        this._drag = null;
        this._resize = null;
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        this._onMove = null;
        this._onUp = null;
    },
});
