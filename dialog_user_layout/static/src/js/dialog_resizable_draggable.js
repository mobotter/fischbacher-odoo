/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';
import { onMounted, onWillUnmount, onRendered } from '@odoo/owl';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
}

async function saveUserLayout(key, values) {
    return await rpc('/odoo_dialog_user_layout/set', { key, values });
}

patch(SelectCreateDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogEl = null;
        this._drag = null;
        this._resize = null;
        this._handleObserver = null;
        this._onMove = null;
        this._onUp = null;
        this._onCancel = null;
        this._onHeaderDown = null;
        this._onResizeDown = null;
        this._resizeHandle = null;
        this._isMounted = false;
        onMounted(() => { this._isMounted = true; this._initDialog(); });
        onRendered(() => this._ensureResizeHandle());
        onWillUnmount(() => this._cleanup());
    },

    async _waitForDialogRoot(retries = 30) {
        for (let i = 0; i < retries; i++) {
            const found = document.querySelector('.modal-dialog.o_dialog') || document.querySelector('.modal-dialog');
            if (found) return found;
            await new Promise((r) => requestAnimationFrame(r));
        }
        return null;
    },

    async _fetchLayout(key) { return await rpc('/odoo_dialog_user_layout/get', { key }); },

    async _initDialog() {
        if (!this._isMounted) return;
        this.dialogEl = await this._waitForDialogRoot();
        if (!this.dialogEl) return;

        this.dialogEl.classList.add('odoo-dialog-resizable');
        this.dialogEl.style.position = 'fixed';
        this.dialogEl.style.margin = '0';
        this.dialogEl.style.maxWidth = 'none';
        this.dialogEl.style.width = '90vw';
        this.dialogEl.style.height = '70vh';
        this.dialogEl.style.transform = 'none';

        const key = layoutKey(this.props);
        const saved = await this._fetchLayout(key);
        const v = saved?.[key];
        if (v) {
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            const width = Math.min(v.width || Math.round(vw * 0.9), vw - 20);
            const height = Math.min(v.height || Math.round(vh * 0.7), vh - 20);
            this.dialogEl.style.width = `${width}px`;
            this.dialogEl.style.height = `${height}px`;
            this.dialogEl.style.left = `${clamp(v.left ?? 0, 0, Math.max(0, vw - width))}px`;
            this.dialogEl.style.top = `${clamp(v.top ?? 0, 0, Math.max(0, vh - height))}px`;
        }

        await new Promise((r) => requestAnimationFrame(r));
        this._ensureHeaderBindings();
        this._ensureResizeHandle();

        if (this._handleObserver) this._handleObserver.disconnect();
        this._handleObserver = new MutationObserver(() => this._ensureResizeHandle());
        this._handleObserver.observe(this.dialogEl, { childList: true, subtree: true });
    },

    _ensureHeaderBindings() {
        const header = this.dialogEl?.querySelector('.modal-header');
        if (!header || this._onHeaderDown) return;
        header.style.cursor = 'move';
        header.style.userSelect = 'none';
        header.style.touchAction = 'none';
        this._onHeaderDown = (ev) => {
            if (ev.button !== 0) return;
            if (ev.target.closest('button, a, input, textarea, select, label')) return;
            this._startDrag(ev);
        };
        header.addEventListener('pointerdown', this._onHeaderDown);
    },

    _ensureResizeHandle() {
        if (!this.dialogEl) return;
        let footer = this.dialogEl.querySelector('.modal-footer');
        if (!footer) {
            footer = document.createElement('div');
            footer.className = 'modal-footer odoo-dialog-resize-footer';
            this.dialogEl.appendChild(footer);
        }
        footer.style.position = 'relative';
        footer.style.minHeight = '28px';
        let handle = footer.querySelector('.odoo-dialog-resize-handle');
        if (!handle) {
            handle = document.createElement('div');
            handle.className = 'odoo-dialog-resize-handle';
            handle.textContent = '↘';
            footer.appendChild(handle);
        }
        this._resizeHandle = handle;
        if (!this._onResizeDown) {
            this._onResizeDown = (ev) => this._startResize(ev);
            handle.addEventListener('pointerdown', this._onResizeDown);
        }
    },

    _cleanup() {
        const header = this.dialogEl?.querySelector('.modal-header');
        if (header && this._onHeaderDown) header.removeEventListener('pointerdown', this._onHeaderDown);
        if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
        if (this._handleObserver) this._handleObserver.disconnect();
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        if (this._onCancel) document.removeEventListener('pointercancel', this._onCancel);
    },

    _startDrag(ev) {
        const r = this.dialogEl.getBoundingClientRect();
        this.dialogEl.style.left = `${r.left}px`;
        this.dialogEl.style.top = `${r.top}px`;
        this._drag = { pointerId: ev.pointerId, startX: ev.clientX, startY: ev.clientY, left: r.left, top: r.top, target: ev.currentTarget };
        this._resize = null;
        ev.preventDefault();
        ev.currentTarget.setPointerCapture?.(ev.pointerId);
        this._bindMove();
    },

    _startResize(ev) {
        const r = this.dialogEl.getBoundingClientRect();
        this._resize = { pointerId: ev.pointerId, startX: ev.clientX, startY: ev.clientY, width: r.width, height: r.height, target: ev.currentTarget };
        this._drag = null;
        ev.preventDefault();
        ev.stopPropagation();
        ev.currentTarget.setPointerCapture?.(ev.pointerId);
        this._bindMove();
    },

    _bindMove() {
        if (this._onMove) return;
        this._onMove = (e) => this._move(e);
        this._onUp = (e) => this._stop(e);
        this._onCancel = (e) => this._stop(e);
        document.addEventListener('pointermove', this._onMove, { passive: false });
        document.addEventListener('pointerup', this._onUp, { once: true });
        document.addEventListener('pointercancel', this._onCancel, { once: true });
    },

    _move(ev) {
        if (this._drag) {
            this.dialogEl.style.left = `${Math.max(0, this._drag.left + (ev.clientX - this._drag.startX))}px`;
            this.dialogEl.style.top = `${Math.max(0, this._drag.top + (ev.clientY - this._drag.startY))}px`;
            ev.preventDefault();
            return;
        }
        if (this._resize) {
            const dx = ev.clientX - this._resize.startX;
            const dy = ev.clientY - this._resize.startY;
            const w = Math.max(320, this._resize.width + dx);
            const h = Math.max(240, this._resize.height + dy);
            this.dialogEl.style.width = `${Math.min(w, window.innerWidth - 20)}px`;
            this.dialogEl.style.height = `${Math.min(h, window.innerHeight - 20)}px`;
            ev.preventDefault();
        }
    },

    async _stop(ev) {
        const active = this._drag || this._resize;
        const target = active?.target;
        const pointerId = active?.pointerId;
        if (target && pointerId != null) {
            try { target.releasePointerCapture?.(pointerId); } catch {}
        }
        if (this.dialogEl && active) {
            const r = this.dialogEl.getBoundingClientRect();
            const key = layoutKey(this.props);
            await saveUserLayout(key, { left: Math.round(r.left), top: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height), maximized: false });
            this.dialogEl.style.left = `${Math.round(r.left)}px`;
            this.dialogEl.style.top = `${Math.round(r.top)}px`;
            this.dialogEl.style.width = `${Math.round(r.width)}px`;
            this.dialogEl.style.height = `${Math.round(r.height)}px`;
        }
        this._drag = null;
        this._resize = null;
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        if (this._onCancel) document.removeEventListener('pointercancel', this._onCancel);
        this._onMove = null;
        this._onUp = null;
        this._onCancel = null;
    },
});
